#!/usr/bin/env python3
"""
Generate TLS Certificates using Python (No OpenSSL Required)
===========================================================
This script generates self-signed certificates using Python's cryptography library
instead of requiring OpenSSL to be installed.
"""

import os
import sys
import ipaddress
from datetime import datetime, timedelta, timezone
from cryptography import x509
from cryptography.x509.oid import NameOID
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.backends import default_backend

def create_certificates():
    """Create TLS certificates for EMQX"""
    print("[INFO] Generating TLS certificates for EMQX MQTT broker...")
    
    # Create certificates directory
    cert_dir = "certs"
    if not os.path.exists(cert_dir):
        os.makedirs(cert_dir)
        print(f"[SUCCESS] Created certificates directory: {cert_dir}")
    
    # Generate CA private key
    print("[INFO] Generating CA private key...")
    ca_private_key = rsa.generate_private_key(
        public_exponent=65537,
        key_size=4096,
        backend=default_backend()
    )
    
    # Generate CA certificate
    print("[INFO] Generating CA certificate...")
    ca_name = x509.Name([
        x509.NameAttribute(NameOID.COUNTRY_NAME, "VN"),
        x509.NameAttribute(NameOID.STATE_OR_PROVINCE_NAME, "Ho Chi Minh"),
        x509.NameAttribute(NameOID.LOCALITY_NAME, "Ho Chi Minh City"),
        x509.NameAttribute(NameOID.ORGANIZATION_NAME, "IoT Security Testing"),
        x509.NameAttribute(NameOID.ORGANIZATIONAL_UNIT_NAME, "Development"),
        x509.NameAttribute(NameOID.COMMON_NAME, "IoT-CA"),
    ])
    
    ca_cert = x509.CertificateBuilder().subject_name(
        ca_name
    ).issuer_name(
        ca_name
    ).public_key(
        ca_private_key.public_key()
    ).serial_number(
        x509.random_serial_number()
    ).not_valid_before(
        datetime.now(timezone.utc)
    ).not_valid_after(
        datetime.now(timezone.utc) + timedelta(days=365)
    ).add_extension(
        x509.BasicConstraints(ca=True, path_length=None),
        critical=True,
    ).sign(ca_private_key, hashes.SHA256(), default_backend())
    
    # Generate server private key
    print("[INFO] Generating server private key...")
    server_private_key = rsa.generate_private_key(
        public_exponent=65537,
        key_size=4096,
        backend=default_backend()
    )
    
    # Generate server certificate signing request
    print("[INFO] Generating server certificate signing request...")
    server_name = x509.Name([
        x509.NameAttribute(NameOID.COUNTRY_NAME, "VN"),
        x509.NameAttribute(NameOID.STATE_OR_PROVINCE_NAME, "Ho Chi Minh"),
        x509.NameAttribute(NameOID.LOCALITY_NAME, "Ho Chi Minh City"),
        x509.NameAttribute(NameOID.ORGANIZATION_NAME, "IoT Security Testing"),
        x509.NameAttribute(NameOID.ORGANIZATIONAL_UNIT_NAME, "Development"),
        x509.NameAttribute(NameOID.COMMON_NAME, "emqx"),
    ])
    
    csr = x509.CertificateSigningRequestBuilder().subject_name(
        server_name
    ).add_extension(
        x509.SubjectAlternativeName([
            x509.DNSName("localhost"),
            x509.DNSName("emqx"),
            x509.IPAddress(ipaddress.IPv4Address("127.0.0.1")),
        ]),
        critical=False,
    ).sign(server_private_key, hashes.SHA256(), default_backend())
    
    # Generate server certificate signed by CA
    print("[INFO] Generating server certificate...")
    server_cert = x509.CertificateBuilder().subject_name(
        csr.subject
    ).issuer_name(
        ca_cert.subject
    ).public_key(
        csr.public_key()
    ).serial_number(
        x509.random_serial_number()
    ).not_valid_before(
        datetime.now(timezone.utc)
    ).not_valid_after(
        datetime.now(timezone.utc) + timedelta(days=365)
    ).add_extension(
        x509.SubjectAlternativeName([
            x509.DNSName("localhost"),
            x509.DNSName("emqx"),
            x509.IPAddress(ipaddress.IPv4Address("127.0.0.1")),
        ]),
        critical=False,
    ).sign(ca_private_key, hashes.SHA256(), default_backend())
    
    # Save CA private key
    with open(os.path.join(cert_dir, "ca-key.pem"), "wb") as f:
        f.write(ca_private_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.NoEncryption()
        ))
    
    # Save CA certificate
    with open(os.path.join(cert_dir, "ca-cert.pem"), "wb") as f:
        f.write(ca_cert.public_bytes(serialization.Encoding.PEM))
    
    # Save server private key
    with open(os.path.join(cert_dir, "server-key.pem"), "wb") as f:
        f.write(server_private_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.NoEncryption()
        ))
    
    # Save server certificate
    with open(os.path.join(cert_dir, "server-cert.pem"), "wb") as f:
        f.write(server_cert.public_bytes(serialization.Encoding.PEM))
    
    print("[SUCCESS] TLS certificates generated successfully!")
    print("")
    print("Certificate files:")
    print(f"   CA Certificate: {cert_dir}/ca-cert.pem")
    print(f"   CA Private Key: {cert_dir}/ca-key.pem")
    print(f"   Server Certificate: {cert_dir}/server-cert.pem")
    print(f"   Server Private Key: {cert_dir}/server-key.pem")
    print("")
    print("Next steps:")
    print("   1. Update docker-compose.yml to use TLS certificates")
    print("   2. Configure EMQX TLS listeners")
    print("   3. Update client connections to use TLS")
    print("   4. Test TLS connections")

def main():
    """Main function"""
    try:
        create_certificates()
    except ImportError:
        print("[ERROR] cryptography library not found!")
        print("Please install it with: pip install cryptography")
        sys.exit(1)
    except Exception as e:
        print(f"[ERROR] Error generating certificates: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
