# verschiedene imports für die verschiedenen eingabefelder
# datetime für das Datum bei der Dateneingabe für das Zertifikat
from datetime import date
# Randint für den UVCI
from random import randint

from flask_wtf import FlaskForm
# transkription bei Namen für der Zertifikat. z.b. Gößing -> Gossing
# eigentlich ä->ae, aber ich hab kein paket gefunden was die regeln vom "ICAO Doc 9303 Part 3" umsetzt
from trans import trans
from wtforms import StringField, SubmitField, SelectField
from wtforms.fields import DateField
from wtforms.validators import DataRequired

# auswahl Impfprodukt,Typ und Hersteller
from choices import choicelist_countries


# Zertifikat Input Forms
class VornameForm(FlaskForm):
    vorname = StringField("Vornamen", validators=[DataRequired()], default="Max")
    submit = SubmitField("Zertifikat erstellen")


class NachnameForm(FlaskForm):
    nachname = StringField("Nachname", validators=[DataRequired()], default="Mustermann")


class DateOfBirthForm(FlaskForm):
    dob = DateField('Geburtsdatum', default=date.today)


class vaccinationDateForm(FlaskForm):
    vdate = DateField('Tag der Brandschutzschulung', default=date.today)


class LandwahlForm(FlaskForm):
    land = SelectField("Ausstellungsland", choices=choicelist_countries, validators=[DataRequired()])


class AusstellerForm(FlaskForm):
    aussteller = StringField("Zertifikatsaussteller", validators=[DataRequired()], default="Institut für Brandschutz")


def makeforms():
    # Je ein Formulareintrag pro variable
    vnameform = VornameForm()
    nnameform = NachnameForm()
    dobform = DateOfBirthForm()
    landform = LandwahlForm()
    dtform = vaccinationDateForm()
    isform = AusstellerForm()

    # liste aller formulareinträge
    formlist = [dobform, vnameform, nnameform, landform, dtform, isform]
    return formlist


# payload Dict erstellen aus den Daten
def makepayload(formlist):
    # siehe: Technical Specifications for EU Digital COVID Certificates JSON Schema Specification
    dob = str(formlist[0].dob.data)
    gn = str(formlist[1].vorname.data)
    fn = str(formlist[2].nachname.data)
    co = str(formlist[3].land.data)
    dt = str(formlist[4].vdate.data)
    is_ = str(formlist[5].aussteller.data)  # "is" ist ein keyword und kann nicht verwendet werden
    ci = str(randint(0, 9999999999999999))
    ci = ci.zfill(16)
    payload_dict = {
        "dob": dob,
        "nam": {
            "fn": fn,
            "fnt": trans(fn, "slug").upper().replace("_", "<"),
            "gn": gn,
            "gnt": trans(gn, "slug").upper().replace("_", "<")
        },
        "v": [
            {
                "ci": ci,
                "co": co,
                "dt": dt,
                "is": is_,
            }
        ],
        "ver": "1.3.3.7"
    }
    return payload_dict
