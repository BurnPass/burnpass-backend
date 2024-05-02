:: pip install waitress
:: pip install hupper
hupper -m waitress --host=0.0.0.0 --port=8000 --threads=8 server:app
pause