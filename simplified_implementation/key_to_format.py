#!env python3

import json
from base64 import b64encode
from cryptography import x509
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives import hashes

#zertifikat laden
with open("dsc-worker.pem", "rb") as file:
    pem = file.read()
cert = x509.load_pem_x509_certificate(pem)
#serialisierung und b64 encoding
public_key=(cert.public_key().public_bytes(serialization.Encoding.DER,serialization.PublicFormat.SubjectPublicKeyInfo))
public_key_formatted=(str(b64encode(public_key).decode('ascii')))

#print(public_key_formatted)
#keyID holen und auch b64 encoden
fingerprint = cert.fingerprint(hashes.SHA256())
keyid = fingerprint[0:8]

keyid_ascii=(b64encode(keyid).decode('ascii'))

thiskeydict={
    keyid_ascii:[{"ian":"DE",
           "keyUsage":["v"],
           "san":"",
           "subjectPk":public_key_formatted}]}

keysdict={
    "eu_keys": thiskeydict
    }
bytedict=json.dumps(keysdict).encode("ascii")

signed={"signature":"none",
        "payload":b64encode(bytedict).decode("ascii")}
#postformat={"dsa_keys":signed}
print(json.dumps(signed))
