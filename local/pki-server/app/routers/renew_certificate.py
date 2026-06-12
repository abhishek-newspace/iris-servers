# app/routers/renew_certificate.py
from fastapi import APIRouter, HTTPException, Depends
from fastapi.security import HTTPBearer
from cryptography import x509
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.backends import default_backend
from pathlib import Path
from datetime import datetime, timezone
import os
import logging

from app.ca.ca_manager import (
    load_intermediate_ca,
    sign_csr,
    track_certificate,
    is_certificate_revoked,   # optional but recommended
)

logger = logging.getLogger("pki-server")
router = APIRouter(tags=["Certificates"])

# -------------------------
# Paths
# -------------------------
PKI_BASE = Path(os.getenv("PKI_BASE_PATH", "/pki"))
ISSUED_DIR = PKI_BASE / "issued"
ISSUED_DIR.mkdir(parents=True, exist_ok=True)

# -------------------------
# Auth
# -------------------------
API_KEYS = os.getenv("ADMIN_API_KEYS", "backend-secret-key,admin-secret-key").split(",")
security = HTTPBearer()

def verify_api_key(authorization: str = Depends(security)):
    if authorization.credentials not in API_KEYS:
        raise HTTPException(status_code=401, detail="Invalid API key")
    return authorization.credentials


# =========================================================
# Unified CSR-based Renewal / Issuance Endpoint
# =========================================================
@router.post("/renew-entity-certificate")
async def renew_entity_certificate(
    request: dict,
    api_key: str = Depends(verify_api_key)
):
    """
    Issue or renew a certificate using CSR.
    Primary identifier is robot_id (backward compatible).
    """

    robot_id = request.get("robot_id")
    entity_type = request.get("entity_type", "robot")
    csr_pem = request.get("csr")
    current_cert_pem = request.get("current_certificate")
    validity_seconds = int(request.get("validity_seconds", 3600))

    if not robot_id or not csr_pem:
        raise HTTPException(
            status_code=400,
            detail="Missing required fields: robot_id and csr"
        )

    entity_name = robot_id  

    logger.info(
        f"Renew request: robot_id={robot_id}, type={entity_type}, "
        f"has_csr={bool(csr_pem)}, validity={validity_seconds}s"
    )

    # -------------------------
    # Load Intermediate CA
    # -------------------------
    try:
        inter_key, inter_cert = load_intermediate_ca()
    except Exception as e:
        logger.error(f"Failed to load intermediate CA: {e}")
        raise HTTPException(500, "Failed to load intermediate CA")

    # -------------------------
    # Optional: validate current cert (warn only)
    # -------------------------
    if current_cert_pem:
        try:
            current_cert = x509.load_pem_x509_certificate(
                current_cert_pem.encode("utf-8"),
                default_backend()
            )

            if current_cert.not_valid_after_utc < datetime.now(timezone.utc):
                logger.warning(f"{robot_id}: current cert expired")

            if is_certificate_revoked and is_certificate_revoked(current_cert.serial_number):
                logger.warning(f"{robot_id}: current cert revoked")

        except Exception as e:
            logger.warning(f"Could not parse current cert: {e}")

    # -------------------------
    # Sign CSR
    # -------------------------
    try:
        new_cert = sign_csr(
            inter_key,
            inter_cert,
            csr_pem.encode("utf-8"),
            validity_seconds=validity_seconds,
        )
    except Exception as e:
        logger.error(f"CSR signing failed: {e}")
        raise HTTPException(400, f"Invalid CSR: {e}")

    # -------------------------
    # Persist certificate
    # -------------------------
    entity_dir = ISSUED_DIR / f"{entity_type}s"
    entity_dir.mkdir(parents=True, exist_ok=True)

    cert_path = entity_dir / f"{robot_id}.cert.pem"
    with open(cert_path, "wb") as f:
        f.write(new_cert.public_bytes(serialization.Encoding.PEM))

    # -------------------------
    # Track certificate
    # -------------------------
    track_certificate(
        f"{entity_type}s",
        robot_id,
        new_cert,
        cert_path
    )

    logger.info(
        f"Certificate issued for {entity_type} '{robot_id}', "
        f"serial={new_cert.serial_number}"
    )

    # -------------------------
    # Response (same shape as old API)
    # -------------------------
    return {
        "success": True,
        "message": "Certificate renewed successfully",
        "robot_id": robot_id,
        "certificate": new_cert.public_bytes(serialization.Encoding.PEM).decode("utf-8"),
        "serial_number": str(new_cert.serial_number),
        "expires_at": new_cert.not_valid_after_utc.isoformat(),
        "validity_seconds": validity_seconds,
    }

