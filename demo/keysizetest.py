# inspect für debug in der server konsole
# IO um generiertes Bild nur im Arbeitsspeicher zu halten
import io
# json import um dateien zu lesen
import json
import zlib
from datetime import datetime
from sys import getsizeof

import cbor2
# QRcode generieren
import qrcode
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
from cryptography.hazmat.primitives.serialization import load_pem_private_key

# Flask-Json für json darstellung im browser
from server.keys_and_signscript.gen_csca_dsc import *


def gen_private_key():
    return ec.generate_private_key(ec.SECP256R1())


def minimise_key(private_key):  # takes private key and
    private_value = str(private_key.private_numbers().private_value).encode()
    public_key = private_key.public_key()
    public_key_pem = public_key.public_bytes(serialization.Encoding.PEM,
                                             serialization.PublicFormat.SubjectPublicKeyInfo)
    print("=====")
    print(public_key_pem)
    public_key_pem_headless = ("".join(public_key_pem.decode("ascii").splitlines()[1:-1])).encode()
    return private_value, public_key_pem_headless


def rebuild_private_key(private_value, public_key_pem_headless):
    public_key_pem = (
            "-----BEGIN PUBLIC KEY-----\n" + public_key_pem_headless.decode() + "\n-----END PUBLIC KEY-----\n").encode(
        "ascii")
    public_key = serialization.load_pem_public_key(public_key_pem)
    private_numbers = ec.EllipticCurvePrivateNumbers(int(private_value), public_key.public_numbers())
    private_key = private_numbers.private_key()
    return private_key


def is_equal_key(key_a, key_b):
    pem_a = (key_a.private_bytes(encoding=serialization.Encoding.PEM,
                                 format=serialization.PrivateFormat.PKCS8,
                                 encryption_algorithm=serialization.NoEncryption()))
    pem_b = (key_b.private_bytes(encoding=serialization.Encoding.PEM,
                                 format=serialization.PrivateFormat.PKCS8,
                                 encryption_algorithm=serialization.NoEncryption()))
    return pem_a == pem_b


def headless_pem_from_private_key(private_key):
    pem = private_key.private_bytes(encoding=serialization.Encoding.PEM,
                                    format=serialization.PrivateFormat.PKCS8,
                                    encryption_algorithm=serialization.NoEncryption())
    headless_pem = ("".join(pem.decode("ascii").splitlines()[1:-1])).encode()
    return headless_pem


def compare_sizes():
    private_key = gen_private_key()
    private_key_pem_headless = headless_pem_from_private_key(private_key)
    # key size comparison
    print("private key size " + str(getsizeof(private_key_pem_headless)))
    private_value, public_key_pem_headless = minimise_key(private_key)
    print("minimised key size " + str(getsizeof(int(private_value)) + getsizeof(public_key_pem_headless)))
    # minimised keys aline
    print("===minimised keys alone===")
    print("minimised public key size " + str(getsizeof(public_key_pem_headless)))
    print("minimised private val size " + str(getsizeof(private_value)))
    # compression
    print("===compression===")
    private_key_pem_headless_compressed = zlib.compress(private_key_pem_headless, 9)
    print("private key size compressed " + str(getsizeof(private_key_pem_headless_compressed)))
    private_value_compressed = zlib.compress(private_value, 9)
    public_key_pem_headless_compressed = zlib.compress(public_key_pem_headless, 9)
    print("minimised key size compressed " + str(
        getsizeof(private_value_compressed) + getsizeof(public_key_pem_headless_compressed)))
    # minimised comopressed keys alone
    print("===minimised keys compressed alone===")
    print("minimised public key size " + str(getsizeof(public_key_pem_headless_compressed)))
    print("minimised private val size " + str(getsizeof(private_value_compressed)))
    # note public key does not benefit from compression, pem seems decently compressed already
    # b45encoding adds 30% to size of private value but might support older devices better


#####practical key size test######

def generate_qrimage(cert_string):
    # genereate matplotlib image
    image = qrcode.make(cert_string, error_correction=qrcode.constants.ERROR_CORRECT_Q)

    # create PNG image in memory
    img = io.BytesIO()  # create file-like object in memory to save image without using disk
    image.save(img, format='png')  # save image in file-like object
    img.seek(0)  # move to beginning of file-like object to read it later

    return img


def sign(payload, dsc_key):
    # load payload to dictionary
    payload = json.loads(payload)
    # add claims
    co = "DE"
    payload = {
        1: co,
        2: int(datetime.now().timestamp() + 180 * 24 * 3600),
        3: int(datetime.today().timestamp()),
        4: {
            1: payload,
        },
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


def test():
    private_key = gen_private_key()
    private_value, public_key_pem_headless = minimise_key(private_key)
    print(public_key_pem_headless)
    dsc_key = gen_private_key()
    payload = '{"user_public": "' + public_key_pem_headless.decode() + '"}'
    cose = sign(payload, dsc_key)
    cose_private_val = cose + b"_private_value:" + private_value
    cose_alt = cose + b"_private_value:" + b45encode(private_value).decode().encode('ascii')
    print(cose_private_val)
    print(cose_alt)
    img = generate_qrimage(cose_private_val)
    img_alt = generate_qrimage(cose_alt)
    print(getsizeof(cose_private_val))
    print(getsizeof(cose_alt))
    with open("qrtest.png", "wb") as f:
        f.write(img.read())
    with open("qrtest_alt.png", "wb") as f:
        f.write(img_alt.read())


def compare_tes():
    pem_kotlin = ("-----BEGIN PRIVATE KEY-----\n" +
                  "ME0CAQAwEwYHKoZIzj0CAQYIKoZIzj0DAQcEMzAxAgEBBCAkHTbb10xt5PW4acyO2DxT93xxgDuvLGYS69MbjqHDRqAKBggqhkjOPQMBBw==" +
                  "\n-----END PRIVATE KEY-----\n")
    pem_server = ("-----BEGIN PRIVATE KEY-----\n" +
                  "MIGHAgEAMBMGByqGSM49AgEGCCqGSM49AwEHBG0wawIBAQQgJB0229dMbeT1uGnM\njtg8U/d8cYA7ryxmEuvTG46hw0ahRANCAAQ9961ecxwB4y74+rNCFczbsEctIJ5g\nWLtKLnU7pBSNVzUx73ehShbKNPPLCSaswSGJ4bxUyadlgmhdk67ugUaf" +
                  "\n-----END PRIVATE KEY-----\n")
    kotlinkey = load_pem_private_key(pem_kotlin.encode(), password=None)
    serverkey = load_pem_private_key(pem_server.encode(), password=None)
    priv_num1 = (kotlinkey.private_numbers().private_value)
    priv_num2 = (serverkey.private_numbers().private_value)
    re_pem_kotlin = kotlinkey.private_bytes(encoding=serialization.Encoding.PEM,
                                            format=serialization.PrivateFormat.PKCS8,
                                            encryption_algorithm=serialization.NoEncryption())
    re_pem_server = serverkey.private_bytes(encoding=serialization.Encoding.PEM,
                                            format=serialization.PrivateFormat.PKCS8,
                                            encryption_algorithm=serialization.NoEncryption())
    # print(pem_kotlin)
    # print(pem_server)
    # print(re_pem_kotlin)
    # print(re_pem_server)
    print("priv value equal")
    print(priv_num1 == priv_num2)
    print("====compare curve====")
    print(kotlinkey.curve.name)
    print(kotlinkey.curve.key_size)
    print(serverkey.curve.name)
    print(serverkey.curve.key_size)
    print("====compare public key====")
    kotlin_public = kotlinkey.public_key()
    server_public = serverkey.public_key()
    print(kotlin_public.public_numbers().curve.name)
    print(server_public.public_numbers().curve.name)
    print(kotlin_public.public_numbers().curve.key_size)
    print(server_public.public_numbers().curve.key_size)
    print(kotlin_public.public_numbers().x)
    print(server_public.public_numbers().x)
    print(kotlin_public.public_numbers().x == server_public.public_numbers().x)
    print(kotlin_public.public_numbers().y)
    print(server_public.public_numbers().y)
    print(kotlin_public.public_numbers().y == server_public.public_numbers().y)
    print("===sign and verify test===")
    algo = ec.ECDSA(hashes.SHA256())
    signed = serverkey.sign("moin moin".encode(), algo)
    try:
        kotlin_public.verify(signed, "moin moin".encode(), algo)
        print("verified")
    except:
        print("failed")


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
    return user_privatek_pem, user_cert_pem


def test311():
    a, b = user_pk_and_cert()
    print(getsizeof(a))
    print(getsizeof(b))
    print(getsizeof(
        "HC1:6BFY70D90T9WJWG.FKY*4GO0B3O+*F X7%BSFBBL/0*70HS8FN08*CRL2WY0LSC:ESD97TK0F90KECTHGWJC0FD1M6AIA%G7X+AQB9746HS8$/5TW6746TW6I%6K/5TM8G:5T1B6H9 X8NX686A:6AJTAKIBSR6WM8TK4WJCT3EHS8XJC%+DXJCCWENF6OF64W5KF6.96%JC QE/IAYJC5LEW34U3ET7DXC9 QE-ED8%E.JCBECB1A-:8$966469L6OF6VX6Q$D.UDRYA 96NF6L/5SW6Y57KQEBJ09WEQDD+Q6TW6FA7C466KCN9E%961A6DL6FA7D46JPCT3E5JDOA7Q477465W5LB7..DX%DZJC0/DFOAF/D JC2/D1UAB$DVKELPCG/DXUCNB8HOAI3D8WEETAMY9.HA$PC5$CUZC$$5Y$527BF GKHQRX0K3L*QDYOCO+ADFVBQNLX7$3ED$6BR375C2GKMIU3:GCGB+%I9EU/IQ2LJTOG7NBEGJI13XB8%PE-VD.N19:DBOE/F5KFF"))


# test()
# compare_sizes()
# compare_tes()
test311()
