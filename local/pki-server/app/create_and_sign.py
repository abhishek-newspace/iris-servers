# import os
# import ipaddress
# from pathlib import Path
# from cryptography.hazmat.primitives import serialization
# from cryptography import x509

# from app.ca.csr_tools import (
#     generate_private_key,
#     write_key_to_pem,
#     create_csr,
# )
# from app.ca.ca_manager import (
#     create_self_signed_root,
#     create_intermediate_ca,
#     sign_csr,
#     write_cert_and_chain,
# )

# # ------------------------------------------------------------------
# # PKI BASE PATH (Docker-safe)
# # ------------------------------------------------------------------
# PKI_BASE = Path(os.getenv("PKI_BASE_PATH", "/pki"))

# ROOT_CA_DIR = PKI_BASE / "root_ca"
# INTERMEDIATE_DIR = PKI_BASE / "intermediate"
# ISSUED_DIR = PKI_BASE / "issued"

# for d in [ROOT_CA_DIR, INTERMEDIATE_DIR, ISSUED_DIR]:
#     d.mkdir(parents=True, exist_ok=True)


# # ------------------------------------------------------------------
# # PKI bootstrap (Root + Intermediate)
# # ------------------------------------------------------------------
# def setup_pki():
#     """
#     Create Root CA and Intermediate CA
#     (should normally be run once)
#     """
#     root_key, root_cert = create_self_signed_root()
#     inter_key, inter_cert = create_intermediate_ca(root_key, root_cert)
#     return root_key, root_cert, inter_key, inter_cert


# # ------------------------------------------------------------------
# # Entity certificate creation (server / broker / dev only)
# # ------------------------------------------------------------------
# def create_entity_certificate(
#     entity_name: str,
#     entity_type: str,
#     inter_key,
#     inter_cert,
#     validity_seconds: int = 120,
#     san_list: list | None = None,
# ):
#     """
#     Create key + certificate for an entity.
#     NOT FOR ROBOTS IN PRODUCTION.
#     """

#     entity_dir = ISSUED_DIR / f"{entity_type}s"
#     entity_dir.mkdir(parents=True, exist_ok=True)

#     key_path = entity_dir / f"{entity_name}.key.pem"
#     cert_path = entity_dir / f"{entity_name}.cert.pem"

#     # Remove existing files if present
#     if key_path.exists():
#         key_path.unlink()
#     if cert_path.exists():
#         cert_path.unlink()

#     # Generate private key
#     key = generate_private_key()
#     write_key_to_pem(key, str(key_path))

#     # Create CSR with SANs
#     csr = create_csr(
#         key,
#         common_name=entity_name,
#         san_list=san_list,
#     )

#     csr_pem = csr.public_bytes(encoding=serialization.Encoding.PEM)

#     # Sign CSR
#     cert = sign_csr(
#         inter_key,
#         inter_cert,
#         csr_pem,
#         validity_seconds=validity_seconds,
#     )

#     # Write certificate
#     with open(cert_path, "wb") as f:
#         f.write(cert.public_bytes(serialization.Encoding.PEM))

#     print(
#         f"{entity_type} certificate created: {cert_path} "
#         f"(valid for {validity_seconds} seconds)"
#     )

#     # Debug: verify extensions
#     print(f"Extensions for {entity_name}:")
#     cert_obj = x509.load_pem_x509_certificate(
#         cert.public_bytes(serialization.Encoding.PEM)
#     )
#     for ext in cert_obj.extensions:
#         print(f"  - {ext.oid._name}: {ext.value}")

#     return key, cert


# # ------------------------------------------------------------------
# # CLI usage (dev / infra only)
# # ------------------------------------------------------------------
# if __name__ == "__main__":
#     # Initialize PKI
#     root_key, root_cert, inter_key, inter_cert = setup_pki()

#     # -------------------------
#     # Broker certificate
#     # -------------------------
#     broker_key, broker_cert = create_entity_certificate(
#         entity_name="broker",
#         entity_type="broker",
#         inter_key=inter_key,
#         inter_cert=inter_cert,
#         validity_seconds=3600,
#         san_list=[
#             "192.168.0.222",
#             "mosquitto",
#             "localhost",
#             "127.0.0.1",
#             "broker",
#         ],
#     )

#     # Broker chain (broker + intermediate)
#     broker_chain_path = ISSUED_DIR / "brokers" / "broker-chain.pem"
#     with open(broker_chain_path, "wb") as f:
#         f.write(broker_cert.public_bytes(serialization.Encoding.PEM))
#         f.write(inter_cert.public_bytes(serialization.Encoding.PEM))

#     print("Broker chain created at", broker_chain_path)

#     # -------------------------
#     # Server certificate
#     # -------------------------
#     server_key, server_cert = create_entity_certificate(
#         entity_name="server",
#         entity_type="server",
#         inter_key=inter_key,
#         inter_cert=inter_cert,
#         validity_seconds=3600,
#         san_list=[
#             "192.168.0.222",
#             "localhost",
#             "127.0.0.1",
#             "server",
#         ],
#     )

#     # -------------------------
#     # ⚠️ Robot certificate (DEV ONLY)
#     # -------------------------
#     robot_key, robot_cert = create_entity_certificate(
#         entity_name="robot01",
#         entity_type="robot",
#         inter_key=inter_key,
#         inter_cert=inter_cert,
#         validity_seconds=3600,
#         san_list=[
#             "raspberrypi.local",
#             "robot01",
#         ],
#     )

#     print("\nGenerated files:")
#     print(" - /pki/issued/brokers/broker.key.pem")
#     print(" - /pki/issued/brokers/broker.cert.pem")
#     print(" - /pki/issued/brokers/broker-chain.pem")
#     print(" - /pki/issued/servers/server.key.pem")
#     print(" - /pki/issued/servers/server.cert.pem")
#     print(" - /pki/issued/robots/robot01.key.pem (DEV ONLY)")
#     print(" - /pki/issued/robots/robot01.cert.pem (DEV ONLY)")
#     print(" - Root certificate to distribute: /pki/root_ca/rootCA.crt.pem")
