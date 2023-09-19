from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import ec

from certificate_util import gen_certificate


def make_csca_dsc():
    # CSCA certificate
    csca_name = 'CN=National CSCA of Friesland/C=FR/'
    csca_private_key = ec.generate_private_key(ec.SECP256R1())
    csca_public_key = csca_private_key.public_key()
    csca_cert = gen_certificate(csca_name, csca_name, csca_public_key, csca_private_key, 3650)
    csca_pem = csca_cert.public_bytes(serialization.Encoding.PEM)
    with open("csca.pem", "wb") as f:
        f.write(csca_pem)
    # DSC certificates
    masterlist = b""
    # 1 2 3 4 werden nur exemplarisch verwendet um eine masterlist anzulegen
    for i in [1, 2, 3, 4, "worker"]:
        dsc_name = "/CN=DSC " + str(i) + " of Friesland/C=FR/"
        dsc_private_key = ec.generate_private_key(ec.SECP256R1())
        dsca_cert = gen_certificate(dsc_name, csca_name, dsc_private_key.public_key(), csca_private_key, 1780)
        masterlist += (dsca_cert.public_bytes(serialization.Encoding.PEM))
        if i == "worker":
            with open("dsc-worker.key", "wb") as f:
                f.write(dsc_private_key.private_bytes(encoding=serialization.Encoding.PEM,
                                                      format=serialization.PrivateFormat.PKCS8,
                                                      encryption_algorithm=serialization.NoEncryption()))
            with open("dsc-worker.pem", "wb") as f:
                f.write(dsca_cert.public_bytes(serialization.Encoding.PEM))
    with open("masterlist-dsc.pem", "wb") as f:
        f.write(masterlist)


make_csca_dsc()
