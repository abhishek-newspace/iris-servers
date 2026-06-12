# app/routers/issuance.py
from fastapi import APIRouter, HTTPException, Depends
from fastapi.security import HTTPBearer
from cryptography.hazmat.primitives import serialization
from app.ca.ca_manager import sign_csr, load_intermediate_ca, track_certificate
from app.ca.csr_tools import generate_private_key, create_csr, write_key_to_pem
import os
import logging
from pathlib import Path

logger = logging.getLogger("pki-server")

router = APIRouter(tags=["Issuance"])

PKI_BASE = Path(os.getenv("PKI_BASE_PATH", "/pki"))
ISSUED_DIR = PKI_BASE / "issued"
ISSUED_DIR.mkdir(parents=True, exist_ok=True)

# API Key authentication
API_KEYS = os.getenv("ADMIN_API_KEYS", "backend-secret-key,admin-secret-key").split(",")
security = HTTPBearer()

def verify_api_key(authorization: str = Depends(security)):
    if authorization.credentials not in API_KEYS:
        raise HTTPException(status_code=401, detail="Invalid API key")
    return authorization.credentials


@router.post("/issue-certificate")
async def issue_certificate(
    request: dict,
    api_key: str = Depends(verify_api_key)
):
    """
    Issue a new certificate (for server / broker).
    """
    try:
        entity_name = request.get("entity_name")
        entity_type = request.get("entity_type", "robot")
        common_name = request.get("common_name", entity_name)
        san_list = request.get("san_list", [])
        validity_seconds = request.get("validity_seconds", 3600)

        if not entity_name:
            raise HTTPException(400, "Entity name required")

        logger.info(f"Issuing new certificate for {entity_type}: {entity_name}")

        # Load intermediate CA
        inter_key, inter_cert = load_intermediate_ca()

        # Generate key and CSR
        key = generate_private_key()
        csr = create_csr(key, common_name=common_name, san_list=san_list)
        csr_pem = csr.public_bytes(encoding=serialization.Encoding.PEM)

        # Sign certificate
        cert = sign_csr(
            inter_key,
            inter_cert,
            csr_pem,
            validity_seconds=validity_seconds
        )

        # Create entity directory
        entity_dir = ISSUED_DIR / f"{entity_type}s"
        entity_dir.mkdir(parents=True, exist_ok=True)

        # Paths
        key_path = entity_dir / f"{entity_name}.key.pem"
        cert_path = entity_dir / f"{entity_name}.cert.pem"

        # Write key and cert
        write_key_to_pem(key, str(key_path))
        with open(cert_path, "wb") as f:
            f.write(cert.public_bytes(serialization.Encoding.PEM))

        # ✅ Create broker chain if entity is broker
        chain_path = None
        if entity_type == "broker":
            chain_path = entity_dir / f"{entity_name}-chain.pem"
            with open(chain_path, "wb") as f:
                f.write(cert.public_bytes(serialization.Encoding.PEM))
                f.write(inter_cert.public_bytes(serialization.Encoding.PEM))

            logger.info(f"Broker certificate chain created at {chain_path}")

        # Track in certificate database
        track_certificate(f"{entity_type}s", entity_name, cert, cert_path)

        logger.info(f"New certificate issued for {entity_type}: {entity_name}")

        return {
            "success": True,
            "message": f"Certificate issued for {entity_name}",
            "certificate": cert.public_bytes(serialization.Encoding.PEM).decode(),
            "private_key": key.private_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PrivateFormat.PKCS8,
                encryption_algorithm=serialization.NoEncryption()
            ).decode(),
            "expires_at": cert.not_valid_after_utc.isoformat(),
            "serial_number": str(cert.serial_number),
            "chain_path": str(chain_path) if chain_path else None
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Certificate issuance failed: {e}")
        raise HTTPException(500, f"Certificate issuance failed: {str(e)}")
