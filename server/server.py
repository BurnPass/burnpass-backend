from flask import Flask, render_template
import json

app = Flask(__name__)

@app.route("/")
def index():
    return "leer"

@app.route("/dsa_keys")
def dsa_keys():
    with open("db.json", "rb") as file:
        dsa_keys = file.read()
    dsa_json=json.loads(dsa_keys)
    return dsa_json

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8000 ,debug=True)
