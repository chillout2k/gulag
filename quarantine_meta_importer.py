#!/usr/bin/env python3

import sys
import imaplib
import email
import email.header
import json
import fcntl
import uuid
import argparse

DB_FILE = "quar_db.json"

def process_mailbox(MAILBOX):
  db = []
  try:
    f = open(DB_FILE, 'r')
    fcntl.flock(f, fcntl.LOCK_EX | fcntl.LOCK_NB)
    db = json.load(f)
    fcntl.flock(f, fcntl.LOCK_UN)
    f.close()
  except FileNotFoundError:
    pass
  except:
    print("DB-file-open-exception: " + str(sys.exc_info()))
    sys.exit(1)

  rv, data = MAILBOX.uid('SEARCH', 'UNSEEN')
  if rv != 'OK':
    return
  # Alle "neuen" Nachrichten durchiterieren und
  # Meta-Infos in die Datenbank importieren
  for uid in data[0].split():    
    uid = uid.decode()
    rv, data = MAILBOX.uid('FETCH', uid, '(RFC822)')
    if rv != 'OK':
      print("ERROR getting message", uid)
      sys.exit(1)
    msg = email.message_from_bytes(data[0][1])
    msg_size = len(str(msg))
    attachments = []
    # Alle MIME-Parts durchiterieren und Attachments
    # (MIME-Parts mit name/filename Attribut) extrahieren
    for part in msg.walk():
      if part.get_filename():
        # ist ein Attachment
        filename = email.header.decode_header(part.get_filename())
        if filename[0][1]:
          # Encoded
          filename = filename[0][0].decode(filename[0][1])
        else:
          # Nicht encoded
          filename = filename[0][0]
        attachments.append({
          'filename': filename,
          'content-type': part.get_content_type() # Ist das wirklich wahr?
        })
      # Ende if part.get_filename()
    # Ende for ... msg.walk()
    r5321_from = email.header.decode_header(msg['Return-Path'])[0][0]
    r5321_rcpts = email.header.decode_header(msg['X-Envelope-To-Blocked'])[0][0]
    r5322_from = email.header.decode_header(msg['From'])[0][0]
    subject = email.header.decode_header(msg['Subject'])[0][0]
    quar_id = str(uuid.uuid4())
    msg_id = None
    try:
      msg_id = email.header.decode_header(msg['Message-ID'])[0][0]
    except:
      pass
    x_spam_status = email.header.decode_header(msg['X-Spam-Status'])[0][0]
    r5321_rcpts = str(r5321_rcpts).lower()
    r5321_rcpts = r5321_rcpts.replace(" ", "")
    db.append({
      'quarantine_id': quar_id, # AUTO_INCREMENT
      'envelope_sender': r5321_from,
      'envelope_recipients': r5321_rcpts,
      'from_header': r5322_from,
      'subject': subject,
      'message_id': msg_id,
      'imap_uid': uid,
      'spam_status': x_spam_status,
      'msg_size': msg_size,
      'attachments': attachments
    })
  # Ende for(unseen)
  try:
    f = open(DB_FILE, 'w')
    fcntl.flock(f, fcntl.LOCK_EX | fcntl.LOCK_NB)
    json.dump(db, f)
    fcntl.flock(f, fcntl.LOCK_UN)
    f.close()
  except:
    print("DB-file-open-exception: " + str(sys.exc_info()))
    sys.exit(1)

if __name__ == '__main__':
  parser = argparse.ArgumentParser()
  parser.add_argument('--config', required=True, help="Path to config file")
  args = parser.parse_args()
  config = {}
  try:
    with open(args.config, 'r') as f:
      config = json.load(f)
    f.close()
  except:
    print("CONFIG-FILE-Exception: " + str(sys.exc_info()))
    sys.exit(1)
 
#  INBOX = imaplib.IMAP4('mbox02.zwackl.local')
  INBOX = imaplib.IMAP4(config['imap']['server'])
  
  try:
#    rv, data = INBOX.login(EMAIL_ACCOUNT, EMAIL_PASS)
    rv, data = INBOX.login(
      config['imap']['user'], config['imap']['password']
    )
  except imaplib.IMAP4.error:
    print ("LOGIN FAILED!!! ")
    sys.exit(1)
  
#  rv, data = INBOX.select(EMAIL_FOLDER)
  rv, data = INBOX.select(config['imap']['folder'])
  if rv == 'OK':
    process_mailbox(INBOX)
    INBOX.close()
  else:
    print("ERROR: Unable to open mailbox ", rv)
  
  INBOX.logout()
  sys.exit(0)
