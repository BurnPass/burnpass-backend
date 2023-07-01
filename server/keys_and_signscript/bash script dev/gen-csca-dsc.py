from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import ec
from cryptography import x509
from cryptography.hazmat.primitives import hashes
from cryptography.x509.oid import NameOID
import datetime

private_key = ec.generate_private_key(ec.SECP256R1(), default_backend())
with open("csca.key", "wb") as f:
    f.write((private_key.private_bytes(encoding=serialization.Encoding.PEM,format=serialization.PrivateFormat.PKCS8,encryption_algorithm=serialization.NoEncryption())))
public_key = private_key.public_key()
builder=x509.CertificateBuilder()
subj_name=x509.Name([x509.NameAttribute(NameOID.COMMON_NAME, u'CN=National CSCA of Friesland/C=FR/'),])
builder=builder.subject_name(subj_name).issuer_name(subj_name).public_key(private_key.public_key()).serial_number(x509.random_serial_number())
builder = builder.not_valid_before(datetime.datetime.utcnow()).not_valid_after(datetime.datetime.utcnow() + datetime.timedelta(days=3650))
cert=builder.sign(private_key, hashes.SHA256())
with open("csca.pem", "wb") as f:
    f.write(cert.public_bytes(serialization.Encoding.PEM))
