from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import logging
import os
from pathlib import Path
import uvicorn
import sys

# Routers
from app.routers import (
    health,
    certificates,
    crl,
    validation,
    issuance,
    renew_certificate,
)

# ------------------------------------------------------------------
# Logging
# ------------------------------------------------------------------
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("pki-server")

# ------------------------------------------------------------------
# PKI BASE PATH
# ------------------------------------------------------------------
PKI_BASE = Path(os.getenv("PKI_BASE_PATH", "/pki"))

ISSUED_DIR = PKI_BASE / "issued"
CRL_DIR = PKI_BASE / "crl"

for d in [ISSUED_DIR, CRL_DIR]:
    d.mkdir(parents=True, exist_ok=True)

# ------------------------------------------------------------------
# Validate PKI existence (NO CREATION HERE)
# ------------------------------------------------------------------
ROOT_CA_CERT = PKI_BASE / "rootCA.crt.pem"
ROOT_CA_KEY = PKI_BASE / "rootCA.key.pem"
INTER_CERT = PKI_BASE / "intermediateCA.crt.pem"
INTER_KEY = PKI_BASE / "intermediateCA.key.pem"

missing = [
    p for p in [ROOT_CA_CERT, ROOT_CA_KEY, INTER_CERT, INTER_KEY]
    if not p.exists()
]

if missing:
    logger.critical("PKI NOT INITIALIZED. Missing files:")
    for p in missing:
        logger.critical("  - %s", p)
    logger.critical("Run bootstrap_pki.py once before starting the server.")
    sys.exit(1)

logger.info("PKI material verified")

# ------------------------------------------------------------------
# FastAPI App
# ------------------------------------------------------------------
app = FastAPI(
    title="PKI Server API",
    description="Certificate Authority Management Server",
    version="1.0.0",
)

# ------------------------------------------------------------------
# CORS (tighten in production)
# ------------------------------------------------------------------
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Restrict in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ------------------------------------------------------------------
# Routers
# ------------------------------------------------------------------
app.include_router(health.router, prefix="/api/v1")
app.include_router(certificates.router, prefix="/api/v1")
app.include_router(crl.router, prefix="/api/v1")
app.include_router(validation.router, prefix="/api/v1")
app.include_router(issuance.router, prefix="/api/v1")
app.include_router(renew_certificate.router, prefix="/api/v1")

@app.get("/")
async def root():
    return {
        "status": "PKI Server Running",
        "version": "1.0.0",
    }

# ------------------------------------------------------------------
# Entrypoint
# ------------------------------------------------------------------
if __name__ == "__main__":
    PORT = int(os.getenv("PKI_PORT", "9000"))

    server_cert = ISSUED_DIR / "servers" / "server.cert.pem"
    server_key = ISSUED_DIR / "servers" / "server.key.pem"

    uvicorn.run(
        app,
        host="0.0.0.0",
        port=PORT,
        # ssl_certfile=str(server_cert) if server_cert.exists() else None,
        # ssl_keyfile=str(server_key) if server_key.exists() else None,
    )
