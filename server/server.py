#!/usr/bin/env python
# Pillow für Bild-Upload
# Flask imports für User Interface
# Flask-Json für json darstellung im browser
from PIL import Image
from flask import Flask, render_template, request
from flask_bootstrap import Bootstrap
from flask_json import FlaskJSON
from pyzbar.pyzbar import decode

# blueprints
from app_valuesets_blueprints import app_valuesets_blueprint
from cert_creation import cert_creation_blueprint
# config
from config import *
# signierfunktion aus eigenem skript
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
# CSRF Token
app.config["SECRET_KEY"] = "2bMYYLmd-EvD1PsDm-cssKJp3p-ZK8exToo-1WMVEewm-`uBrMvMY-Kr\a4t3I-FD6mTVbZ-oxY5uBTA"


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
# certificate creation
app.register_blueprint(cert_creation_blueprint)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8000, debug=True)
