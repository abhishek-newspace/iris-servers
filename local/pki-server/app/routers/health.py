# app/routers/health.py
from fastapi import APIRouter
from datetime import datetime, timezone
from pathlib import Path
import logging
import os

logger = logging.getLogger("pki-server")

router = APIRouter(tags=["Health"])

PKI_BASE = Path(os.getenv("PKI_BASE_PATH", "/pki"))
pki_dir = PKI_BASE 

@router.get("/health")
async def health_check():
    """Health check endpoint"""
    try:
        # Check if essential PKI files exist
        status = {
            "status": "healthy",
            "root_ca_exists": (pki_dir / "rootCA.crt.pem").exists(),
            "intermediate_ca_exists": (pki_dir / "intermediateCA.crt.pem").exists(),
            "crl_exists": (pki_dir / "crl" / "intermediate.crl.pem").exists(),
            "certificate_database_exists": (pki_dir / "certificate_database.json").exists(),
            "timestamp": datetime.now(timezone.utc)
        }
        return status
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return {"status": "unhealthy", "error": str(e)}