use std::sync::Arc;
use std::time::Duration;

use futures_util::{SinkExt, StreamExt};
use log::{error, info, warn};
use serde::{Deserialize, Serialize};
use serde_json::json;
use tokio::sync::{mpsc, RwLock};
use tokio_tungstenite::tungstenite::Message;

use crate::smartcard::check_card_status;
use crate::vpn::check_vpn_status;

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ConnectionState {
    pub ws_connected: bool,
    pub card_inserted: bool,
    pub card_holder: Option<String>,
    pub vpn_connected: bool,
    pub vpn_name: Option<String>,
    pub reader_available: bool,
    pub last_error: Option<String>,
    pub agent_id: Option<String>,
}

impl Default for ConnectionState {
    fn default() -> Self {
        Self {
            ws_connected: false,
            card_inserted: false,
            card_holder: None,
            vpn_connected: false,
            vpn_name: None,
            reader_available: false,
            last_error: None,
            agent_id: None,
        }
    }
}

pub type SharedState = Arc<RwLock<ConnectionState>>;

/// Read smart card and VPN stubs, build status message.
fn build_status_message() -> serde_json::Value {
    let card = check_card_status();
    let vpn = check_vpn_status();
    json!({
        "type": "status",
        "card_inserted": card.card_inserted,
        "card_holder": card.card_holder,
        "reader_available": card.reader_available,
        "vpn_connected": vpn.connected,
        "vpn_name": vpn.connection_name,
    })
}

/// Cookie file path for persistent sessions across CEZIH calls.
const COOKIE_FILE: &str = "cezih_session_cookies.txt";

/// Handle an HTTP proxy request via curl.exe subprocess.
/// Uses --ssl-auto-client-cert for SChannel smart card mTLS.
/// Cookie jar persists the Keycloak session across requests.
async fn handle_http_proxy(msg: serde_json::Value) -> String {
    let request_id = msg.get("request_id").and_then(|v| v.as_str()).unwrap_or("");
    let method = msg.get("method").and_then(|v| v.as_str()).unwrap_or("GET");
    let url = msg.get("url").and_then(|v| v.as_str()).unwrap_or("");
    let headers = msg.get("headers").and_then(|v| v.as_object());
    let body = msg.get("body");

    let cookie_path = std::env::temp_dir().join(COOKIE_FILE);
    let cookie_str = cookie_path.to_string_lossy().to_string();

    let mut cmd = tokio::process::Command::new("curl.exe");
    cmd.arg("-s")                      // Silent
       .arg("-L")                      // Follow redirects
       .arg("--ssl-auto-client-cert")  // SChannel auto-select smart card cert
       .arg("-b").arg(&cookie_str)     // Read cookies
       .arg("-c").arg(&cookie_str)     // Write cookies
       .arg("--max-time").arg("30")
       .arg("-w").arg("\n%{http_code}") // Append status code
       .arg("-X").arg(method);

    // Set headers — skip Authorization (let smart card cert auth handle it)
    if let Some(hdrs) = headers {
        for (key, val) in hdrs {
            if key.eq_ignore_ascii_case("authorization") {
                continue;
            }
            if let Some(v) = val.as_str() {
                cmd.arg("-H").arg(format!("{}: {}", key, v));
            }
        }
    }

    // Set body if present
    if let Some(b) = body {
        if !b.is_null() {
            let body_str = if b.is_string() { b.as_str().unwrap_or("").to_string() } else { b.to_string() };
            cmd.arg("-d").arg(body_str);
        }
    }

    cmd.arg(url);

    // Execute curl
    match cmd.output().await {
        Ok(output) => {
            let raw = String::from_utf8_lossy(&output.stdout).to_string();
            let stderr = String::from_utf8_lossy(&output.stderr).to_string();

            if !output.status.success() && raw.is_empty() {
                error!("curl failed for {} — exit={}, stderr={}", &request_id[..request_id.len().min(8)], output.status, stderr);
                return json!({
                    "type": "http_proxy_response",
                    "request_id": request_id,
                    "error": format!("curl failed: {}", stderr.trim())
                }).to_string();
            }

            // Parse status code from last line (appended by -w)
            let (resp_body, status_code) = match raw.rfind('\n') {
                Some(pos) => {
                    let code_str = raw[pos+1..].trim();
                    let code = code_str.parse::<u16>().unwrap_or(0);
                    (raw[..pos].to_string(), code)
                }
                None => (raw, 0),
            };

            info!("HTTP proxy response {} — {} ({} bytes)", &request_id[..request_id.len().min(8)], status_code, resp_body.len());
            json!({
                "type": "http_proxy_response",
                "request_id": request_id,
                "status_code": status_code,
                "headers": {},
                "body": resp_body
            }).to_string()
        }
        Err(e) => {
            error!("Failed to spawn curl for {} — {}", &request_id[..request_id.len().min(8)], e);
            json!({
                "type": "http_proxy_response",
                "request_id": request_id,
                "error": format!("Failed to run curl: {}", e)
            }).to_string()
        }
    }
}

/// Spawn a WebSocket connection task that reconnects with exponential backoff.
pub fn spawn_connection_task(
    backend_url: String,
    tenant_id: String,
    agent_secret: String,
    initial_agent_id: Option<String>,
    state: SharedState,
) {
    tauri::async_runtime::spawn(async move {
        let mut backoff = Duration::from_secs(1);
        let max_backoff = Duration::from_secs(60);

        // Agent ID persists across reconnections within this process
        let mut agent_id: Option<String> = initial_agent_id;

        loop {
            // Connect WITHOUT credentials in URL — auth is sent as first message
            let ws_url = format!("{}ws/agent", backend_url);
            info!("Connecting to {}", ws_url);

            match tokio_tungstenite::connect_async(&ws_url).await {
                Ok((ws_stream, _)) => {
                    info!("WebSocket TCP connected (awaiting auth confirmation)");

                    let (mut write, mut read) = ws_stream.split();

                    // Send auth message IMMEDIATELY as first message (credentials NOT in URL)
                    let auth_msg = json!({
                        "type": "auth",
                        "tenant_id": tenant_id,
                        "agent_secret": agent_secret,
                        "agent_id": agent_id,
                    });
                    if write.send(Message::Text(auth_msg.to_string().into())).await.is_err() {
                        error!("Failed to send auth message");
                        break;
                    }

                    // Channel for spawned tasks to send WS messages (e.g., HTTP proxy responses)
                    let (outbound_tx, mut outbound_rx) = mpsc::channel::<String>(32);

                    // Don't set ws_connected yet — wait for server "connected" confirmation
                    {
                        let mut s = state.write().await;
                        s.last_error = None;
                    }
                    let mut status_interval = tokio::time::interval(Duration::from_secs(30));

                    loop {
                        tokio::select! {
                            msg = read.next() => {
                                match msg {
                                    Some(Ok(Message::Text(text))) => {
                                        if let Ok(parsed) = serde_json::from_str::<serde_json::Value>(&text) {
                                            let msg_type = parsed.get("type").and_then(|t| t.as_str()).unwrap_or("");
                                            match msg_type {
                                                "connected" => {
                                                    info!("Server confirmed connection: {}", parsed.get("message").and_then(|m| m.as_str()).unwrap_or(""));
                                                    // Auth confirmed — NOW mark as connected and reset backoff
                                                    backoff = Duration::from_secs(1);
                                                    {
                                                        let mut s = state.write().await;
                                                        s.ws_connected = true;
                                                    }
                                                    // Persist agent_id from server
                                                    if let Some(id) = parsed.get("agent_id").and_then(|v| v.as_str()) {
                                                        agent_id = Some(id.to_string());
                                                        let mut s = state.write().await;
                                                        s.agent_id = Some(id.to_string());
                                                        info!("Agent ID: {}", id);
                                                    }
                                                    // Send initial status
                                                    let status = build_status_message();
                                                    let _ = write.send(Message::Text(status.to_string().into())).await;
                                                    // Update state
                                                    let card = check_card_status();
                                                    let vpn = check_vpn_status();
                                                    let mut s = state.write().await;
                                                    s.reader_available = card.reader_available;
                                                    s.card_inserted = card.card_inserted;
                                                    s.card_holder = card.card_holder;
                                                    s.vpn_connected = vpn.connected;
                                                    s.vpn_name = vpn.connection_name;
                                                }
                                                "ping" => {
                                                    let _ = write.send(Message::Text(r#"{"type":"pong"}"#.into())).await;
                                                }
                                                "sign_request" => {
                                                    // Future: handle real signing via smart card
                                                    info!("Received sign_request (mock)");
                                                    let response = json!({
                                                        "type": "sign_response",
                                                        "request_id": parsed.get("request_id"),
                                                        "signature": "MOCK_SIGNATURE_PLACEHOLDER",
                                                        "mock": true
                                                    });
                                                    let _ = write.send(Message::Text(response.to_string().into())).await;
                                                }
                                                "http_proxy_request" => {
                                                    let rid = parsed.get("request_id").and_then(|v| v.as_str()).unwrap_or("").to_string();
                                                    info!("HTTP proxy request {} — {} {}",
                                                        &rid[..rid.len().min(8)],
                                                        parsed.get("method").and_then(|v| v.as_str()).unwrap_or("?"),
                                                        parsed.get("url").and_then(|v| v.as_str()).unwrap_or("?"));
                                                    let tx = outbound_tx.clone();
                                                    let p = parsed.clone();
                                                    tokio::spawn(async move {
                                                        let resp = handle_http_proxy(p).await;
                                                        let _ = tx.send(resp).await;
                                                    });
                                                }
                                                other => {
                                                    warn!("Unknown message type: {}", other);
                                                }
                                            }
                                        }
                                    }
                                    Some(Ok(Message::Ping(data))) => {
                                        let _ = write.send(Message::Pong(data)).await;
                                    }
                                    Some(Ok(Message::Close(_))) | None => {
                                        info!("WebSocket closed by server");
                                        break;
                                    }
                                    Some(Err(e)) => {
                                        error!("WebSocket error: {}", e);
                                        break;
                                    }
                                    _ => {}
                                }
                            }
                            // Forward outbound messages from spawned tasks (HTTP proxy responses)
                            Some(outbound_msg) = outbound_rx.recv() => {
                                if write.send(Message::Text(outbound_msg.into())).await.is_err() {
                                    break;
                                }
                            }
                            _ = status_interval.tick() => {
                                let status = build_status_message();
                                if write.send(Message::Text(status.to_string().into())).await.is_err() {
                                    break;
                                }
                                // Update state
                                let card = check_card_status();
                                let vpn = check_vpn_status();
                                let mut s = state.write().await;
                                s.reader_available = card.reader_available;
                                s.card_inserted = card.card_inserted;
                                s.card_holder = card.card_holder;
                                s.vpn_connected = vpn.connected;
                                s.vpn_name = vpn.connection_name;
                            }
                        }
                    }

                    // Disconnected
                    {
                        let mut s = state.write().await;
                        s.ws_connected = false;
                    }
                }
                Err(e) => {
                    let mut s = state.write().await;
                    s.ws_connected = false;
                    s.last_error = Some(format!("{}", e));
                    warn!("Connection failed: {}", e);
                }
            }

            // Wait before reconnecting (agent_id preserved for next attempt)
            info!("Reconnecting in {:?}...", backoff);
            tokio::time::sleep(backoff).await;
            backoff = (backoff * 2).min(max_backoff);
        }
    });
}
