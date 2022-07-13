from flask import Flask, render_template
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField
from wtforms.validators import DataRequired
import json

app = Flask(__name__)

#CSRF Token
app.config["SECRET_KEY"] = "2bMYYLmd-EvD1PsDm-cssKJp3p-ZK8exToo-1WMVEewm-`uBrMvMY-Kr\a4t3I-FD6mTVbZ-oxY5uBTA"

#Zertifikat Input Form
class ZertForm(FlaskForm):
    inputdata = StringField("Paylaod",validators=[DataRequired()])
    submit = SubmitField("Zertifikat erstellen")


#DSA Key bereitstellung
@app.route("/dsa_keys")
def dsa_keys():
    with open("db.json", "rb") as file:
        dsa_keys = file.read()
    dsa_json=json.loads(dsa_keys)
    return dsa_json

#Seite zum Erstellen von Zertifikaten
@app.route('/create_digital_hcert',methods=["GET","POST"])
def create_digital_hcert():
    inputdata = None
    form = ZertForm()
    if form.validate_on_submit():
        inputdata = form.inputdata.data
        form.inputdata.data=None 
    return render_template("hcert_creation.html",
                           inputdata=inputdata,
                           form = form)

#Index
@app.route('/')
def index():
    return render_template("index.html")
    
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8000 ,debug=True)
