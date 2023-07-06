import requests
import json

# dict with suburl:[onlineurl,content]
urls = {"/trustList/DSC/": ["https://de.dscg.ubirch.com/trustList/DSC", None],
        "/bnrules": ["https://distribution.dcc-rules.de/bnrules", None],  # has suburl /bnrules/<string:bnhash>
        "/valuesets": ["https://distribution.dcc-rules.de/valuesets", None],
        # has suburl /valuesets/<string:valuesethash>
        "/rules": ["https://distribution.dcc-rules.de/rules", None],
        # has suburl '/rules/<string:rules_country>/<string:rules_sub_hash>'
        "/countrylist": ["https://distribution.dcc-rules.de/countrylist", None],
        "/domesticrules": ["https://distribution.dcc-rules.de/domesticrules", None],  # has suburl
        "/kid.lst": ["https://de.crl.dscg.ubirch.com/kid.lst", None],  # '/<string:indexhash>/index.lst'
        }


def download_valuesets_and_rules():
    for element in urls:
        response = requests.get(urls[element][0])
        if element == "/kid.lst":
            urls[element][1] = response.content
        else:
            urls[element][1] = response.text
        print("loading " + element)

    suburls = ["/bnrules", "/valuesets", "/rules", "/domesticrules"]
    for suburl in suburls:
        liste = json.loads(urls[suburl][1])
        for element in liste:
            if suburl == "/rules":
                hash_ = element["hash"]
                country = element["country"]
                url = "/" + country + "/" + hash_
            else:
                hash_ = element["hash"]
                url = "/" + hash_
            url_ganz = urls[suburl][0] + url
            response = requests.get(url_ganz)
            urls[suburl + url] = [url_ganz, response.text]
            print("loading " + suburl + url)

    for element in urls:
        if element == "/kid.lst":
            with open("offline_valuesets/" + element.replace("/", "_"), "wb") as f:
                f.write((urls[element][1]))
        else:
            with open("offline_valuesets/" + element.replace("/", "_") + ".txt", "w", encoding="utf-8") as f:
                f.write((urls[element][1]))
        print("saving " + element)


if __name__ == "__main__":
    download_valuesets_and_rules()
