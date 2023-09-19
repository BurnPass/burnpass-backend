import datetime

from cryptography import x509
from cryptography.hazmat.primitives import hashes
from cryptography.x509.oid import NameOID


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
