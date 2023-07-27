#!/usr/bin/env python
# IO um generiertes Bild nur im Arbeitsspeicher zu halten
import io
# QRcode generieren
import qrcode
# Pillow für Bild-Upload
from flask import render_template, send_file
# Eingabefelder und erstellung des payloads
from Formclasses import makeforms, makepayload
# signierfunktion aus eigenem skript
from keys_and_signscript.hc1_sign import sign
from flask import Blueprint

cert_creation_blueprint = Blueprint('cert_creation_blueprint', __name__)


# QR-Image generation
def generate_qrimage(cert_string: str):
    # generate matplotlib image
    image = qrcode.make(cert_string, error_correction=qrcode.constants.ERROR_CORRECT_Q)

    # create PNG image in memory
    img = io.BytesIO()  # create file-like object in memory to save image without using disk
    image.save(img, format='png')  # save image in file-like object
    img.seek(0)  # move to beginning of file-like object to read it later

    return img


# Seite zum Erstellen von Zertifikaten
@cert_creation_blueprint.route('/create_digital_hcert', methods=["GET", "POST"])
def create_digital_hcert():
    formlist = makeforms()
    # bei Abschicken des Formulares
    if formlist[1].validate_on_submit():
        # daten abgreifen
        payload = makepayload(formlist)
        # zum qr bild machen
        img = generate_qrimage(sign(payload))
        return send_file(img, 'file.png', as_attachment=True,
                         download_name=f'HCERT_{formlist[2].nachname.data}_{formlist[1].vorname.data}_{formlist[0].dob.data}.png')
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
