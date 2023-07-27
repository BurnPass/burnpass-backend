#!/usr/bin/env python
# Flask imports für User Interface
# IO um generiertes Bild nur im Arbeitsspeicher zu halten
import io

# QRcode generieren
import qrcode
# Pillow für Bild-Upload
from PIL import Image
from flask import Flask, render_template, send_file, request
from flask_bootstrap import Bootstrap
# Flask-Json für json darstellung im browser
from flask_json import FlaskJSON
# QRcode lesen
from pyzbar.pyzbar import decode

# Eingabefelder und erstellung des payloads
from Formclasses import makeforms, makepayload
from app_valuesets_blueprints import app_valuesets_blueprint
# config
from config import *
# signierfunktion aus eigenem skript
from keys_and_signscript.hc1_sign import sign
from keys_and_signscript.hc1_verify import verify
# zertifikat mit existierenden publickeys erstellen und in die datenbank einfügen
from keys_and_signscript.make_cert import make_cert, cert_to_db

# Erstelle die Public Key Zertifikat Datenbank aus den aktuellen Keys
# fehlen die Keys wird darauf aufmerksam
try:
    cert_to_db(make_cert("keys_and_signscript"), "keys_and_signscript")
except:
    print(" ! Please first generate Keys in the keys_and_signscript folder with gen_csca_dsc.py script ! ")
    exit(-1)

app = Flask(__name__)
Bootstrap(app)
# config für json
json_app = FlaskJSON(app)
app.config['JSON_AS_ASCII'] = False
app.config['JSONIFY_PRETTYPRINT_REGULAR'] = True


# QR-Image generation
def generate_qrimage(cert_string: str):
    # genereate matplotlib image
    image = qrcode.make(cert_string, error_correction=qrcode.constants.ERROR_CORRECT_Q)

    # create PNG image in memory
    img = io.BytesIO()  # create file-like object in memory to save image without using disk
    image.save(img, format='png')  # save image in file-like object
    img.seek(0)  # move to beginning of file-like object to read it later

    return img


# CSRF Token
app.config["SECRET_KEY"] = "2bMYYLmd-EvD1PsDm-cssKJp3p-ZK8exToo-1WMVEewm-`uBrMvMY-Kr\a4t3I-FD6mTVbZ-oxY5uBTA"


# Seite zum Erstellen von Zertifikaten
@app.route('/create_digital_hcert', methods=["GET", "POST"])
def create_digital_hcert():
    formlist = makeforms()
    # bei abschicken des Formulares
    if formlist[1].validate_on_submit():
        # daten abgreifen
        returnstring = makepayload(formlist)
        # zum qr bild machen
        img = generate_qrimage(sign(returnstring))
        return send_file(img, 'file.png', as_attachment=True,
                         download_name=f'HCERT_{formlist[2].nachname.data}_{formlist[1].vorname.data}_{formlist[0].dob.data}.png')
        # return "SUCCESS: \n" + str(sign(str(inputdata)))
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


# Index
@app.route('/')
def index():
    return render_template("index.html")


# verfication of hcert by image with qr
@app.route('/verifyqr')
def form():
    return render_template('verifyqr.html')


@app.route('/upload', methods=['POST', 'GET'])
def upload():
    if request.method == 'POST':
        f = request.files['file']
        image = Image.open(f)
        data = decode(image)
        if len(data) == 0:
            return "No QR detected"
        else:
            # falls ein QR-Code gefunden wurde, prüfe diesen
            payload = data[0].data
            valid = verify(payload, verify_url)
            return valid
    else:
        return "No image selected"


# trustlist, rules, valuesets
app.register_blueprint(app_valuesets_blueprint)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8000, debug=True)
