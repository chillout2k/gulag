import json,sys
import email,email.header,email.message
from flask import request
from smtplib import SMTP
from GulagDB import GulagDB,GulagDBException
from GulagMailbox import IMAPmailbox,IMAPmailboxException

class GulagException(Exception):
  message = None
  def __init__(self,message):
    self.message = message

class Gulag:
  version = None
  config = None
  db = None

  def __init__(self, path_to_config_file):
    self.version = "VERSION-TODO!"
    try:
      with open(path_to_config_file, 'r') as f:
        self.config = json.load(f)
      f.close()
    except:
      raise GulagException("CONFIG-FILE-Exception: " + str(sys.exc_info()))

    try:
      self.db = GulagDB(self.config['db'],self.config['uri_prefixes'])
    except GulagDBException as e:
      raise GulagException(e.message) from e

  # Iterate through all mailboxes, extract metadata
  # from all unseen mails and pump them into database
  def import_quarmails(self):
    for mailbox in self.db.get_mailboxes():
      imap_mb = None
      try:
        imap_mb = IMAPmailbox(mailbox)
      except IMAPmailboxException as e:
        print(e.message)
        continue
      quarmail_ids = []
      attachments = []
      for unseen in imap_mb.get_unseen_messages():
        uid = unseen['imap_uid']
        msg = unseen['msg']
        msg_size = len(str(msg))
        r5321_from = email.header.decode_header(msg['Return-Path'])[0][0]
        if(r5321_from is not '<>'):
          r5321_from = r5321_from.replace("<","")
          r5321_from = r5321_from.replace(">","")
        r5321_rcpts = None
        try:
          r5321_rcpts = email.header.decode_header(msg['X-Envelope-To-Blocked'])[0][0]
        except:
          print("Failed to extract envelope recipients! Skipping mail")
          continue
        r5322_from = None
        try:
          r5322_from = email.header.decode_header(msg['From'])[0][0]
        except:
          print("Failed to extract from header! Skipping mail")
          continue
        subject = email.header.decode_header(msg['Subject'])[0][0]
        msg_id = None
        try:
          msg_id = email.header.decode_header(msg['Message-ID'])[0][0]
        except:
          pass
        date = None
        try:
          date = email.header.decode_header(msg['Date'])[0][0]
        except:
          pass
        x_spam_status = email.header.decode_header(msg['X-Spam-Status'])[0][0]
        mx_queue_id = "n.a."
        try:
          mx_queue_id = email.header.decode_header(msg['X-Spam-QID'])[0][0]
        except:
          pass
        r5321_rcpts = str(r5321_rcpts).lower()
        r5321_rcpts = r5321_rcpts.replace(" ", "")
        r5321_rcpts = r5321_rcpts.replace("<", "")
        r5321_rcpts = r5321_rcpts.replace(">", "")
        # Pro Envelope-RCPT einen Eintrag in die DB schreiben.
        # Die E-Mail im IMAP-Backend existiert jedoch nur ein Mal und wird
        # über die mailbox_id sowie die imap_uid mehrfach referenziert.
        for r5321_rcpt in r5321_rcpts.split(","):
          quarmail_id = self.db.add_quarmail({
            'mx_queue_id': mx_queue_id, 'env_from': r5321_from, 'env_rcpt': r5321_rcpt,
            'hdr_cf': x_spam_status, 'hdr_from': r5322_from, 'hdr_subject': subject,
            'hdr_msgid': msg_id, 'hdr_date': date, 'cf_meta': 'cf_meta',
            'mailbox_id': 'quarantine@zwackl.de', 'imap_uid': uid, 'msg_size': msg_size
          })
          quarmail_ids.append(quarmail_id)
        # Ende for rcpts
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
            attach_id = self.db.add_attachment({
              'filename': filename,
              'content_type': part.get_content_type()
            })
            attachments.append(attach_id)
          # Ende if part.get_filename()
        # Ende for msg.walk()
      # Ende for(unseen)
      imap_mb.close()
      # QuarMails und Attachments verknüpfen
      if(len(attachments) > 0):
        for quarmail_id in quarmail_ids:
          for attachment_id in attachments:
            self.db.quarmail2attachment(str(quarmail_id), str(attachment_id))
    # Ende for get_mailboxes

  def cleanup_quarmails(self):
    print("Mails to expunge: " + 
      str(len(
        self.db.get_deprecated_mails(self.config['cleaner']['retention_period'])
      ))
    )
  
  def get_mailboxes(self):
    try:
      return self.db.get_mailboxes()
    except GulagDBException as e:
      raise GulagException("GulagDBException: " + e.message) from e

  def get_quarmails(self):
    try:
      return self.db.get_quarmails()
    except GulagDBException as e:
      raise GulagException("GulagDBException: " + e.message) from e
  
  def get_quarmail(self,args):
    qm_db = None
    try:
      qm_db = self.db.get_quarmail({
        "id": args['id']
      })
    except GulagDBException as e:
      raise GulagException("GulagDBException: " + e.message) from e
    if 'rfc822_message' not in args:
      return qm_db
    mailbox = None
    try:
      mailbox = self.db.get_mailbox(qm_db['mailbox_id'])
    except GulagDBException as e:
      raise GulagException(e.message) from e 
    imap_mb = None
    try:
      imap_mb = IMAPmailbox(mailbox)
      qm_db['rfc822_message'] = imap_mb.get_message(qm_db['imap_uid'])
      return qm_db
    except IMAPmailboxException as e:
      print(e.message)
      raise GulagException(e.message) from e
  
  def rspamd_http2imap(self,mailbox_id):
    mailbox = None
    try:
      mailbox = self.db.get_mailbox(mailbox_id)
    except GulagDBException as e:
      raise GulagException(e.message) from e

    if(request.headers.get('X-Rspamd-From') == None):
      raise GulagException("Missing Rspamd-specific headers (e.g. X-Rspamd-From)!")
    # recompose rejected mail that will be sent to quarantine mailbox
    msg = None
    try:
      rcpts_hdr = ""
      for rcpt in json.loads(str(request.headers.get('X-Rspamd-Rcpt'))):
        if(len(rcpts_hdr) > 0):
          rcpts_hdr = rcpts_hdr + "," + rcpt
        else:
          rcpts_hdr = rcpt
      msg = "Return-Path: <" + request.headers.get('X-Rspamd-From') + ">\r\n"
      msg = msg + "Received: from rspamd_http2imap relay by gulag-mailbox " + mailbox_id + "\r\n"
      msg = msg + "X-Envelope-To-Blocked: " + rcpts_hdr + "\r\n"
      msg = msg + "X-Spam-Status: " + request.headers.get('X-Rspamd-Symbols') + "\r\n"
      msg = msg + "X-Spam-QID: " + request.headers.get('X-Rspamd-Qid') + "\r\n"
      msg = msg + request.get_data(as_text=True)
#FIXME:   except email.errors.* as e:
    except:
      raise GulagException(str(sys.exc_info()))
    
    # Use IMAP´s APPEND command to store the message into mailbox
    imap_mb = None
    try:
      imap_mb = IMAPmailbox(mailbox)
      imap_mb.append_message(msg)
    except IMAPmailboxException as e:
      raise GulagException(e.message) from e
#    try:
#      if not mailbox['smtp_server']:
#        raise GulagException("No SMTP server configured for mailbox " + mailbox_id)
#      # FIXME: SMTP tranaport security and authentication!
#      with SMTP(host=mailbox['smtp_server'],port=mailbox['smtp_port']) as smtp:
#        try:
#          smtp.sendmail(
#            request.headers.get('X-Rspamd-From'),
#            mailbox_id,
#            msg
#          )
#        except (SMTPRecipientsRefused,SMTPHeloError,SMTPSenderRefused,SMTPDataError) as e:
#          raise GulagException(str(e)) from e
#    except TimeoutError as e:
#      raise GulagException(str(e)) from e

