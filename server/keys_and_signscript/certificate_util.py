from cryptography import x509
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.serialization import load_pem_private_key
from cryptography.x509.oid import NameOID
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import ec
import datetime


# generate certificate with random serial number and SHA256 hash that's valid from now
def gen_certificate(subj_name, issuer_name, subj_public_key, issuer_private_key, valid_days):
    builder = x509.CertificateBuilder()
    subj_name = x509.Name([x509.NameAttribute(NameOID.COMMON_NAME, subj_name), ])
    issuer_name = x509.Name([x509.NameAttribute(NameOID.COMMON_NAME, issuer_name), ])
    builder = builder.subject_name(subj_name)
    builder = builder.issuer_name(issuer_name)
    builder = builder.public_key(subj_public_key)
    builder = builder.serial_number(x509.random_serial_number())
    builder = builder.not_valid_before(datetime.datetime.utcnow())
    builder = builder.not_valid_after(datetime.datetime.utcnow() + datetime.timedelta(days=valid_days))
    return builder.sign(issuer_private_key, hashes.SHA256())


def user_pk_and_cert():
    csca_name = 'CN=National CSCA of Friesland/C=FR/'
    user_name = "user"
    user_privatek = ec.generate_private_key(ec.SECP256R1())
    user_privatek_pem = user_privatek.private_bytes(encoding=serialization.Encoding.PEM,
                                                    format=serialization.PrivateFormat.PKCS8,
                                                    encryption_algorithm=serialization.NoEncryption())
    user_publick = user_privatek.public_key()
    with open("dsc-worker.key", 'rb') as pem_in:
        pemlines = pem_in.read()
    ds_private_key = load_pem_private_key(pemlines, password=None)
    user_cert = gen_certificate(user_name, csca_name, user_publick, ds_private_key, 3650)
    user_cert_pem = user_cert.public_bytes(serialization.Encoding.PEM)
    return user_privatek_pem, user_cert_pem
