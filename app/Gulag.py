import json,sys
import email,email.header
from GulagDB import GulagDB,GulagDBException
from GulagMailbox import IMAPmailbox,IMAPmailboxException

class GulagException(Exception):
  message = None
  def __init__(self,message):
    self.message = message

class Gulag:
  config = None
  db = None

  def __init__(self, path_to_config_file):
    try:
      with open(path_to_config_file, 'r') as f:
        self.config = json.load(f)
      f.close()
    except:
      raise GulagException("CONFIG-FILE-Exception: " + str(sys.exc_info()))

    try:
      self.db = GulagDB(
        self.config['db']['server'],
        self.config['db']['user'],
        self.config['db']['password'],
        self.config['db']['name']
      )
    except GulagDBException as e:
      raise GulagException(e.message) from e

  def import_quarmails(self):
    # Alle Mailboxes durchiterieren und die Meta-Infos aller neuen (unseen)
    # Nachrichten in die Datenbank importieren
    for mailbox in self.db.get_mailboxes():
      imap_mb = None
      try:
        imap_mb = IMAPmailbox(
          mailbox['imap_server'],
          mailbox['imap_user'],
          mailbox['imap_pass'],
          mailbox['imap_mailbox']
        )
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
        r5321_rcpts = email.header.decode_header(msg['X-Envelope-To-Blocked'])[0][0]
        r5322_from = email.header.decode_header(msg['From'])[0][0]
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
        r5321_rcpts = str(r5321_rcpts).lower()
        r5321_rcpts = r5321_rcpts.replace(" ", "")
        # Pro Envelope-RCPT einen Eintrag in die DB schreiben.
        # Die E-Mail im IMAP-Backend existiert jedoch nur ein Mal und wird
        # über die mailbox_id sowie die imap_uid mehrfach referenziert.
        for r5321_rcpt in r5321_rcpts.split(","):
          quarmail_id = self.db.add_quarmail({
            'mx_queue_id': 'queue_id', 'env_from': r5321_from, 'env_rcpt': r5321_rcpt,
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

