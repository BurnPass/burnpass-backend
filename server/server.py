#!/usr/bin/env python
#Flask imports für User Interface
from flask import Flask, render_template, send_file, request
from flask_bootstrap import Bootstrap
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
#Pillow für Bild-Upload
from PIL import Image
#requests um auf das offizielle Backend live zurückzugreifen
import requests
#inspect für debug in der server konsole
import inspect
#Flask-Json für json darstellung im browser
from flask_json import FlaskJSON, as_json
#Eingabefelder und erstellung des payloads
from Formclasses import makeforms, makepayload
#zertifikat mit existierenden publickeys erstellen und in die datenbank einfügen
from keys_and_signscript.make_cert import make_cert,cert_to_db
#config
from config import *
#Erstelle die Public Key Zertifikat Datenbank aus den aktuellen Keys
#fehlen die Keys wird darauf aufmerksam
try:
    cert_to_db(make_cert("keys_and_signscript"),"keys_and_signscript")
except:
    print(" ! Please first generate Keys in the keys_and_signscript folder with gen_csca_dsc.py script ! ")
    exit(-1)
    
app = Flask(__name__)
Bootstrap(app)
#config für json
json_app = FlaskJSON(app)
app.config['JSON_AS_ASCII'] = False
app.config['JSONIFY_PRETTYPRINT_REGULAR'] = True


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
        return send_file(img, 'file.png', as_attachment=True, download_name=f'HCERT_{formlist[2].nachname.data}_{formlist[1].vorname.data}_{formlist[0].dob.data}.png')
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
            valid = verify(payload,verify_url)
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
        if offlinemode:
            with open("offline_valuesets/_trustList_DSC_.txt", "r") as file:
                content = file.read()
            return content
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
    if offlinemode:
        with open("offline_valuesets/_bnrules.txt", "r",encoding="utf-8") as file:
            content = json.loads(file.read())
        return content
    else:
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
    if offlinemode:
        with open("offline_valuesets/_bnrules_"+bnhash+".txt", "r",encoding="utf-8") as file:
            content = json.loads(file.read())
        return content
    else:
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
    if offlinemode:
        with open("offline_valuesets/_valuesets.txt", "r",encoding="utf-8") as file:
            content = json.loads(file.read())
        return content
    else:
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
    if offlinemode:
        with open("offline_valuesets/_valuesets_"+valuesethash+".txt", "r",encoding="utf-8") as file:
            content = json.loads(file.read())
        return content
    else:    
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
    if offlinemode:
        with open("offline_valuesets/_rules.txt", "r",encoding="utf-8") as file:
            content = json.loads(file.read())
        return content
    else:    
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
    if offlinemode:
        with open("offline_valuesets/_rules_"+rules_country+"_"+rules_sub_hash+".txt", "r",encoding="utf-8") as file:
            content = json.loads(file.read())
        return content
    else:    
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
    if offlinemode:
        with open("offline_valuesets/_countrylist.txt", "r",encoding="utf-8") as file:
            content = json.loads(file.read())
        return content
    else:  
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
    if offlinemode:
        with open("offline_valuesets/_domesticrules.txt", "r",encoding="utf-8") as file:
            content = json.loads(file.read())
        return content
    else:  
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
    if offlinemode:
        with open("offline_valuesets/_domesticrules"+"_"+domestic_hash+".txt", "r",encoding="utf-8") as file:
            content = json.loads(file.read())
        return content
    else:  
        try:
            response = requests.get(url)
            domesticrules = response.json()
            return domesticrules
        except:
            return "not valid or failed"
    
#lst kid und index, wurde iwann mal abgefragt. aber nicht oft, kann also nicht so wichtig sein
#hat was mit der revocationlist zu tun
@app.route('/kid.lst')
def kidlst():
    print("queried", inspect.stack()[0][3])
    if offlinemode:
        with open("offline_valuesets/_kid.lst", "rb") as file:
            content = file.read()
        return (content)
    else:  
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
    if offlinemode:
        return "None"
    else:
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

