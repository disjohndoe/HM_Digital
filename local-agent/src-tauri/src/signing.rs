//! Smart card digital signing via Windows CryptSignMessage.
//!
//! Uses the high-level CryptSignMessage API which handles all CSP, hash
//! algorithm, and key access details internally. This works reliably with
//! smart cards whose CSPs don't support direct CryptCreateHash(SHA-256)
//! or NCryptSignHash.
//!
//! Output is a detached PKCS#7/CMS signature (DER-encoded).

use log::{debug, info, warn};
use std::ptr;
use windows_sys::Win32::Security::Cryptography::*;

/// Result of a successful signing operation.
pub struct SignResult {
    /// Detached CMS/PKCS#7 signature (DER-encoded).
    pub signature: Vec<u8>,
    /// Certificate thumbprint (SHA-1 hex) — used as JWS `kid`.
    pub kid: String,
}

/// Sign data using the AKD smart card signing certificate.
///
/// Uses CryptSignMessage which handles CSP, hashing, and signing internally.
/// Returns a detached PKCS#7/CMS signature.
pub fn sign_with_smartcard(data: &[u8]) -> Result<SignResult, String> {
    unsafe { sign_with_smartcard_inner(data) }
}

unsafe fn sign_with_smartcard_inner(data: &[u8]) -> Result<SignResult, String> {
    const ENCODING: u32 = X509_ASN_ENCODING | PKCS_7_ASN_ENCODING;

    // 1. Open "My" certificate store
    let store_name: Vec<u16> = "My\0".encode_utf16().collect();
    let store = CertOpenSystemStoreW(0, store_name.as_ptr());
    if store.is_null() {
        return Err("Failed to open certificate store".into());
    }

    // 2. Find the signing certificate
    let cert_ctx = find_signing_cert(store, ENCODING);
    if cert_ctx.is_null() {
        CertCloseStore(store, 0);
        return Err(
            "No signing certificate found (OU=Signing). Is the AKD smart card inserted?".into(),
        );
    }

    // 3. Get certificate thumbprint for kid
    let kid = get_cert_thumbprint(cert_ctx)?;
    info!("Found signing cert, thumbprint (kid): {}", &kid[..kid.len().min(16)]);

    // 4. Sign using CryptSignMessage — handles CSP, hash, key internally
    // SHA-256 OID: 2.16.840.1.101.3.4.2.1
    let hash_oid = b"2.16.840.1.101.3.4.2.1\0";

    let sign_params = CRYPT_SIGN_MESSAGE_PARA {
        cbSize: std::mem::size_of::<CRYPT_SIGN_MESSAGE_PARA>() as u32,
        dwMsgEncodingType: ENCODING,
        pSigningCert: cert_ctx,
        HashAlgorithm: CRYPT_ALGORITHM_IDENTIFIER {
            pszObjId: hash_oid.as_ptr() as *mut u8,
            Parameters: CRYPT_INTEGER_BLOB {
                cbData: 0,
                pbData: ptr::null_mut(),
            },
        },
        pvHashAuxInfo: ptr::null_mut(),
        cMsgCert: 0,          // Don't include cert in output
        rgpMsgCert: ptr::null_mut(),
        cMsgCrl: 0,
        rgpMsgCrl: ptr::null_mut(),
        cAuthAttr: 0,
        rgAuthAttr: ptr::null_mut(),
        cUnauthAttr: 0,
        rgUnauthAttr: ptr::null_mut(),
        dwFlags: 0,
        dwInnerContentType: 0,
    };

    // Data to sign
    let data_ptr: *const u8 = data.as_ptr();
    let data_len: u32 = data.len() as u32;

    // Get signature size first
    let mut sig_size: u32 = 0;
    let ok = CryptSignMessage(
        &sign_params,
        1, // fDetachedSignature = TRUE (detached)
        1, // cToBeSigned = 1 data blob
        &data_ptr,
        &data_len,
        ptr::null_mut(),
        &mut sig_size,
    );

    if ok == 0 {
        let err = windows_sys::Win32::Foundation::GetLastError();
        CertFreeCertificateContext(cert_ctx);
        CertCloseStore(store, 0);
        return Err(format!(
            "CryptSignMessage size query failed (err=0x{:08x})",
            err
        ));
    }

    info!("CryptSignMessage: signature will be {} bytes", sig_size);

    // Allocate and sign
    let mut sig_buf = vec![0u8; sig_size as usize];
    let ok = CryptSignMessage(
        &sign_params,
        1,
        1,
        &data_ptr,
        &data_len,
        sig_buf.as_mut_ptr(),
        &mut sig_size,
    );

    CertFreeCertificateContext(cert_ctx);
    CertCloseStore(store, 0);

    if ok == 0 {
        let err = windows_sys::Win32::Foundation::GetLastError();
        return Err(format!(
            "CryptSignMessage failed (err=0x{:08x}). PIN cancelled or card error?",
            err
        ));
    }

    sig_buf.truncate(sig_size as usize);
    info!("Signing successful, CMS signature size: {} bytes", sig_buf.len());

    Ok(SignResult {
        signature: sig_buf,
        kid,
    })
}

/// Find a certificate with OU=Signing in the store.
unsafe fn find_signing_cert(store: *mut core::ffi::c_void, encoding: u32) -> *const CERT_CONTEXT {
    let mut prev_ctx: *const CERT_CONTEXT = ptr::null();

    loop {
        let ctx = CertEnumCertificatesInStore(store, prev_ctx);
        if ctx.is_null() {
            break;
        }

        let cert_info = &*(*ctx).pCertInfo;
        let name_blob = &cert_info.Subject;

        let len = CertNameToStrW(encoding, name_blob, CERT_X500_NAME_STR, ptr::null_mut(), 0);
        if len > 1 {
            let mut buf = vec![0u16; len as usize];
            CertNameToStrW(encoding, name_blob, CERT_X500_NAME_STR, buf.as_mut_ptr(), len);
            let subject = String::from_utf16_lossy(&buf);
            let subject = subject.trim_end_matches('\0');
            debug!("Checking cert: {}", subject);

            if subject.contains("OU=Signing") || subject.contains("OU=Digital Signature") {
                info!("Found signing certificate: {}", subject);
                return ctx;
            }
        }
        prev_ctx = ctx;
    }

    // Fallback: any non-Identification cert
    warn!("No OU=Signing cert found, trying fallback...");
    prev_ctx = ptr::null();
    loop {
        let ctx = CertEnumCertificatesInStore(store, prev_ctx);
        if ctx.is_null() {
            break;
        }

        let cert_info = &*(*ctx).pCertInfo;
        let name_blob = &cert_info.Subject;
        let len = CertNameToStrW(encoding, name_blob, CERT_X500_NAME_STR, ptr::null_mut(), 0);
        if len > 1 {
            let mut buf = vec![0u16; len as usize];
            CertNameToStrW(encoding, name_blob, CERT_X500_NAME_STR, buf.as_mut_ptr(), len);
            let subject = String::from_utf16_lossy(&buf);
            let subject = subject.trim_end_matches('\0');

            if !subject.contains("OU=Identification") {
                info!("Fallback signing certificate: {}", subject);
                return ctx;
            }
        }
        prev_ctx = ctx;
    }

    ptr::null()
}

/// Get SHA-1 thumbprint of a certificate (hex string).
unsafe fn get_cert_thumbprint(ctx: *const CERT_CONTEXT) -> Result<String, String> {
    let mut hash_size: u32 = 20;
    let mut hash_buf = [0u8; 20];

    let ok = CryptHashCertificate(
        0,
        CALG_SHA1,
        0,
        (*ctx).pbCertEncoded,
        (*ctx).cbCertEncoded,
        hash_buf.as_mut_ptr(),
        &mut hash_size,
    );

    if ok == 0 {
        return Err("Failed to compute certificate thumbprint".into());
    }

    Ok(hash_buf[..hash_size as usize]
        .iter()
        .map(|b| format!("{:02x}", b))
        .collect())
}
