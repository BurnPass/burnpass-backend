Generieren der Key-DB
=====================

```
pip install -r requirements.txt
cd keys_and_signscript
./gen-csca-dsc.sh
./keys_to_db.sh
```
Optional: Runterladen der valuesets und rules für den offline-modus
===================
```
python3 offline_valuesets.py
```
Starten des Servers
===================

```
sudo apt-get install zbar-tools
sudo apt-get install zbar-tools --fix-missing
./start_server.sh
```

Server braucht zum Prüfen mind. zwei Threads da sonst beim Prüfen nicht gleichzeit auch der Key zur Verfügung gestellt werden kann