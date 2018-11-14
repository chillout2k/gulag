# gulag
Gulag quarantine

config.json:
`{
  "daemon":{
    "listen_host": "127.0.0.1",
    "listen_port": 5001
  },
  "trusted_proxies": {
    "rprx01":[
      "172.16.100.5", "fd00:100::5"
    ],
    "rprx02":[
      "172.16.100.6", "fd00:100::6"
    ]
  },
  "api_keys": {
    "HIGHLY_SECURE_API_KEY": {
      "user": "GULAG APP"
    }
  },
  "uri_prefixes": {
    "root": "https://<fqdn>/api/v1/",
    "quarmails": "https://<fqdn>/api/v1/quarmails/",
    "attachments": "https://<fqdn>/api/v1/attachments/"
  },
  "db":{
    "server": "127.0.0.1",
    "user": "root",
    "password": "",
    "name": "Gulag"
  },
  "cleaner":{
    "retention_period": "12 hour",
    "interval": 10
  },
  "importer":{
    "interval": 10
  }
}`

uwsgi.ini:
`[uwsgi]
processes = 4
cheaper = 1
cheaper-initial = 1
cheaper-step = 1
python-path = /app
wsgi-file = /app/uwsgi.py
pyargv = --config /config/config.json
socket = /socket/gulag_uwsgi.sock`

