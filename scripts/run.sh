#!/bin/sh

rm -f /etc/nginx/conf.d/default.conf
nginx -g "daemon off;" > /dev/null 2>&1 &
python -u /event-listner.py
