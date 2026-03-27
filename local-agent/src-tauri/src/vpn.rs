use serde::Serialize;

#[derive(Debug, Clone, Serialize)]
pub struct VpnStatus {
    pub connected: bool,
    pub connection_name: Option<String>,
}

/// Stub — will be replaced with actual VPN connection check.
pub fn check_vpn_status() -> VpnStatus {
    VpnStatus {
        connected: false,
        connection_name: None,
    }
}
