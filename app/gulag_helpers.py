#!/usr/bin/env python3

import argparse,sys,os,time,signal
from Gulag import Gulag,GulagException

parser = argparse.ArgumentParser()
parser.add_argument('--config', required=True, help="Path to config file")
args = parser.parse_args()

child_pids = []
importer_pid = os.fork()
if(importer_pid == 0):
  # Child process: importer
  try:
    gulag = Gulag(args.config)
  except GulagException as e:
    print(e.message)
    sys.exit(1)
  while True:
    try:
      gulag.import_quarmails()
    except GulagException as e:
      print("Importer-Exception: " + e.message)
    time.sleep(gulag.config['importer']['interval'])

cleaner_pid = os.fork()
if(cleaner_pid == 0):
  # Child process: cleaner
  try:
    gulag = Gulag(args.config)
  except GulagException as e:
    print(e.message)
    sys.exit(1)
  while True:
    try:
      gulag.cleanup_quarmails()
    except GulagException as e:
      print("Cleaner-Exception: " + e.message)
    time.sleep(gulag.config['cleaner']['interval'])
 
# Parent
child_pids.append(importer_pid)
child_pids.append(cleaner_pid)
try:
  print("Entered helpers main loop...")
  while True:
    time.sleep(10)
except:
  print("MAIN-EXCEPTION: " + str(sys.exc_info()))
  # Destroy childs
  for child_pid in child_pids:
    print("Killing child pid: %s", child_pid)
    os.kill(child_pid, signal.SIGTERM)

