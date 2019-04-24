#!/usr/bin/env python3

import argparse,sys,os,time,signal,logging
from Gulag import Gulag,GulagException
import traceback

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
    logging.info("Gulag-Importer Exception: " + e.message)
    sys.exit(1)
  except:
    logging.info("Gulag-Importer Exception: " + str(sys.exc_info()))
  logging.info("Gulag-Importer: starting")
  while True:
    try:
      gulag.import_quarmails()
    except GulagException as e:
      logging.error("Gulag-Importer-Exception: " + e.message)
    except:
      logging.error("Gulag-Importer-Exception: " + traceback.format_exc())
    time.sleep(gulag.config['importer']['interval'])

cleaner_pid = os.fork()
if(cleaner_pid == 0):
  # Child process: cleaner
  try:
    gulag = Gulag(args.config)
  except GulagException as e:
    logging.info("Gulag-Cleaner-Exception: " + e.message)
    sys.exit(1)
  logging.info("Gulag-Cleaner: starting")
  while True:
    try:
      gulag.cleanup_quarmails()
    except GulagException as e:
      logging.info("Cleaner-Exception: " + e.message)
    except:
      logging.info("Cleaner-Exception: " + traceback.format_exc())
    time.sleep(gulag.config['cleaner']['interval'])

# Parent
child_pids.append(importer_pid)
child_pids.append(cleaner_pid)
try:
  while True:
    time.sleep(10)
except:
  logging.info("Helpers MAIN-EXCEPTION: " + traceback.format_exc())
  # Destroy childs
  for child_pid in child_pids:
    logging.info("Helpers parent: Killing child pid: %s", child_pid)
    os.kill(child_pid, signal.SIGTERM)
