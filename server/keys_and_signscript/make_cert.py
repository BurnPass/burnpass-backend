#!/usr/bin/env python
import datetime
from base64 import b64encode

from cryptography import x509
from cryptography.hazmat.primitives import hashes


def make_cert(folder):
    # zertifikat laden
    with open(folder + "/dsc-worker.pem", "r") as file:
        pemlines = file.readlines()
    with open(folder + "/dsc-worker.pem", "rb") as file:
        pem = file.read()
    # Zeilen der PEM datei ohne Kopf und Fuß und ohne Zeilenumbruch
    pemheadless = "".join([lines[:-1] for lines in pemlines[1:-1]])

    cert = x509.load_pem_x509_certificate(pem)

    fingerprint = cert.fingerprint(hashes.SHA256())
    keyid = fingerprint[0:8]
    keyid_ascii = (b64encode(keyid).decode('ascii'))
    dictentry = {'certificateType': 'DSC',
                 'country': 'CH',
                 'kid': keyid_ascii,
                 'rawData': pemheadless,
                 'signature': '',
                 'thumbprint': '',
                 'timestamp': datetime.datetime.now().astimezone().replace(microsecond=0).isoformat()}

    certs = {"certificates": [dictentry]}
    return str(certs).replace("'", '"')


def cert_to_db(cert, folder):
    with open(folder + "/db.json", "w") as file:
        file.write(cert)
