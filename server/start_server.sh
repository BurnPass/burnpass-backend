#!/bin/sh
export FLASK_DEBUG=development
export FLASK_APP=server.py
gunicorn 'server:app' --reload -w 4
