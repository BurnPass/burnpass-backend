#!/bin/sh
export FLASK_ENV=development
export FLASK_APP=server.py
gunicorn 'server:app' --reload -w 2
