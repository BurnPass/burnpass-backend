#!/usr/bin/env python
# IO um generiertes Bild nur im Arbeitsspeicher zu halten
import io

import qrcode
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import ec
from flask import Blueprint
from flask import render_template, send_file

# Eingabefelder und erstellung des payloads
from Formclasses import makeforms, makepayload
# signierfunktion aus eigenem skript
from keys_and_signscript.hc1_sign import sign

cert_creation_blueprint = Blueprint('cert_creation_blueprint', __name__)


def seperate_key(private_key):  # seperates the private key into the public key and the private value
    private_value = str(private_key.private_numbers().private_value).encode()
    public_key = private_key.public_key()
    public_key_pem = public_key.public_bytes(serialization.Encoding.PEM,
                                             serialization.PublicFormat.SubjectPublicKeyInfo)
    public_key_pem_headless = ("".join(public_key_pem.decode("ascii").splitlines()[1:-1]))
    return private_value, public_key_pem_headless


def add_user_cert_an_sign(payload_dict):
    # create user private key
    user_private_key = ec.generate_private_key(ec.SECP256R1())
    # seperate the key into its public and private component
    private_value, public_key_pem_headless = seperate_key(user_private_key)
    # add the user public key to the payload dict
    payload = str(payload_dict).replace("'", '"')
    # sign the payload
    cose = sign(payload,public_key_pem_headless)
    # add the private value after the cose message
    # PV = private value
    cose_and_private_value = b"PV:" + private_value + cose
    # when reading the QR-Code, the last first occurence of PV: can be looked for as well as the first occurence of BP:
    # Furthmore PV: is already base45
    return cose_and_private_value


# QR-Image generation
def generate_qrimage(cert_string):
    # generate matplotlib image
    image = qrcode.make(cert_string, error_correction=qrcode.constants.ERROR_CORRECT_Q)

    # create PNG image in memory
    img = io.BytesIO()  # create file-like object in memory to save image without using disk
    image.save(img, format='png')  # save image in file-like object
    img.seek(0)  # move to beginning of file-like object to read it later

    return img


# Seite zum Erstellen von Zertifikaten
@cert_creation_blueprint.route('/create_digital_bpcert', methods=["GET", "POST"])
def create_digital_bpcert():
    formlist = makeforms()
    # bei Abschicken des Formulares
    if formlist[1].validate_on_submit():
        # daten abgreifen
        payload_dict = makepayload(formlist)
        # user keys hinzufügen und signieren
        payload = add_user_cert_an_sign(payload_dict)
        # zum qr bild machen
        img = generate_qrimage(payload)
        return send_file(img, 'file.png', as_attachment=True,
                         download_name=f'BPCERT_{formlist[2].nachname.data}_{formlist[1].vorname.data}_{formlist[0].dob.data}.png')
    # Eingabemaske anzeigen
    return render_template("hcert_creation.html",
                           dobform=formlist[0],
                           vnameform=formlist[1],
                           nnameform=formlist[2],
                           landform=formlist[3],
                           dATform=formlist[4],
                           impftypform=formlist[5],
                           impfnameform=formlist[6],
                           impfhersteller=formlist[7],
                           dnform=formlist[8],
                           sdform=formlist[9],
                           dtform=formlist[10],
                           isform=formlist[11])
