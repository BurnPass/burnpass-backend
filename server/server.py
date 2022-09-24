#!/usr/bin/env python
from flask import Flask, render_template, send_file, request
from flask_wtf import FlaskForm
from wtforms.fields import DateField
from wtforms import StringField, SubmitField, TextAreaField, SelectField, IntegerField
from wtforms.validators import DataRequired, NumberRange
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
from datetime import date
from trans import trans

app = Flask(__name__)
#config für json
json_app = FlaskJSON(app)
app.config['JSON_AS_ASCII'] = False
app.config['JSONIFY_PRETTYPRINT_REGULAR'] = True


choicelist_vaccines=[('EU/1/20/1507','Spikevax')
,('EU/1/20/1525','Jcovden')
,('EU/1/20/1528','Comirnaty')
,('EU/1/21/1529','Vaxzevria')
,('EU/1/21/1618','Nuvaxovid')
,('AZD2816','AZD2816')
,('Abdala','Abdala')
,('BBIBP-CorV','BBIBP-CorV')
,('CVnCoV','CVnCoV')
,('Convidecia','Convidecia')
,('CoronaVac','CoronaVac')
,('Covaxin','Covaxin')
,('CoviVac','CoviVac')
,('Covid-19-adsorvida-inativada','Vacina adsorvida covid-19 (inativada)')
,('Covid-19-recombinant','Covid-19 (recombinant)')
,('Covifenz','Covifenz')
,('Covishield','Covishield')
,('Covovax','Covovax')
,('EpiVacCorona','EpiVacCorona')
,('EpiVacCorona-N','EpiVacCorona-N')
,('Hayat-Vax','Hayat-Vax')
,('Inactivated-SARS-CoV-2-Vero-Cell','Inactivated SARS-CoV-2 (Vero Cell) (deprecated)')
,('MVC-COV1901','MVC COVID-19 vaccine')
,('NVSI-06-08','NVSI-06-08')
,('NVX-CoV2373','NVX-CoV2373 (deprecated)')
,('R-COVI','R-COVI')
,('SCTV01C','SCTV01C')
,('Soberana-02','Soberana 02')
,('Soberana-Plus','Soberana Plus')
,('Sputnik-Light','Sputnik Light')
,('Sputnik-M','Sputnik M')
,('Sputnik-V','Sputnik-V')
,('VLA2001','VLA2001')
,('Vidprevtyn','Vidprevtyn')
,('WIBP-CorV','WIBP-CorV')
,('YS-SC2-010','YS-SC2-010')]
choicelist_vaccine_types=[("1119305005","SARS-CoV-2 antigen vaccine"),("1119349007","SARS-CoV-2 mRNA vaccine"),("1157024006","Inactivated whole SARS-CoV-2 antigen vaccine"),("1162643001","SARS-CoV-2 recombinant spike protein antigen vaccine"),("29061000087103",	"COVID-19 non-replicating viral vector vaccine"),("J07BX03","covid-19 vaccines")]
choicelist_vaccine_auth_holder=[('Bharat-Biotech','Bharat Biotech'),
('CIGB','Center for Genetic Engineering and Biotechnology'),
('Chumakov-Federal-Scientific-Center','Chumakov Federal Scientific Center for Research and Development of Immune-and-Biological Products'),
('Finlay-Institute','Finlay Institute of Vaccines'),
('Fiocruz','Fiocruz'),
('Gamaleya-Research-Institute','Gamaleya Research Institute'),
('Instituto-Butantan','Instituto Butantan'),
('NVSI','National Vaccine and Serum Institute, China'),
('ORG-100000788','Sanofi Pasteur'),
('ORG-100001417','Janssen-Cilag International'),
('ORG-100001699','AstraZeneca AB'),
('ORG-100001981','Serum Institute Of India Private Limited'),
('ORG-100006270','Curevac AG'),
('ORG-100007893','R-Pharm CJSC'),
('ORG-100008549','Medicago Inc.'),
('ORG-100010771','Sinopharm Weiqida Europe Pharmaceutical s.r.o. - Prague location'),
('ORG-100013793','CanSino Biologics'),
('ORG-100020693','China Sinopharm International Corp. - Beijing location'),
('ORG-100023050','Gulf Pharmaceutical Industries'),
('ORG-100024420','Sinopharm Zhijun (Shenzhen) Pharmaceutical Co. Ltd. - Shenzhen location'),
('ORG-100026614','Sinocelltech Ltd.'),
('ORG-100030215','Biontech Manufacturing GmbH'),
('ORG-100031184','Moderna Biotech Spain S.L.'),
('ORG-100032020','Novavax CZ a.s.'),
('ORG-100033914','Medigen Vaccine Biologics Corporation'),
('ORG-100036422','Valneva France'),
('Sinopharm-WIBP','Sinopharm - Wuhan Institute of Biological Products'),
('Sinovac-Biotech','Sinovac Biotech'),
('Vector-Institute','Vector Institute'),
('Yisheng-Biopharma','Yisheng Biopharma')]

local_url="http://localhost:8000/trustList/DSC/"
public_url="https://verifier-api.coronacheck.nl/v4/verifier/public_keys"
public_url_app="https://de.dscg.ubirch.com/trustList/DSC"
test_url="http://scahry.ddns.net:8000/trustList/DSC/"
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

#Zertifikat Input Forms
class VornameForm(FlaskForm,):
    vorname = StringField("Vornamen",validators=[DataRequired()],default="Max")
    submit = SubmitField("Zertifikat erstellen")

class NachnameForm(FlaskForm,):
    nachname = StringField("Nachname",validators=[DataRequired()],default="Mustermann")

class DateOfBirthForm(FlaskForm):
    dob = DateField('Geburtsdatum',default=date.today)

class vaccinationDateForm(FlaskForm):
    vdate = DateField('Tag der Impfung',default=date.today)
    
class LandwahlForm(FlaskForm):
    land = SelectField("Ausstellungsland", choices=[("DE","Deutschland"),("GB","Großbritannien")],validators = [DataRequired()])

class diseaseAgentTargetedForm(FlaskForm):
    dAT = SelectField("Krankheit oder Krankheitserreger", choices=[("840539006","COVID-19")],validators = [DataRequired()])

class ImpfstoffTypForm(FlaskForm):
    vp = SelectField("Impfstoff Typ", choices=choicelist_vaccine_types,validators = [DataRequired()])

class ImpfstoffNameForm(FlaskForm):
    mp = SelectField("Impfstoff Produkt", choices=choicelist_vaccines,validators = [DataRequired()])

class ImpfstoffHerstellerForm(FlaskForm):
    ma = SelectField("Impfstoff Hersteller", choices=choicelist_vaccine_auth_holder,validators = [DataRequired()])

class DNIntForm(FlaskForm):
    number = IntegerField("Anzahl der vorgesehenen Impfungen in der Serie",default=1,validators = [DataRequired(),NumberRange(min=1)])

class SDIntForm(FlaskForm):
    number = IntegerField("Zahl der Impfung in der Serie",default=1,validators = [DataRequired(),NumberRange(min=1)])

class AusstellerForm(FlaskForm,):
    aussteller = StringField("Zertifikatsausteller",validators=[DataRequired()],default="Robert Koch-Institut")
    
#payload ersteller aus den Daten
def make_payload_and_delete(formlist):
    #siehe: Technical Specifications for EU Digital COVID Certificates JSON Schema Specification
    dob=str(formlist[0].dob.data)
    formlist[0].dob.data=None
    gn=str(formlist[1].vorname.data)
    formlist[1].vorname.data=None
    fn=str(formlist[2].nachname.data)
    formlist[2].nachname.data=None
    co=str(formlist[3].land.data)
    formlist[3].land.data=None
    tg=str(formlist[4].dAT.data)
    formlist[4].dAT.data=None
    vp=str(formlist[5].vp.data)
    formlist[5].vp.data=None
    mp=str(formlist[6].mp.data)
    formlist[6].mp.data=None
    ma=str(formlist[7].ma.data)
    formlist[7].ma.data=None
    dn=(formlist[8].number.data)
    formlist[8].number.data=None
    sd=(formlist[9].number.data)
    formlist[9].number.data=None
    dt=str(formlist[10].vdate.data)
    formlist[10].vdate.data=None
    is_=str(formlist[11].aussteller.data)#"is" ist ein keyword und kann nicht verwendet werden
    formlist[11].aussteller.data=None
    ci=str(randint(10000000000000000,99999999999999999))
    payload_dict={
    "dob": dob,
        "nam": {
            "fn": fn,
            "fnt": trans(fn,"slug").upper().replace("_","<"),
            "gn": gn,
            "gnt": trans(gn,"slug").upper().replace("_","<")
        },
        "v": [
            {
                "ci": ci,
                "co": co,
                "dn": dn,
                "dt": dt,
                "is": is_,
                "ma": ma,
                "mp": mp,
                "sd": sd,
                "tg": tg,
                "vp": vp
            }
        ],
        "ver": "1.3.3.7"
    }
    return str(payload_dict).replace("'",'"')

#Seite zum Erstellen von Zertifikaten
@app.route('/create_digital_hcert',methods=["GET","POST"])
def create_digital_hcert():
    #Je ein Formulareintrag pro variable
    vnameform = VornameForm()
    nnameform = NachnameForm()
    dobform = DateOfBirthForm()
    landform = LandwahlForm()
    dATform = diseaseAgentTargetedForm()
    impftypform = ImpfstoffTypForm()
    impfnameform = ImpfstoffNameForm()
    impfhersteller = ImpfstoffHerstellerForm()
    dnform = DNIntForm()
    sdform = SDIntForm()
    dtform = vaccinationDateForm()
    isform = AusstellerForm()
    
    #liste aller formulareinträge
    formlist=[dobform,vnameform,nnameform,landform,dATform,impftypform,impfnameform,impfhersteller,dnform,sdform,dtform,isform]
    #bei abschicken des Formulares
    if vnameform.validate_on_submit():
        #daten abgreifen
        returnstring = make_payload_and_delete(formlist)
        img = generate_qrimage(sign(returnstring))
        return send_file(img, 'file.png', as_attachment=True, download_name='HCERT'+str(randint(10000,99999)))
        #return "SUCCESS: \n" + str(sign(str(inputdata)))
    return render_template("hcert_creation.html",
                           vnameform = vnameform,
                           nnameform = nnameform,
                           dobform=dobform,
                           landform=landform,
                           dATform = dATform,
                           impftypform = impftypform,
                           impfnameform = impfnameform,
                           impfhersteller = impfhersteller,
                           dnform = dnform,
                           sdform = sdform,
                           dtform = dtform,
                           isform = isform)

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

