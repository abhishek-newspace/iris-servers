# ca/csr_tools.py
from cryptography.hazmat.primitives import serialization, hashes
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography import x509
from cryptography.x509.oid import NameOID, ExtendedKeyUsageOID
from pathlib import Path
import ipaddress

def generate_private_key(key_size: int = 2048):
    key = rsa.generate_private_key(public_exponent=65537, key_size=key_size)
    return key

def write_key_to_pem(key, path: str, password: bytes = None):
    enc = serialization.BestAvailableEncryption(password) if password else serialization.NoEncryption()
    pem = key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.TraditionalOpenSSL,
        encryption_algorithm=enc
    )
    # Ensure the parent directory exists
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    
    # Write the key to file
    with open(path, "wb") as f:
        f.write(pem)

def create_csr(key, common_name: str, san_list: list = None):
    name = x509.Name([x509.NameAttribute(NameOID.COMMON_NAME, common_name)])
    csr_builder = x509.CertificateSigningRequestBuilder().subject_name(name)

    if san_list:
        alt_names = []
        for entry in san_list:
            try:
                alt_names.append(x509.IPAddress(ipaddress.ip_address(entry)))
            except ValueError:
                alt_names.append(x509.DNSName(entry))

        csr_builder = csr_builder.add_extension(
            x509.SubjectAlternativeName(alt_names),
            critical=False
        )

    # ADD REQUIRED EXTENSIONS FOR mTLS:
    
    # 1. BasicConstraints extension - CRITICAL for client certificates
    csr_builder = csr_builder.add_extension(
        x509.BasicConstraints(ca=False, path_length=None),
        critical=True
    )
    
    # 2. KeyUsage extension - specifies what the certificate can be used for
    csr_builder = csr_builder.add_extension(
        x509.KeyUsage(
            digital_signature=True,     # Required for TLS client authentication
            content_commitment=False,
            key_encipherment=True,      # Required for TLS
            data_encipherment=False,
            key_agreement=False,
            key_cert_sign=False,        # Must be False for non-CA certificates
            crl_sign=False,             # Must be False for non-CA certificates
            encipher_only=False,
            decipher_only=False
        ),
        critical=True
    )
    
    # 3. ExtendedKeyUsage extension - specifies allowed purposes
    # Include BOTH serverAuth AND clientAuth for certificates used in mTLS
    csr_builder = csr_builder.add_extension(
        x509.ExtendedKeyUsage([
            ExtendedKeyUsageOID.SERVER_AUTH,   # For server-side (broker)
            ExtendedKeyUsageOID.CLIENT_AUTH    # For client-side (when connecting to broker)
        ]),
        critical=False
    )

    csr = csr_builder.sign(key, hashes.SHA256())
    return csr

def write_csr_to_pem(csr, path: str):
    with open(path, "wb") as f:
        f.write(csr.public_bytes(serialization.Encoding.PEM))