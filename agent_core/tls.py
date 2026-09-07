"""Persistent local TLS identity. No CA service, HTTP fallback or custom crypto."""
from datetime import datetime, timedelta, timezone
import ipaddress
import os
from pathlib import Path
import ssl
import subprocess
import tempfile


def create_server_context(directory: Path) -> ssl.SSLContext:
    """Create the identity once; a damaged existing identity requires explicit repair."""
    certificate = directory / "agent-cert.pem"
    key = directory / "agent-key.pem"
    directory.mkdir(parents=True, exist_ok=True)
    if not certificate.exists() and not key.exists():
        with tempfile.TemporaryDirectory(prefix=".tls-", dir=directory) as temp:
            temp_cert, temp_key = Path(temp) / certificate.name, Path(temp) / key.name
            try:
                from cryptography import x509
                from cryptography.hazmat.primitives import hashes, serialization
                from cryptography.hazmat.primitives.asymmetric import rsa
                from cryptography.x509.oid import NameOID
            except ImportError:
                # DSM ships OpenSSL; do not bundle architecture-specific crypto wheels.
                subprocess.run([
                    "openssl", "req", "-x509", "-newkey", "rsa:2048", "-sha256",
                    "-nodes", "-days", "3650", "-subj", "/CN=localhost",
                    "-addext", "subjectAltName=DNS:localhost,IP:127.0.0.1",
                    "-keyout", str(temp_key), "-out", str(temp_cert),
                ], check=True, capture_output=True, timeout=60)
            else:
                private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
                subject = x509.Name([x509.NameAttribute(NameOID.COMMON_NAME, "localhost")])
                now = datetime.now(timezone.utc)
                cert = (x509.CertificateBuilder().subject_name(subject).issuer_name(subject)
                    .public_key(private_key.public_key()).serial_number(x509.random_serial_number())
                    .not_valid_before(now - timedelta(days=1)).not_valid_after(now + timedelta(days=3650))
                    .add_extension(x509.SubjectAlternativeName([
                        x509.DNSName("localhost"), x509.IPAddress(ipaddress.ip_address("127.0.0.1"))
                    ]), critical=False).sign(private_key, hashes.SHA256()))
                temp_key.write_bytes(private_key.private_bytes(serialization.Encoding.PEM,
                    serialization.PrivateFormat.PKCS8, serialization.NoEncryption()))
                temp_cert.write_bytes(cert.public_bytes(serialization.Encoding.PEM))
            temp_key.chmod(0o600)
            os.replace(temp_key, key)
            os.replace(temp_cert, certificate)
    context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
    context.minimum_version = ssl.TLSVersion.TLSv1_2
    context.load_cert_chain(certificate, key)
    return context
