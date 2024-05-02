Generating the keys
===================
```bash
pip install -r requirements.txt
cd keys_and_signscript
python3 gen_csca_dsc.py
cd ../
```

Starting the server
===================
```bash
sudo apt-get install zbar-tools
sudo apt-get install zbar-tools --fix-missing
./start_server.sh
```

Server needs at least two threads to allow for concurrent signing and checking.

Windows/WSL is not recommended.
