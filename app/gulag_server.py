#!/usr/bin/env python3

import argparse,sys,os,time,signal
from flask import Flask
from flask_restful import Api
from Gulag import Gulag,GulagException
from Resources import ResRoot,ResQuarMails

parser = argparse.ArgumentParser()
parser.add_argument('--config', required=True, help="Path to config file")
args = parser.parse_args()

#child_pids = []
#importer_pid = os.fork()
#if(importer_pid == 0):
#  # Child process: importer
#  try:
#    gulag = Gulag(args.config)
#  except GulagException as e:
#    print(e.message)
#    sys.exit(1)
#  while True:
#    try:
#      gulag.import_quarmails()
#    except GulagException as e:
#      print("Importer-Exception: " + e.message)
#    time.sleep(gulag.config['importer']['interval'])
#
#cleaner_pid = os.fork()
#if(cleaner_pid == 0):
#  # Child process: cleaner
#  try:
#    gulag = Gulag(args.config)
#  except GulagException as e:
#    print(e.message)
#    sys.exit(1)
#  while True:
#    try:
#      gulag.cleanup_quarmails()
#    except GulagException as e:
#      print("Cleaner-Exception: " + e.message)
#    time.sleep(gulag.config['cleaner']['interval'])
 
# Parent
#child_pids.append(importer_pid)
#child_pids.append(cleaner_pid)
try:
  try:
    gulag = Gulag(args.config)
  except GulagException as e:
    raise Exception(e.message) from e
  app = Flask(__name__)
  api = Api(app, catch_all_404s=True)
  api.add_resource(ResRoot,
    '/api/v1/',
    resource_class_kwargs={'gulag_object': gulag}
  )
  api.add_resource(ResQuarMails,
    '/api/v1/quarmails/',
    resource_class_kwargs={'gulag_object': gulag}
  )
  if __name__ == '__main__':
    app.run(debug=False,
      # will be overriden by uwsgi.ini
      host=gulag.config['daemon']['listen_host'],
      port=gulag.config['daemon']['listen_port']
    )
    gulag.db.close()
    sys.exit(0)
except:
  print("MAIN-EXCEPTION: " + str(sys.exc_info()))
#  # Destroy childs
#  for child_pid in child_pids:
#    print("Killing child pid: %s", child_pid)
#    os.kill(child_pid, signal.SIGTERM)


