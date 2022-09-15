#!env python3

import json
import requests
import sys
import zlib
import re
from base64 import b64decode, b64encode
from datetime import date, datetime

import cbor2
from binascii import unhexlify, hexlify

from base45 import b45decode
from cose.algorithms import Es256
from cose.keys.curves import P256
from cose.algorithms import Es256, EdDSA, Ps256
from cose.headers import KID, Algorithm
from cose.keys import CoseKey
from cose.keys.keyparam import KpAlg, EC2KpX, EC2KpY, EC2KpCurve, RSAKpE, RSAKpN
from cose.keys.keyparam import KpKty
from cose.keys.keytype import KtyEC2, KtyRSA
from cose.messages import CoseMessage
from cryptography import x509
from cryptography.utils import int_to_bytes
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric.ec import EllipticCurvePublicKey
from cryptography.hazmat.primitives.asymmetric.rsa import RSAPublicKey
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import ec


def key_maker(pub):
        x=0
        if (isinstance(pub, RSAPublicKey)):
              x = CoseKey.from_dict(
               {   
                    KpKty: KtyRSA,
                    KpAlg: Ps256,  # RSSASSA-PSS-with-SHA-256-and-MFG1
                    RSAKpE: int_to_bytes(pub.public_numbers().e),
                    RSAKpN: int_to_bytes(pub.public_numbers().n)
               })
        elif (isinstance(pub, EllipticCurvePublicKey)):
              x = CoseKey.from_dict(
               {
                    KpKty: KtyEC2,
                    EC2KpCurve: P256,  # Ought o be pk.curve - but the two libs clash
                    KpAlg: Es256,  # ecdsa-with-SHA256
                    EC2KpX: pub.public_numbers().x.to_bytes(32, byteorder="big"),
                    EC2KpY: pub.public_numbers().y.to_bytes(32, byteorder="big")
               })
        else:
              print(f"Skipping unexpected/unknown key type (keyid={kid_b64}, {pub.__class__.__name__}).",  file=sys.stderr)

        return x

def json_serial(obj):
    """JSON serializer for objects not serializable by default json code"""

    if isinstance(obj, (datetime, date)):
        return obj.isoformat()
    raise TypeError ("Type %s not serializable" % type(obj))


def verify(cin, url):
        cin = cin.decode("ASCII")
        if cin.startswith('HC1'):
                cin = cin[3:]
        if cin.startswith(':'):
                cin = cin[1:]
        cin = b45decode(cin)

        if (cin[0] == 0x78):
                cin = zlib.decompress(cin)

        decoded = CoseMessage.decode(cin)

        kids = {}
        keyid = None
        key = None

        response = requests.get(url)
        response=str(response.content)
        i=(response.index("{"))
        ii=len(response)-(response[::-1].index("}"))
        pkg = json.loads(response[i:ii])
        certificates= pkg["certificates"]
        for c in certificates:
                kids[c["kid"]]=c["rawData"]


        given_kid = None
        if KID in decoded.phdr.keys():
           given_kid = decoded.phdr[KID]
        else:
           given_kid = decoded.uhdr[KID]
           
        given_kid_b64 = b64encode(given_kid).decode('ASCII')

        if given_kid_b64 in kids:
                x="-----BEGIN CERTIFICATE-----\n" +kids[given_kid_b64] + "\n"+"-----END CERTIFICATE-----"
                keyfile = x509.load_pem_x509_certificate(bytes(x,"utf-8"))
        if not given_kid_b64 in kids:
                return f"KeyID is unknown (kid={given_kid_b64}) -- cannot verify."
        key  = key_maker(keyfile.public_key())#kids[given_kid_b64]

        decoded.key = key
        if not decoded.verify_signature():
                return f"Signature invalid (kid={given_kid_b64})"

           
        payload = decoded.payload
        payload = cbor2.loads(payload)
        payload = payload[-260][1]
        payload = json.dumps(payload, indent=4, sort_keys=True, default=json_serial, ensure_ascii=False)
        
        return ("Signature valid with KID: "+str(given_kid_b64))
