import os
from pathlib import Path
from app.ca.ca_manager import (
    create_self_signed_root,
    create_intermediate_ca,
)

PKI_BASE = Path(os.getenv("PKI_BASE_PATH", "/pki"))

ROOT_CA_DIR = PKI_BASE / "root_ca"
INTERMEDIATE_DIR = PKI_BASE / "intermediate"
CRL_DIR = PKI_BASE / "crl"

for d in [ROOT_CA_DIR, INTERMEDIATE_DIR, CRL_DIR]:
    d.mkdir(parents=True, exist_ok=True)

ROOT_CA_CERT = ROOT_CA_DIR / "rootCA.crt.pem"
INTER_CERT = INTERMEDIATE_DIR / "intermediateCA.crt.pem"

def pki_exists():
    return ROOT_CA_CERT.exists() and INTER_CERT.exists()

if __name__ == "__main__":
    if pki_exists():
        print("PKI already initialized. Exiting.")
        exit(0)

    print("Bootstrapping PKI...")

    root_key, root_cert = create_self_signed_root()
    create_intermediate_ca(root_key, root_cert)

    print("PKI bootstrap completed successfully.")
