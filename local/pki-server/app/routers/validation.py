from fastapi import APIRouter, HTTPException, Depends
from fastapi.security import HTTPBearer
from app.ca.ca_manager import (
    validate_certificate,
    load_cert_database,
    check_all_certificates,
)
import os
import logging
from pathlib import Path
from cryptography import x509
from cryptography.hazmat.backends import default_backend
from datetime import datetime, timezone

logger = logging.getLogger("pki-server")

router = APIRouter(tags=["Validation"])

PKI_BASE = Path(os.getenv("PKI_BASE_PATH", "/pki"))
ISSUED_DIR = PKI_BASE / "issued"

# ------------------------------------------------------------------
# API Key authentication
# ------------------------------------------------------------------
API_KEYS = os.getenv(
    "ADMIN_API_KEYS", "backend-secret-key,admin-secret-key"
).split(",")

security = HTTPBearer()


def verify_api_key(authorization: str = Depends(security)):
    if authorization.credentials not in API_KEYS:
        raise HTTPException(status_code=401, detail="Invalid API key")
    return authorization.credentials


# ------------------------------------------------------------------
# Helper: locate certificate across entity types
# ------------------------------------------------------------------
def find_certificate(entity_name: str) -> Path | None:
    """
    Search for a certificate under issued/<entity_type>s/
    """
    for entity_dir in ["robots", "servers", "brokers"]:
        cert_path = ISSUED_DIR / entity_dir / f"{entity_name}.cert.pem"
        if cert_path.exists():
            return cert_path
    return None


# ------------------------------------------------------------------
# Certificate status (human-readable)
# ------------------------------------------------------------------
@router.get("/certificate-status/{entity_name}")
def get_certificate_info(entity_name: str):
    try:
        cert_path = find_certificate(entity_name)
        if not cert_path:
            return {"error": f"Certificate not found for {entity_name}"}

        with open(cert_path, "rb") as f:
            cert_data = f.read()

        cert = x509.load_pem_x509_certificate(cert_data, default_backend())

        not_valid_before = cert.not_valid_before.replace(
            tzinfo=timezone.utc
        ).isoformat()
        not_valid_after = cert.not_valid_after.replace(
            tzinfo=timezone.utc
        ).isoformat()

        subject = {attr.oid._name: attr.value for attr in cert.subject}
        issuer = {attr.oid._name: attr.value for attr in cert.issuer}

        now_utc = datetime.now(timezone.utc)
        is_expired = now_utc > cert.not_valid_after.replace(
            tzinfo=timezone.utc
        )

        return {
            "entity_name": entity_name,
            "subject": subject,
            "issuer": issuer,
            "not_valid_before": not_valid_before,
            "not_valid_after": not_valid_after,
            "is_expired": is_expired,
            "is_revoked": False,  # detailed revocation handled elsewhere
            "certificate_path": str(cert_path),
        }

    except Exception as e:
        logger.error(f"Failed to fetch certificate info: {e}")
        return {"error": str(e)}


# ------------------------------------------------------------------
# List all certificates (tracked)
# ------------------------------------------------------------------
@router.get("/certificates")
async def list_all_certificates(api_key: str = Depends(verify_api_key)):
    """
    List all tracked certificates with their lifecycle status
    """
    try:
        db = load_cert_database()
        status_report = check_all_certificates()

        total = sum(len(certs) for certs in db.values())

        return {
            "certificate_database": db,
            "status_summary": status_report,
            "total_certificates": total,
        }

    except Exception as e:
        logger.error(f"Failed to list certificates: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to list certificates: {str(e)}",
        )


# ------------------------------------------------------------------
# Validate a single certificate (expiry + CRL)
# ------------------------------------------------------------------
@router.get("/validate/{entity_name}")
async def validate_certificate_api(
    entity_name: str, api_key: str = Depends(verify_api_key)
):
    """
    Validate a specific certificate (expiry + revocation)
    """
    try:
        cert_path = find_certificate(entity_name)
        if not cert_path:
            raise HTTPException(
                status_code=404,
                detail=f"Certificate not found for {entity_name}",
            )

        is_valid, message = validate_certificate(cert_path)

        return {
            "entity_name": entity_name,
            "is_valid": is_valid,
            "message": message,
            "certificate_path": str(cert_path),
            "validation_timestamp": datetime.now(timezone.utc).isoformat(),
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Certificate validation failed: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Certificate validation failed: {str(e)}",
        )
