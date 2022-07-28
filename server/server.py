from flask import Flask, render_template, send_file
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, TextAreaField
from wtforms.validators import DataRequired
from wtforms.widgets import TextArea
import json
from keys_and_signscript.hc1_sign import sign
import io
import qrcode

app = Flask(__name__)
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
        return send_file(img, 'file.png')
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
    
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8000 ,debug=True)
