#!env python3.8
import zlib
import json
import cbor2
from datetime import datetime
from base64 import b64encode, b64decode
from sys import platform


from base45 import b45encode
from cose.algorithms import Es256
from cose.keys.curves import P256
from cose.algorithms import Es256, EdDSA
from cose.keys.keyparam import KpKty, KpAlg, EC2KpD, EC2KpX, EC2KpY, EC2KpCurve
from cose.headers import Algorithm, KID
from cose.keys import CoseKey
from cose.keys.keyparam import KpAlg, EC2KpD, EC2KpCurve
from cose.keys.keyparam import KpKty
from cose.keys.keytype import KtyEC2
from cose.messages import Sign1Message
from cryptography import x509
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.serialization import load_pem_private_key


def sign(payload):
    #load payload to dictionary
    payload = json.loads(payload)
    #add claims
    payload = {
               1: "DE",
               4: int(datetime.now().timestamp() + 180 * 24 * 3600),
               6: int(datetime.today().timestamp()),
               -260: {
                    1: payload,
                },
         }
    #convert to byte
    payload = cbor2.dumps(payload)

    # Note - we only need the public key for the KeyID calculation - we're not actually using it.
    #
    with open("keys_and_signscript/dsc-worker.pem", "rb") as file:
        pem = file.read()
    cert = x509.load_pem_x509_certificate(pem)
    fingerprint = cert.fingerprint(hashes.SHA256())
    keyid = fingerprint[0:8]

    # Read in the private key that we use to actually sign this
    #
    with open("keys_and_signscript/dsc-worker.key", "rb") as file:
        pem = file.read()
    keyfile = load_pem_private_key(pem, password=None)
    priv = keyfile.private_numbers().private_value.to_bytes(32, byteorder="big")

    # Prepare a message to sign; specifying algorithm and keyid
    # that we (will) use
    #
    msg = Sign1Message(phdr={Algorithm: Es256, KID: keyid}, payload=payload)

    # Create the signing key - use ecdsa-with-SHA256
    # and NIST P256 / secp256r1
    #
    cose_key = {
        KpKty: KtyEC2,
        KpAlg: Es256,  # ecdsa-with-SHA256
        EC2KpCurve: P256,  # Ought to be pk.curve - but the two libs clash
        EC2KpD: priv,
    }

    # Encode the message (which includes signing)
    #
    msg.key = CoseKey.from_dict(cose_key)
    out = msg.encode()
    # Compress with ZLIB
    #
    out = zlib.compress(out, 9)
    # And base45 encode the result
    #
    #windows only
    if platform == "win32" :
        out = b'HC1:' + b45encode(out).decode().encode('ascii')
    #linux only - not tested on other platforms:
    else:
        out = b'HC1:' + bytes(b45encode(out),"utf8").decode().encode('ASCII')
    return out
