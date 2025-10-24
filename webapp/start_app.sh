#!/bin/bash

# Start Gunicorn in the background
# gunicorn -w 1 -b 0.0.0.0:5000 app:app --access-logfile /var/log/gunicorn/access.log --error-logfile /var/log/gunicorn/error.log &
/usr/bin/python3 app.py 

# Start socket server in foreground
# /usr/bin/python3 /webapp/ws_server.py
