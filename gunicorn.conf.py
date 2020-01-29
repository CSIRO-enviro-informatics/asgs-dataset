#!/usr/bin/env python3
#
threads = 1
workers = 2
pid = "./gunicorn.pid"
keepalive = 5
timeout = 320
app_module = "asgs_dataset.proxyfix_app:app"
