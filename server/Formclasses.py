#verschiedene imports für die verschiedenen eingabefelder
from flask_wtf import FlaskForm
from wtforms.fields import DateField
from wtforms import StringField, SubmitField, SelectField, IntegerField
from wtforms.validators import DataRequired, NumberRange
#transkription bei Namen für der Zertifikat. z.b. Gößing -> Gossing
#eigentlich ä->ae, aber ich hab kein paket gefunden was die regeln vom "ICAO Doc 9303 Part 3" umsetzt
from trans import trans
#Randint für den UVCI
from random import randint
#datetime für das Datum bei der Dateneingabe für das Zertifikat
from datetime import date
#auswahl Impfprodukt,Typ und Hersteller
from choices import choicelist_vaccines,choicelist_vaccine_types,choicelist_vaccine_auth_holder

#Zertifikat Input Forms
class VornameForm(FlaskForm):
    vorname = StringField("Vornamen",validators=[DataRequired()],default="Max")
    submit = SubmitField("Zertifikat erstellen")

class NachnameForm(FlaskForm):
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

class AusstellerForm(FlaskForm):
    aussteller = StringField("Zertifikatsausteller",validators=[DataRequired()],default="Robert Koch-Institut")
    
def makeforms():
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
    return formlist

#payload ersteller aus den Daten
def makepayload(formlist):
    #siehe: Technical Specifications for EU Digital COVID Certificates JSON Schema Specification
    dob=str(formlist[0].dob.data)
    gn=str(formlist[1].vorname.data)
    fn=str(formlist[2].nachname.data)
    co=str(formlist[3].land.data)
    tg=str(formlist[4].dAT.data)
    vp=str(formlist[5].vp.data)
    mp=str(formlist[6].mp.data)
    ma=str(formlist[7].ma.data)
    dn=(formlist[8].number.data)
    sd=(formlist[9].number.data)
    dt=str(formlist[10].vdate.data)
    is_=str(formlist[11].aussteller.data)#"is" ist ein keyword und kann nicht verwendet werden
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
