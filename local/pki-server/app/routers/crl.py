# app/routers/crl.py
from fastapi import APIRouter, HTTPException
from cryptography.hazmat.primitives import serialization
from app.ca.ca_manager import get_crl, create_crl, load_intermediate_ca
import logging
from pathlib import Path
import os

PKI_BASE = Path(os.getenv("PKI_BASE_PATH", "/pki"))
CRL_DIR = PKI_BASE / "crl"
CRL_DIR.mkdir(parents=True, exist_ok=True)

logger = logging.getLogger("pki-server")

router = APIRouter(tags=["CRL"])

@router.get("/crl")
async def get_crl_api():
    """
    Get current Certificate Revocation List
    """
    try:
        print("🔍 Attempting to load CRL...")
        crl = get_crl()
        if crl is not None:
            crl_pem = crl.public_bytes(serialization.Encoding.PEM).decode()
            revoked_certs = list(crl)            
            return {
                "crl": crl_pem,
                "last_update": crl.last_update_utc.isoformat() if hasattr(crl, "last_update_utc") else crl.last_update.isoformat(),
                "next_update": crl.next_update_utc.isoformat() if hasattr(crl, "next_update_utc") else crl.next_update.isoformat(),
                "revoked_certificates_count": len(revoked_certs)
            }
        else:
            print("CRL is None - file may not exist")
            # Create an empty CRL if none exists
            inter_key, inter_cert = load_intermediate_ca()
            empty_crl = create_crl(inter_key, inter_cert)
            
            # Save the empty CRL
            crl_path = CRL_DIR / "intermediate.crl.pem"
            with open(crl_path, "wb") as f:
                f.write(empty_crl.public_bytes(serialization.Encoding.PEM))
            
            print("Created and saved empty CRL")
            
            return {
                "crl": empty_crl.public_bytes(serialization.Encoding.PEM).decode(),
                "last_update": empty_crl.last_update.isoformat(),
                "next_update": empty_crl.next_update.isoformat(),
                "revoked_certificates_count": 0,
                "message": "Empty CRL created"
            }
            
    except Exception as e:
        logger.error(f"Failed to get CRL: {e}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
        raise HTTPException(500, f"Failed to get CRL: {str(e)}")
