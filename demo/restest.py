# inspect für debug in der server konsole
# IO um generiertes Bild nur im Arbeitsspeicher zu halten
import datetime
# json import um dateien zu lesen
import json
import zlib
from sys import getsizeof

import cbor2
# QRcode generieren
# requests um auf das offizielle Backend live zurückzugreifen
# Eingabefelder und erstellung des payloads
# Pillow für Bild-Upload
from base45 import b45encode
# config
from cose.algorithms import Es256
from cose.headers import Algorithm, KID
from cose.keys import CoseKey
from cose.keys.curves import P256
from cose.keys.keyparam import KpKty, KpAlg, EC2KpD, EC2KpCurve
from cose.keys.keytype import KtyEC2
from cose.messages import Sign1Message
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import ec

# Flask-Json für json darstellung im browser
from server.keys_and_signscript.gen_csca_dsc import gen_certificate

payload_dict = (
    '{"1": "DE", "4": 1713213411, "6": 1697661411, "-260": {"1": {"dob": "2023-10-18", "nam": {"fn": "Mustermann", "fnt": "MUSTERMANN", "gn": "Max", "gnt": "MAX"}, "v": [{"ci": "32218895206968604", "co": "DE", "dn": 1, "dt": "2023-10-18", "is": "Robert Koch-Institut", "ma": "Bharat-Biotech", "mp": "EU/1/20/1507", "sd": 1, "tg": "840539006", "vp": "1119305005"}], "ver": "1.3.3.7"}}}'
)


def gen_private_key():
    return ec.generate_private_key(ec.SECP256R1())


def remove_pem_header(pem):
    return "".join(pem.decode("ascii").splitlines()[1:-1])


def minimise_key(private_key):  # takes private key and
    private_value = private_key.private_numbers().private_value
    public_key = private_key.public_key()
    public_key_pem = public_key.public_bytes(serialization.Encoding.PEM,
                                             serialization.PublicFormat.SubjectPublicKeyInfo)
    # print("=====")
    # print(public_key_pem)
    public_key_pem_headless = remove_pem_header(public_key_pem).encode()
    return private_value, public_key_pem_headless, public_key_pem


def rebuild_private_key(private_value, public_key_pem_headless):
    public_key_pem = (
            "-----BEGIN PUBLIC KEY-----\n" + public_key_pem_headless.decode() + "\n-----END PUBLIC KEY-----\n").encode(
        "ascii")
    public_key = serialization.load_pem_public_key(public_key_pem)
    private_numbers = ec.EllipticCurvePrivateNumbers(int(private_value), public_key.public_numbers())
    private_key = private_numbers.private_key()
    return private_key


def headless_pem_from_private_key(private_key):
    pem = private_key.private_bytes(encoding=serialization.Encoding.PEM,
                                    format=serialization.PrivateFormat.PKCS8,
                                    encryption_algorithm=serialization.NoEncryption())
    headless_pem = remove_pem_header(pem).encode()
    return headless_pem, pem


def compare_sizes():
    private_key = gen_private_key()
    private_key_pem_headless, private_key_pem = headless_pem_from_private_key(private_key)
    # key size comparison
    print("private key size " + str(getsizeof(private_key_pem)))
    print("private key size headless " + str(getsizeof(private_key_pem_headless)))
    private_value, public_key_pem_headless, public_key_pem = minimise_key(private_key)
    print("public key size  " + str(getsizeof(public_key_pem)))
    print("minimised key size " + str(getsizeof(private_value) + getsizeof(public_key_pem_headless)))
    # minimised keys aline
    print("===minimised keys alone===")
    print("minimised public key size " + str(getsizeof(public_key_pem_headless)))
    print("minimised private val size " + str(getsizeof(str(private_value).encode())))
    # compression
    print("===compression===")
    private_key_pem_headless_compressed = zlib.compress(private_key_pem_headless, 9)
    print("private key size compressed " + str(getsizeof(private_key_pem_headless_compressed)))
    print("")
    print("priv val " + str(getsizeof(private_value)))
    print(private_value.bit_length())
    import math
    number_of_bytes = int(math.ceil(private_value.bit_length() / 8))
    s = private_value.to_bytes(number_of_bytes, byteorder="big")
    g = int.from_bytes(s, byteorder='big')
    print(b45encode(s).decode().encode('ascii'))
    print(getsizeof(b45encode(s).decode().encode('ascii')))
    print("priv val converted " + str(getsizeof(s)))
    private_value_compressed = zlib.compress(s, 9)
    print("priv val converted compressed " + str(getsizeof(private_value_compressed)))
    public_key_pem_headless_compressed = zlib.compress(public_key_pem_headless, 9)
    print("minimised key size compressed " + str(
        getsizeof(private_value_compressed) + getsizeof(public_key_pem_headless_compressed)))
    # minimised comopressed keys alone
    print("===minimised keys compressed alone===")
    print("minimised public key size " + str(getsizeof(public_key_pem_headless_compressed)))
    print("minimised private val size " + str(getsizeof(private_value_compressed)))
    # note public key does not benefit from compression, pem seems decently compressed already
    # b45encoding adds 30% to size of private value but might support older devices better


def sign2(payload, public_key_headless, dsc_key):
    # load payload to dictionary
    payload = json.loads(payload)
    # add claims
    co = "DE"
    payload = {
        1: co,
        2: int(datetime.datetime.now().timestamp() + 180 * 24 * 3600),
        3: int(datetime.datetime.today().timestamp()),
        4: {
            1: payload,
        },
        5: public_key_headless
    }
    # convert to byte
    payload = cbor2.dumps(payload)
    cert = gen_certificate("dsc", "dsc", dsc_key.public_key(), dsc_key, 365)

    # cert = x509.load_pem_x509_certificate(dsc_pem)
    fingerprint = cert.fingerprint(hashes.SHA256())
    keyid = fingerprint[0:8]

    priv = dsc_key.private_numbers().private_value.to_bytes(32, byteorder="big")

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
    # windows only
    # if platform == "win32" : #bei fehlern auf linux auch die windows version benutzen
    out = b'HC1:' + b45encode(out).decode().encode('ascii')
    # linux version für base45 version < 0.4.4
    # else:
    #   out = b'HC1:' + bytes(b45encode(out),"utf8").decode().encode('ASCII')
    return out


def user_pk_and_cert():
    csca_name = 'CN=National CSCA of Friesland/C=FR/'
    user_name = "user"
    user_privatek = ec.generate_private_key(ec.SECP256R1())
    user_privatek_pem = user_privatek.private_bytes(encoding=serialization.Encoding.PEM,
                                                    format=serialization.PrivateFormat.PKCS8,
                                                    encryption_algorithm=serialization.NoEncryption())
    user_publick = user_privatek.public_key()
    ds_private_key = ec.generate_private_key(ec.SECP256R1())
    user_cert = gen_certificate(user_name, csca_name, user_publick, ds_private_key, 3650)
    user_cert_pem = user_cert.public_bytes(serialization.Encoding.PEM)
    user_publick_pem = user_publick.public_bytes(serialization.Encoding.PEM,
                                                 serialization.PublicFormat.SubjectPublicKeyInfo)
    return user_privatek_pem, user_cert_pem, user_publick_pem, ds_private_key


def user_pk_cert_test():
    user_privatek_pem, user_cert_pem, user_publick_pem, ds_privatekey = user_pk_and_cert()
    print(getsizeof(user_privatek_pem))
    print(getsizeof(user_cert_pem))
    print(getsizeof(user_publick_pem))
    user_privatek_pem_headless = remove_pem_header(user_privatek_pem).encode()
    user_cert_pem_headless = remove_pem_header(user_cert_pem).encode()
    user_publick_pem_headless = remove_pem_header(user_publick_pem)
    print(" ")
    print(getsizeof(user_privatek_pem_headless))
    print(getsizeof(user_cert_pem_headless))
    sign = sign2(payload_dict, user_publick_pem_headless, ds_privatekey)
    print("")
    print(getsizeof(sign))


compare_sizes()
#user_pk_cert_test()
