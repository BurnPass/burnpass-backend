import datetime

from cryptography import x509
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.x509.oid import NameOID


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


def gen_csca_dsc(folder=""):
    # CSCA certificate
    csca_name = 'CN=National CSCA of Germany/C=FR/'
    csca_private_key = ec.generate_private_key(ec.SECP256R1())
    csca_public_key = csca_private_key.public_key()
    csca_cert = gen_certificate(csca_name, csca_name, csca_public_key, csca_private_key, 3650)
    csca_pem = csca_cert.public_bytes(serialization.Encoding.PEM)
    with open(folder + "csca.pem", "wb") as f:
        f.write(csca_pem)
    # DSC certificates
    masterlist = b""
    # 1 2 3 4 werden nur exemplarisch verwendet um eine masterlist anzulegen
    for i in [1, 2, 3, 4, "worker"]:
        dsc_name = "/CN=DSC " + str(i) + " for fire protection/C=FR/"
        dsc_private_key = ec.generate_private_key(ec.SECP256R1())
        dsca_cert = gen_certificate(dsc_name, csca_name, dsc_private_key.public_key(), csca_private_key, 1780)
        masterlist += (dsca_cert.public_bytes(serialization.Encoding.PEM))
        if i == "worker":
            with open(folder + "dsc-worker.key", "wb") as f:
                f.write(dsc_private_key.private_bytes(encoding=serialization.Encoding.PEM,
                                                      format=serialization.PrivateFormat.PKCS8,
                                                      encryption_algorithm=serialization.NoEncryption()))
            with open(folder + "dsc-worker.pem", "wb") as f:
                f.write(dsca_cert.public_bytes(serialization.Encoding.PEM))
    with open(folder + "masterlist-dsc.pem", "wb") as f:
        f.write(masterlist)


if __name__ == "__main__":
    gen_csca_dsc()
