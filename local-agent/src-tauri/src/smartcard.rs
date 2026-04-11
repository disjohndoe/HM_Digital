use log::{debug, warn};
use once_cell::sync::Lazy;
use serde::Serialize;
use serde_json::json;
use std::sync::Mutex;

#[derive(Debug, Clone, Serialize)]
pub struct ReaderInfo {
    pub name: String,
    pub card_inserted: bool,
    pub card_holder: Option<String>,
    pub atr_hex: Option<String>,
}

/// Convert reader list to JSON values for WebSocket status messages and shared state.
pub fn readers_to_json(readers: &[ReaderInfo]) -> Vec<serde_json::Value> {
    readers.iter().map(|r| {
        json!({
            "name": r.name,
            "card_inserted": r.card_inserted,
            "card_holder": r.card_holder,
            "atr": r.atr_hex,
        })
    }).collect()
}

#[derive(Debug, Clone, Serialize)]
pub struct SmartCardStatus {
    pub reader_available: bool,
    pub card_inserted: bool,
    pub card_holder: Option<String>,
    pub readers: Vec<ReaderInfo>,
}

/// Cache for the last known card state to avoid PowerShell on every tick.
struct CachedCard {
    reader_name: String,
    atr_hex: Option<String>,
    card_holder: Option<String>,
}

static CARD_CACHE: Lazy<Mutex<Option<CachedCard>>> = Lazy::new(|| Mutex::new(None));

/// Check smart card readers, card presence, and read holder names.
///
/// Uses `get_status_change()` to detect card presence and read ATR from reader
/// state flags — **never connects to the card**, so it never triggers Windows
/// Certificate Propagation Service PIN prompts.
///
/// Holder name is read from the Windows cert store via CryptoAPI (public data
/// only, no private key access, no PIN).
pub fn check_card_status() -> SmartCardStatus {
    let ctx = match pcsc::Context::establish(pcsc::Scope::User) {
        Ok(ctx) => ctx,
        Err(e) => {
            debug!("PC/SC context failed: {}", e);
            return SmartCardStatus {
                reader_available: false,
                card_inserted: false,
                card_holder: None,
                readers: vec![],
            };
        }
    };

    // List readers
    let readers_list = match ctx.list_readers_len() {
        Ok(len) => {
            let mut buf = vec![0u8; len];
            match ctx.list_readers(&mut buf) {
                Ok(readers) => readers.map(|r| r.to_string_lossy().into_owned()).collect::<Vec<_>>(),
                Err(e) => {
                    debug!("Failed to list readers: {}", e);
                    return SmartCardStatus {
                        reader_available: false,
                        card_inserted: false,
                        card_holder: None,
                        readers: vec![],
                    };
                }
            }
        }
        Err(e) => {
            debug!("Failed to get readers buffer length: {}", e);
            return SmartCardStatus {
                reader_available: false,
                card_inserted: false,
                card_holder: None,
                readers: vec![],
            };
        }
    };

    if readers_list.is_empty() {
        return SmartCardStatus {
            reader_available: false,
            card_inserted: false,
            card_holder: None,
            readers: vec![],
        };
    }

    debug!("Found {} reader(s): {:?}", readers_list.len(), readers_list);

    // Query reader states WITHOUT connecting to cards.
    // get_status_change returns card presence + ATR from the reader driver,
    // with zero card interaction → zero PIN prompts.
    let mut reader_states: Vec<pcsc::ReaderState> = readers_list
        .iter()
        .filter_map(|name| {
            std::ffi::CString::new(name.as_str()).ok()
                .map(|cname| pcsc::ReaderState::new(cname, pcsc::State::UNAWARE))
        })
        .collect();

    if let Err(e) = ctx.get_status_change(std::time::Duration::from_millis(0), &mut reader_states) {
        warn!("get_status_change failed: {}", e);
        return SmartCardStatus {
            reader_available: true,
            card_inserted: false,
            card_holder: None,
            readers: readers_list.iter().map(|name| ReaderInfo {
                name: name.clone(), card_inserted: false, card_holder: None, atr_hex: None,
            }).collect(),
        };
    }

    let mut readers: Vec<ReaderInfo> = Vec::new();

    for rs in reader_states.iter() {
        let reader_name = rs.name().to_string_lossy().into_owned();
        let state = rs.event_state();
        let card_present = state.contains(pcsc::State::PRESENT);

        if card_present {
            // Read ATR directly from reader state (no card connection needed)
            let atr = rs.atr();
            let atr_hex = if !atr.is_empty() {
                let hex: String = atr.iter().map(|b| format!("{:02x}", b)).collect();
                debug!("Card ATR in '{}': {}", reader_name, hex);
                Some(hex)
            } else {
                None
            };

            // Check cache: only call CryptoAPI if card changed
            let holder = {
                let cache = CARD_CACHE.lock().unwrap_or_else(|e| e.into_inner());
                if let Some(ref cached) = *cache {
                    if cached.reader_name == reader_name && cached.atr_hex == atr_hex {
                        debug!("Card unchanged (same reader+ATR) — using cached holder");
                        cached.card_holder.clone()
                    } else {
                        drop(cache);
                        debug!("Card changed — reading holder from cert store");
                        read_card_holder_from_certstore()
                    }
                } else {
                    drop(cache);
                    debug!("No cached card — reading holder from cert store");
                    read_card_holder_from_certstore()
                }
            };

            if let Some(ref name) = holder {
                debug!("Card holder: {}", name);
            }

            // Update cache
            {
                let mut cache = CARD_CACHE.lock().unwrap_or_else(|e| e.into_inner());
                *cache = Some(CachedCard {
                    reader_name: reader_name.clone(),
                    atr_hex: atr_hex.clone(),
                    card_holder: holder.clone(),
                });
            }

            readers.push(ReaderInfo {
                name: reader_name.clone(),
                card_inserted: true,
                card_holder: holder,
                atr_hex,
            });
        } else {
            debug!("Reader '{}' — no card inserted", reader_name);
            readers.push(ReaderInfo {
                name: reader_name.clone(),
                card_inserted: false,
                card_holder: None,
                atr_hex: None,
            });
        }
    }

    // Derive top-level fields from readers array (backward compat)
    let any_card = readers.iter().any(|r| r.card_inserted);
    let first_holder = readers
        .iter()
        .find(|r| r.card_holder.is_some())
        .and_then(|r| r.card_holder.clone());

    // Clear cache when all cards removed
    if !any_card {
        let mut cache = CARD_CACHE.lock().unwrap_or_else(|e| e.into_inner());
        *cache = None;
    }

    SmartCardStatus {
        reader_available: !readers.is_empty(),
        card_inserted: any_card,
        card_holder: first_holder,
        readers,
    }
}

/// Read the cardholder name from the Windows certificate store using CryptoAPI.
///
/// Reads only public certificate data (subject DN) — does NOT access private keys,
/// so this never triggers Windows Security PIN prompts. ~1ms vs certutil's ~50ms.
///
/// Windows Certificate Propagation Service automatically copies smart card certs
/// to CurrentUser\My when a card is inserted, so we just read from there.
fn read_card_holder_from_certstore() -> Option<String> {
    use std::ptr;
    use windows_sys::Win32::Security::Cryptography::*;

    const ENCODING: u32 = X509_ASN_ENCODING | PKCS_7_ASN_ENCODING;

    unsafe {
        let store_name: Vec<u16> = "My\0".encode_utf16().collect();
        let store = CertOpenSystemStoreW(0, store_name.as_ptr());
        if store.is_null() {
            warn!("Failed to open certificate store");
            return None;
        }

        let mut result = None;
        let mut prev_ctx: *const CERT_CONTEXT = ptr::null();

        loop {
            let ctx = CertEnumCertificatesInStore(store, prev_ctx);
            if ctx.is_null() {
                break;
            }

            // Read the subject DN as an X.500 string
            let cert_info = &*(*ctx).pCertInfo;
            let name_blob = &cert_info.Subject;

            // First call: get buffer size
            let len = CertNameToStrW(ENCODING, name_blob, CERT_X500_NAME_STR, ptr::null_mut(), 0);

            if len > 1 {
                let mut buf = vec![0u16; len as usize];
                CertNameToStrW(ENCODING, name_blob, CERT_X500_NAME_STR, buf.as_mut_ptr(), len);

                let subject = String::from_utf16_lossy(&buf);
                let subject = subject.trim_end_matches('\0');
                debug!("Cert subject: {}", subject);

                if subject.contains("OU=Identification") {
                    for part in subject.split(',') {
                        let part = part.trim();
                        if let Some(cn) = part.strip_prefix("CN=") {
                            result = Some(cn.to_string());
                            break;
                        }
                    }
                    if result.is_some() {
                        CertFreeCertificateContext(ctx);
                        break;
                    }
                }
            }

            prev_ctx = ctx;
        }

        let _ = CertCloseStore(store, 0);
        result
    }
}
