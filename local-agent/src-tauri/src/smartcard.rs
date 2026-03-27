use serde::Serialize;

#[derive(Debug, Clone, Serialize)]
pub struct SmartCardStatus {
    pub reader_available: bool,
    pub card_inserted: bool,
    pub card_holder: Option<String>,
}

/// Stub — will be replaced with actual PC/SC smart card reader integration.
pub fn check_card_status() -> SmartCardStatus {
    SmartCardStatus {
        reader_available: false,
        card_inserted: false,
        card_holder: None,
    }
}
