from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import ec
from cryptography import x509
from cryptography.hazmat.primitives import hashes
from cryptography.x509.oid import NameOID
import datetime

#generate certificate with random serial number and SHA256 hash thats valid from now
def gen_certificate(subj_name,issuer_name,subj_public_key,issuer_private_key,valid_days):
    builder=x509.CertificateBuilder()
    subj_name=x509.Name([x509.NameAttribute(NameOID.COMMON_NAME, subj_name),])
    issuer_name=x509.Name([x509.NameAttribute(NameOID.COMMON_NAME, issuer_name),])
    builder=builder.subject_name(subj_name)
    builder=builder.issuer_name(subj_name)
    builder=builder.public_key(subj_public_key)
    builder=builder.serial_number(x509.random_serial_number())
    builder=builder.not_valid_before(datetime.datetime.utcnow())
    builder=builder.not_valid_after(datetime.datetime.utcnow() + datetime.timedelta(days=valid_days))
    return builder.sign(issuer_private_key, hashes.SHA256())

def make_CSCA_DSC():
    #CSCA certificate
    csca_name='CN=National CSCA of Friesland/C=FR/'
    csca_private_key = ec.generate_private_key(ec.SECP256R1(), default_backend())
    #with open("csca.key", "wb") as f:
    #    f.write((csca_private_key.private_bytes(encoding=serialization.Encoding.PEM,format=serialization.PrivateFormat.PKCS8,encryption_algorithm=serialization.NoEncryption())))
    csca_public_key = csca_private_key.public_key()
    csca_cert=gen_certificate(csca_name,csca_name,csca_public_key,csca_private_key,3650)
    csca_pem=csca_cert.public_bytes(serialization.Encoding.PEM)
    with open("csca.pem", "wb") as f:
        f.write(csca_pem)
    #DSC certificates
    masterlist=b""
    #1 2 3 4 werden nur exemplarisch verwendet um eine masterlist anzulegen
    for i in [1,2,3,4,"worker"]:
        dsc_name="/CN=DSC "+str(i)+" of Friesland/C=FR/"
        dsc_private_key = ec.generate_private_key(ec.SECP256R1(), default_backend())
        dsc_public_key = dsc_private_key.public_key()
        dsca_cert=gen_certificate(dsc_name,csca_name,dsc_public_key,csca_private_key,1780)
        masterlist+=(dsca_cert.public_bytes(serialization.Encoding.PEM))
        if i=="worker":
            with open("dsc-worker.key", "wb") as f:
                f.write(dsc_private_key.private_bytes(encoding=serialization.Encoding.PEM,format=serialization.PrivateFormat.PKCS8,encryption_algorithm=serialization.NoEncryption()))
            with open("dsc-worker.pem", "wb") as f:
                f.write(dsca_cert.public_bytes(serialization.Encoding.PEM))
    with open("masterlist-dsc.pem", "wb") as f:
        f.write(masterlist)

make_CSCA_DSC()
