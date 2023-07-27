#!/usr/bin/env python
import inspect
import json
# requests um auf das offizielle Backend live zurückzugreifen
import requests
# Flask-Json für json darstellung im browser
from flask_json import as_json
# config
from config import *
from flask import Blueprint

app_valuesets_blueprint = Blueprint('app_valuesets_blueprint', __name__)


# trustlist
@app_valuesets_blueprint.route("/trustList/DSC/")
# @as_json
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
            url = "https://de.dscg.ubirch.com/trustList/DSC"
            try:
                response = requests.get(url)
                trustlist = response.content
                return trustlist
            except:
                return "not valid or failed"


# bnrules
@app_valuesets_blueprint.route("/bnrules")
@as_json
def bnrules_app():
    print("queried", inspect.stack()[0][3])
    url = "https://distribution.dcc-rules.de/bnrules"
    if offlinemode:
        with open("offline_valuesets/_bnrules.txt", "r", encoding="utf-8") as file:
            content = json.loads(file.read())
        return content
    else:
        try:
            response = requests.get(url)
            bnrules = response.json()
            return bnrules
        except:
            return "not valid or failed"


@app_valuesets_blueprint.route("/bnrules/<string:bnhash>")
@as_json
def bnrules_app_hashes(bnhash):
    print("queried", inspect.stack()[0][3], bnhash)
    url = "https://distribution.dcc-rules.de/bnrules/" + bnhash
    if offlinemode:
        with open("offline_valuesets/_bnrules_" + bnhash + ".txt", "r", encoding="utf-8") as file:
            content = json.loads(file.read())
        return content
    else:
        try:
            response = requests.get(url)
            bnrules = response.json()
            return bnrules
        except:
            return "not valid or failed"


# valuests
@app_valuesets_blueprint.route('/valuesets')
@as_json
def valuesets():
    print("queried", inspect.stack()[0][3])
    url = "https://distribution.dcc-rules.de/valuesets"
    if offlinemode:
        with open("offline_valuesets/_valuesets.txt", "r", encoding="utf-8") as file:
            content = json.loads(file.read())
        return content
    else:
        try:
            response = requests.get(url)
            valuesets = response.json()
            return valuesets
        except:
            return "not valid or failed"


@app_valuesets_blueprint.route('/valuesets/<string:valuesethash>')
@as_json
def valuesetshash(valuesethash):
    print("queried", inspect.stack()[0][3], valuesethash)
    url = "https://distribution.dcc-rules.de/valuesets/" + valuesethash
    if offlinemode:
        with open("offline_valuesets/_valuesets_" + valuesethash + ".txt", "r", encoding="utf-8") as file:
            content = json.loads(file.read())
        return content
    else:
        try:
            response = requests.get(url)
            valuesets = response.json()
            return valuesets
        except:
            return "not valid or failed"


# rules
@app_valuesets_blueprint.route('/rules')
@as_json
def rules():
    print("queried", inspect.stack()[0][3])
    url = "https://distribution.dcc-rules.de/rules"
    if offlinemode:
        with open("offline_valuesets/_rules.txt", "r", encoding="utf-8") as file:
            content = json.loads(file.read())
        return content
    else:
        try:
            response = requests.get(url)
            rules = response.json()
            return rules
        except:
            return "not valid or failed"


@app_valuesets_blueprint.route('/rules/<string:rules_country>/<string:rules_sub_hash>')
@as_json
def rules_suburl(rules_country, rules_sub_hash):
    print("queried", inspect.stack()[0][3], rules_country, rules_sub_hash)
    url = "https://distribution.dcc-rules.de/rules/" + rules_country + "/" + rules_sub_hash
    if offlinemode:
        with open("offline_valuesets/_rules_" + rules_country + "_" + rules_sub_hash + ".txt", "r",
                  encoding="utf-8") as file:
            content = json.loads(file.read())
        return content
    else:
        try:
            response = requests.get(url)
            rules = response.json()
            return rules
        except:
            return "not valid or failed"


# country list
@app_valuesets_blueprint.route('/countrylist')
@as_json
def countrylist():
    print("queried", inspect.stack()[0][3])
    url = "https://distribution.dcc-rules.de/countrylist"
    if offlinemode:
        with open("offline_valuesets/_countrylist.txt", "r", encoding="utf-8") as file:
            content = json.loads(file.read())
        return content
    else:
        try:
            response = requests.get(url)
            countrylist = response.json()
            return countrylist
        except:
            return "not valid or failed"


# domestic rules
@app_valuesets_blueprint.route('/domesticrules')
@as_json
def domesticrules():
    print("queried", inspect.stack()[0][3])
    url = "https://distribution.dcc-rules.de/domesticrules"
    if offlinemode:
        with open("offline_valuesets/_domesticrules.txt", "r", encoding="utf-8") as file:
            content = json.loads(file.read())
        return content
    else:
        try:
            response = requests.get(url)
            domesticrules = response.json()
            return domesticrules
        except:
            return "not valid or failed"


@app_valuesets_blueprint.route('/domesticrules/<string:domestic_hash>')
@as_json
def domestic_suburl(domestic_hash):
    print("queried", inspect.stack()[0][3], domestic_hash)
    url = "https://distribution.dcc-rules.de/domesticrules/" + domestic_hash
    if offlinemode:
        with open("offline_valuesets/_domesticrules" + "_" + domestic_hash + ".txt", "r", encoding="utf-8") as file:
            content = json.loads(file.read())
        return content
    else:
        try:
            response = requests.get(url)
            domesticrules = response.json()
            return domesticrules
        except:
            return "not valid or failed"


# lst kid und index, wurde iwann mal abgefragt. aber nicht oft, kann also nicht so wichtig sein
# hat was mit der revocationlist zu tun
@app_valuesets_blueprint.route('/kid.lst')
def kidlst():
    print("queried", inspect.stack()[0][3])
    if offlinemode:
        with open("offline_valuesets/_kid.lst", "rb") as file:
            content = file.read()
        return content
    else:
        try:
            url = "https://de.crl.dscg.ubirch.com/kid.lst"
            response = requests.get(url)
            kidlst = response.content
            return kidlst
        except:
            return "not valid or failed"


@app_valuesets_blueprint.route('/<string:indexhash>/index.lst')
def lstindex(indexhash):
    print("queried", inspect.stack()[0][3], indexhash)
    if offlinemode:
        return "None"
    else:
        try:
            url = "https://de.crl.dscg.ubirch.com/" + indexhash + "/index.lst"
            response = requests.get(url)
            kidlst = response.content
            return kidlst
        except:
            return "not valid or failed"
