#!/usr/bin/env python
from flask import Flask, render_template, send_file, request
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, TextAreaField
from wtforms.validators import DataRequired
from wtforms.widgets import TextArea
import json
from keys_and_signscript.hc1_sign import sign
from hc1_verify import verify
import io
import qrcode
from pyzbar.pyzbar import decode
from PIL import Image
from random import randint
import requests
import inspect, sys
from flask_json import FlaskJSON, as_json

app = Flask(__name__)
#config für json
json_app = FlaskJSON(app)
app.config['JSON_AS_ASCII'] = False
app.config['JSONIFY_PRETTYPRINT_REGULAR'] = True

example="""{
    "dob": "1990-05-05",
    "nam": {
        "fn": "Mustermann",
        "fnt": "MUSTERMANN",
        "gn": "Max",
        "gnt": "MAX"
    },
    "v": [
        {
            "ci": "dieser_string_ist_unique_123",
            "co": "DE",
            "dn": 3,
            "dt": "2000-01-01",
            "is": "Robert Koch-Institut",
            "ma": "ORG-100030215",
            "mp": "EU/1/20/1528",
            "sd": 3,
            "tg": "840539006",
            "vp": "1119349007"
        }
    ],
    "ver": "1.3.3.7"
}"""

local_url="http://localhost:8000/trustList/DSC/"
public_url="https://verifier-api.coronacheck.nl/v4/verifier/public_keys"
public_url_app="https://de.dscg.ubirch.com/trustList/DSC"
test_url="http://192.168.178.23:8000/trustList/DSC/"
#QR-Image generation
def generate_qrimage(cert_string: str):
    # genereate matplotlib image
    image = qrcode.make(cert_string,error_correction=qrcode.constants.ERROR_CORRECT_Q)

    # create PNG image in memory
    img = io.BytesIO()              # create file-like object in memory to save image without using disk
    image.save(img, format='png')  # save image in file-like object
    img.seek(0)                     # move to beginning of file-like object to read it later

    return img

#CSRF Token
app.config["SECRET_KEY"] = "2bMYYLmd-EvD1PsDm-cssKJp3p-ZK8exToo-1WMVEewm-`uBrMvMY-Kr\a4t3I-FD6mTVbZ-oxY5uBTA"

#Zertifikat Input Form
class ZertForm(FlaskForm):
    inputdata = TextAreaField("Payload",validators=[DataRequired()],widget=TextArea())
    submit = SubmitField("Zertifikat erstellen")



#Seite zum Erstellen von Zertifikaten
@app.route('/create_digital_hcert',methods=["GET","POST"])
def create_digital_hcert():
    inputdata = None
    form = ZertForm(inputdata=example)
    if form.validate_on_submit():
        inputdata = form.inputdata.data
        form.inputdata.data=None
        img = generate_qrimage(sign(str(inputdata)))
        return send_file(img, 'file.png', as_attachment=True, download_name='HCERT'+str(randint(10000,99999)))
        #return "SUCCESS: \n" + str(sign(str(inputdata)))
    return render_template("hcert_creation.html",
                           inputdata=inputdata,
                           form = form)


#DSA Key bereitstellung
@app.route("/dsa_keys")
def dsa_keys():
    with open("keys_and_signscript/db.json", "rb") as file:
        dsa_keys = file.read()
    dsa_json=json.loads(dsa_keys)
    return dsa_json



#Index
@app.route('/')
def index():
    return render_template("index.html")

#verfication of hcert by image with qr
@app.route('/verifyqr')
def form():
    return render_template('verifyqr.html')

@app.route('/upload', methods = ['POST', 'GET'])
def upload():
    if request.method == 'POST':
        f = request.files['file']
        image = Image.open(f)
        data = decode(image)
        if len(data)==0:
            return "No QR detected"
        else:
            payload=(data[0].data)
            valid = verify(payload,test_url)
            return valid
    else:
        return "No image selected"
#======bereitstellung für App
#übernehme einfach die echten urls
    
#trustlist
localcert=True
@app.route("/trustList/DSC/")
#@as_json
def dsa_keys_app():
    print("queried", inspect.stack()[0][3])
    if localcert:
        with open("keys_and_signscript/db.json", "r") as file:
            dsa_keys = file.read()
        return dsa_keys
    else:
        url="https://de.dscg.ubirch.com/trustList/DSC"
        try:
            response = requests.get(url)
            trustlist = response.content
            return trustlist
        except:
            return "not valid or failed"

#bnrules
@app.route("/bnrules")
@as_json
def bnrules_app():
    print("queried", inspect.stack()[0][3])
    url = "https://distribution.dcc-rules.de/bnrules"
    try:
        response = requests.get(url)
        bnrules = response.json()
        return bnrules
    except:
        return "not valid or failed"

@app.route("/bnrules/<string:bnhash>")
@as_json
def bnrules_app_hashes(bnhash):
    print("queried", inspect.stack()[0][3], bnhash)
    url = "https://distribution.dcc-rules.de/bnrules/"+bnhash
    try:
        response = requests.get(url)
        bnrules = response.json()
        return bnrules
    except:
        return "not valid or failed"


#valuests
@app.route('/valuesets')
@as_json
def valuesets():
    print("queried", inspect.stack()[0][3])
    url = "https://distribution.dcc-rules.de/valuesets"
    try:
        response = requests.get(url)
        valuesets = response.json()
        return valuesets
    except:
        return "not valid or failed"

    
@app.route('/valuesets/<string:valuesethash>')
@as_json
def valuesetshash(valuesethash):
    print("queried", inspect.stack()[0][3], valuesethash)
    url = "https://distribution.dcc-rules.de/valuesets/"+valuesethash
    try:
        response = requests.get(url)
        valuesets = response.json()
        return valuesets
    except:
        return "not valid or failed"
    
#rules
@app.route('/rules')
@as_json
def rules():
    print("queried", inspect.stack()[0][3])
    url = "https://distribution.dcc-rules.de/rules"
    try:
        response = requests.get(url)
        rules = response.json()
        return rules
    except:
        return "not valid or failed"

    
@app.route('/rules/<string:rules_country>/<string:rules_sub_hash>')
@as_json
def rules_suburl(rules_country,rules_sub_hash):
    print("queried", inspect.stack()[0][3],rules_country,rules_sub_hash)
    url = "https://distribution.dcc-rules.de/rules/"+rules_country+"/"+rules_sub_hash
    try:
        response = requests.get(url)
        rules = response.json()
        return rules
    except:
        return "not valid or failed"

#country list
@app.route('/countrylist')
@as_json
def countrylist():
    print("queried", inspect.stack()[0][3])
    url = "https://distribution.dcc-rules.de/countrylist"
    try:
        response = requests.get(url)
        countrylist = response.json()
        return countrylist
    except:
        return "not valid or failed"
    
#domestic rules
@app.route('/domesticrules')
@as_json
def domesticrules():
    print("queried", inspect.stack()[0][3])
    url = "https://distribution.dcc-rules.de/domesticrules"
    try:
        response = requests.get(url)
        domesticrules = response.json()
        return domesticrules
    except:
        return "not valid or failed"

@app.route('/domesticrules/<string:domestic_hash>')
@as_json
def domestic_suburl(domestic_hash):
    print("queried", inspect.stack()[0][3],domestic_hash)
    url = "https://distribution.dcc-rules.de/domesticrules/"+domestic_hash
    try:
        response = requests.get(url)
        domesticrules = response.json()
        return domesticrules
    except:
        return "not valid or failed"
    
#kid list
@app.route('/kid.lst')
def kidlst():
    print("queried", inspect.stack()[0][3])
    try:
        url = "https://de.crl.dscg.ubirch.com/kid.lst"
        response = requests.get(url)
        kidlst = (response.content)
        return kidlst
    except:
        return "not valid or failed"

@app.route('/<string:indexhash>/index.lst')
def lstindex(indexhash):
    print("queried", inspect.stack()[0][3],indexhash)
    try:
        url = "https://de.crl.dscg.ubirch.com/"+indexhash+"/index.lst"
        response = requests.get(url)
        kidlst = (response.content)
        return kidlst
    except:
        return "not valid or failed"
#======ende bereitstellung für die app
    
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8000, debug=True)

