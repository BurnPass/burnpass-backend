Generieren der Keys
=====================

```
pip install -r requirements.txt
cd keys_and_signscript
python3 gen_csca_dsc.py
cd ../
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

Server braucht zum Prüfen mit eigenem Public Key mind. zwei Threads da sonst beim Prüfen nicht gleichzeit auch der Key zur Verfügung gestellt werden kann.
Nachdem die Schritte einmal in Linux ausgeführt wurden, kann der Server auch auf windows mit dem start_windows.bat ausgeführt werden, dafür muss jedoch auch noch mit pip waitress und hupper installiert werden.
Im "Windows Subsystem for Linux" (WSL) kann der Server zwar ausgeführt werden, ist jedoch im lokalen Netz nicht ohne weiteres erreichbar.