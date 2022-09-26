#!/usr/bin/env python
#Flask imports für User Interface
from flask import Flask, render_template, send_file, request
#json import um dateien zu lesen
import json
#signierfunktion aus eigenem skript
from keys_and_signscript.hc1_sign import sign
from keys_and_signscript.hc1_verify import verify
#IO um generiertes Bild nur im Arbeitsspeicher zu halten
import io
#QRcode generieren
import qrcode
#QRcode lesen
from pyzbar.pyzbar import decode
#Pillow für Bildgenerierung des QRcodes
from PIL import Image
#requests um auf das offizielle Backend live zurückzugreifen
import requests
#inspect für debug in der server konsole
import inspect
#Flask-Json für json darstellung im browser
from flask_json import FlaskJSON, as_json
#Eingabefelder und erstellung des payloads
from Formclasses import makeforms, makepayload
#randint für den Dateinamen
from random import randint
#zertifikat mit existierenden publickeys erstellen und in die datenbank einfügen
from keys_and_signscript.make_cert import make_cert,cert_to_db

localcert=True#ob auf die lokalen public keys oder die offiziellen zugegriffen werden soll
offlinemode=False#ist der offline mode an, wird auf eine offizielle version der offiziellen backends zurückgegriffen


#Erstelle die Public Key Zertifikat Datenbank aus den aktuellen Keys
#fehlen die Keys wird darauf aufmerksam
try:
    cert_to_db(make_cert("keys_and_signscript"),"keys_and_signscript")
except:
    print(" ! Please first generate Keys in the keys_and_signscript folder with gen-csca-dsc.sh script ! ")
    exit(-1)
    
app = Flask(__name__)
#config für json
json_app = FlaskJSON(app)
app.config['JSON_AS_ASCII'] = False
app.config['JSONIFY_PRETTYPRINT_REGULAR'] = True


local_url="http://localhost:8000/trustList/DSC/"
public_url="https://verifier-api.coronacheck.nl/v4/verifier/public_keys"
public_url_app="https://de.dscg.ubirch.com/trustList/DSC"
www_url="http://scahry.ddns.net:8000/trustList/DSC/"


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
    


#Seite zum Erstellen von Zertifikaten
@app.route('/create_digital_hcert',methods=["GET","POST"])
def create_digital_hcert():
    formlist=makeforms()
    #bei abschicken des Formulares
    if formlist[1].validate_on_submit():
        #daten abgreifen
        returnstring = makepayload(formlist)
        #zum qr bild machen
        img = generate_qrimage(sign(returnstring))
        return send_file(img, 'file.png', as_attachment=True, download_name='HCERT'+str(randint(10000,99999)))
        #return "SUCCESS: \n" + str(sign(str(inputdata)))
    #Eingabemaske anzeigen
    return render_template("hcert_creation.html",
                           dobform=formlist[0],
                           vnameform = formlist[1],
                           nnameform = formlist[2],
                           landform=formlist[3],
                           dATform = formlist[4],
                           impftypform = formlist[5],
                           impfnameform = formlist[6],
                           impfhersteller = formlist[7],
                           dnform = formlist[8],
                           sdform = formlist[9],
                           dtform = formlist[10],
                           isform = formlist[11])

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
            #falls ein QR-Code gefunden wurde, prüfe diesen
            payload=(data[0].data)
            valid = verify(payload,www_url)
            return valid
    else:
        return "No image selected"
    
#======bereitstellung für App
#übernehme einfach die echten urls, oder falls offline stelle eigene zur verfügung
    
#trustlist
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

