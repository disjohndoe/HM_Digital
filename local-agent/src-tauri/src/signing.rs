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

    // 2. Collect all candidate certs (signing first, then identification as fallback)
    let certs = find_all_certs(store, ENCODING);
    if certs.is_empty() {
        CertCloseStore(store, 0);
        return Err("No certificates found in store. Is the AKD smart card inserted?".into());
    }

    // 3. Try each cert with SHA-256, then SHA-1
    let hash_oids: &[(&[u8], &str)] = &[
        (b"2.16.840.1.101.3.4.2.1\0", "SHA-256"),
        (b"1.3.14.3.2.26\0", "SHA-1"),
    ];

    for (cert_ctx, cert_label) in &certs {
        let kid = match get_cert_thumbprint(*cert_ctx) {
            Ok(k) => k,
            Err(_) => continue,
        };
        for (hash_oid, hash_name) in hash_oids {
            info!("Trying {} with {} ...", cert_label, hash_name);
            match try_sign_message(*cert_ctx, ENCODING, hash_oid, data) {
                Ok(sig) => {
                    info!("Signing successful with {} + {}, CMS sig size: {} bytes", cert_label, hash_name, sig.len());
                    // Cleanup all certs
                    for (ctx, _) in &certs {
                        CertFreeCertificateContext(*ctx);
                    }
                    CertCloseStore(store, 0);
                    return Ok(SignResult { signature: sig, kid });
                }
                Err(e) => {
                    warn!("{} with {} failed: {}", cert_label, hash_name, e);
                }
            }
        }
    }

    for (ctx, _) in &certs {
        CertFreeCertificateContext(*ctx);
    }
    CertCloseStore(store, 0);
    Err("All signing attempts failed with all certificates and hash algorithms".into())
}

unsafe fn try_sign_message(
    cert_ctx: *const CERT_CONTEXT,
    encoding: u32,
    hash_oid: &[u8],
    data: &[u8],
) -> Result<Vec<u8>, String> {

    let sign_params = CRYPT_SIGN_MESSAGE_PARA {
        cbSize: std::mem::size_of::<CRYPT_SIGN_MESSAGE_PARA>() as u32,
        dwMsgEncodingType: encoding,
        pSigningCert: cert_ctx,
        HashAlgorithm: CRYPT_ALGORITHM_IDENTIFIER {
            pszObjId: hash_oid.as_ptr() as *mut u8,
            Parameters: CRYPT_INTEGER_BLOB {
                cbData: 0,
                pbData: ptr::null_mut(),
            },
        },
        pvHashAuxInfo: ptr::null_mut(),
        cMsgCert: 0,
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

    let data_ptr: *const u8 = data.as_ptr();
    let data_len: u32 = data.len() as u32;

    // Get signature size
    let mut sig_size: u32 = 0;
    let ok = CryptSignMessage(
        &sign_params,
        1, // detached
        1,
        &data_ptr,
        &data_len,
        ptr::null_mut(),
        &mut sig_size,
    );

    if ok == 0 {
        let err = windows_sys::Win32::Foundation::GetLastError();
        return Err(format!("size query failed (err=0x{:08x})", err));
    }

    // Sign
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

    if ok == 0 {
        let err = windows_sys::Win32::Foundation::GetLastError();
        return Err(format!("sign failed (err=0x{:08x})", err));
    }

    sig_buf.truncate(sig_size as usize);
    Ok(sig_buf)
}

/// Find all candidate certificates, signing certs first, then identification as fallback.
/// Returns duplicated cert contexts (caller must free each).
unsafe fn find_all_certs(store: *mut core::ffi::c_void, encoding: u32) -> Vec<(*const CERT_CONTEXT, String)> {
    let mut signing_certs = Vec::new();
    let mut other_certs = Vec::new();
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
            let subject = subject.trim_end_matches('\0').to_string();
            info!("Found cert: {}", subject);

            // Duplicate the context so enumeration can continue
            let dup = CertDuplicateCertificateContext(ctx) as *const CERT_CONTEXT;

            if subject.contains("OU=Signing") || subject.contains("OU=SignatureTest") || subject.contains("OU=Digital Signature") {
                signing_certs.push((dup, format!("signing({})", subject)));
            } else {
                other_certs.push((dup, format!("fallback({})", subject)));
            }
        }
        prev_ctx = ctx;
    }

    info!("Found {} signing + {} other certs", signing_certs.len(), other_certs.len());

    // Signing certs first, then others as fallback
    signing_certs.extend(other_certs);
    signing_certs
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
