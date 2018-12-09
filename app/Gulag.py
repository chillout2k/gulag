import json,sys,os,logging
import email,email.header,email.message
from GulagDB import GulagDB,GulagDBException
from GulagMailbox import IMAPmailbox,IMAPmailboxException
from GulagUtils import whoami

class GulagException(Exception):
  message = None
  def __init__(self,message):
    self.message = message

class Gulag:
  version = None
  config = None
  db = None
  fields = {}

  def __init__(self, path_to_config_file):
    self.version = "VERSION-TODO!"
    try:
      with open(path_to_config_file, 'r') as f:
        self.config = json.load(f)
      f.close()
    except:
      raise GulagException(whoami(self) + str(sys.exc_info()))
    # logging
#    logging_level = logging.INFO
#    if 'level' in self.config['logging']:     
    if 'logging' not in self.config:
      raise GulagException(whoami(self) + "Logging not configured!")
    if('filename' in self.config['logging'] and 
       len(self.config['logging']['filename']) > 0):
      logging.basicConfig(
        filename=self.config['logging']['filename'],
        format='%(asctime)s %(levelname)s %(message)s',
        level=self.config['logging']['level']
      )
    else:
      logging.basicConfig(
        format='%(asctime)s %(levelname)s %(message)s',
        level=self.config['logging']['level']
      )
    try:
      self.db = GulagDB(self.config['db'],self.config['uri_prefixes'])
      self.fields['Mailboxes'] = self.db.get_fields('Mailboxes')
      self.fields['QuarMails'] = self.db.get_fields('QuarMails')
      self.fields['Attachments'] = self.db.get_fields('Attachments')
    except GulagDBException as e:
      logging.warning(whoami(self) + e.message)
      raise GulagException(whoami(self) + e.message) from e
    logging.info('Gulag core initialized by ' + os.path.basename(__file__))
   
  def check_fields(self,fields_target,args):
    if fields_target not in self.fields:
      raise GulagException(
        whoami(self) + fields_target + " not found in Gulag.fields!"
      )
    for arg in args:
      if(arg == 'query_offset' or arg == 'query_limit' 
         or arg == 'sort_index' or arg == 'sort_order'):
        continue
      if arg not in self.fields[fields_target]:
        raise GulagException(
          whoami(self) + arg + " is not a valid field of " 
          + fields_target + "!"
        )

  # Iterate through all mailboxes, extract metadata
  # from all unseen mails and pump them into database
  def import_quarmails(self):
    for mailbox in self.db.get_mailboxes():
      imap_mb = None
      try:
        imap_mb = IMAPmailbox(mailbox)
      except IMAPmailboxException as e:
        logging.warning(whoami(self) + e.message)
        continue
      for unseen in imap_mb.get_unseen_messages():
        quarmail_ids = []
        attachments = []
        uid = unseen['imap_uid']
        msg = email.message_from_bytes(unseen['msg'])
        msg_size = len(msg)
        r5321_from = email.header.decode_header(msg['Return-Path'])[0][0]
        if(r5321_from is not '<>'):
          r5321_from = r5321_from.replace("<","")
          r5321_from = r5321_from.replace(">","")
        r5321_rcpts = None
        try:
          r5321_rcpts = email.header.decode_header(msg['X-Envelope-To-Blocked'])[0][0]
        except:
          logging.warning(whoami(self) + 
            "Failed to extract envelope recipients! Skipping mail"
          )
          continue
        r5322_from = None
        try:
          r5322_from = email.header.decode_header(msg['From'])[0][0]
        except:
          logging.warning(whoami(self) + 
            "Failed to extract from header! Skipping mail"
          )
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
          logging.info(whoami(self) + "QuarMail (%s) imported" % (quarmail_id))
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
              'content_type': part.get_content_type(),
              'content_encoding': part['Content-Transfer-Encoding']
            })
            attachments.append(attach_id)
          # Ende if part.get_filename()
        # Ende for msg.walk()
        # QuarMail und Attachments verknüpfen
        if(len(attachments) > 0):
          for quarmail_id in quarmail_ids:
            for attachment_id in attachments:
              self.db.quarmail2attachment(str(quarmail_id), str(attachment_id))
      # Ende for(unseen)
      imap_mb.close()
    # Ende for get_mailboxes

  def cleanup_quarmails(self):
    logging.info(whoami(self) + "QuarMails to purge:  " + str(len(
      self.db.get_deprecated_mails(self.config['cleaner']['retention_period'])
     )))
  
  def get_mailboxes(self):
    try:
      return self.db.get_mailboxes()
    except GulagDBException as e:
      logging.warning(whoami(self) + e.message)
      raise GulagException(whoami(self) + e.message) from e

  def get_quarmails(self,args):
    try:
      self.check_fields('QuarMails',args)
      return self.db.get_quarmails(args)
    except(GulagException,GulagDBException) as e:
      logging.warning(whoami(self) + e.message)
      raise GulagException(
        whoami(self) + e.message
      ) from e
  
  def get_quarmail(self,args):
    qm_db = None
    try:
      qm_db = self.db.get_quarmail({"id": args['quarmail_id']})
    except GulagDBException as e:
      logging.warning(whoami(self) + e.message)
      raise GulagException(whoami(self) + e.message) from e
    if 'rfc822_message' not in args:
      return qm_db
    # pull full RFC822 message from IMAP mailbox
    mailbox = None
    try:
      mailbox = self.db.get_mailbox(qm_db['mailbox_id'])
    except GulagDBException as e:
      logging.warning(whoami(self) + e.message)
      raise GulagException(whoami(self) + e.message) from e 
    imap_mb = None
    try:
      imap_mb = IMAPmailbox(mailbox)
      qm_db['rfc822_message'] = imap_mb.get_message(qm_db['imap_uid']).decode("utf-8")
      return qm_db
    except IMAPmailboxException as e:
      logging.warning(whoami(self) + e.message)
      raise GulagException(whoami(self) + e.message) from e

  def get_quarmail_attachments(self,args):
    try:
      return self.db.get_quarmail_attachments(args['quarmail_id'])
    except GulagDBException as e:
      logging.warning(whoami(self) + e.message)
      raise GulagException(whoami(self) + e.message) from e
  
  def get_quarmail_attachment(self,args):
    qmat_db = None
    try:
      qmat_db = self.db.get_quarmail_attachment(
        args['quarmail_id'],args['attachment_id']
      )
    except GulagDBException as e:
      logging.warning(whoami(self) + e.message)
      raise GulagException(whoami(self) + e.message) from e
    if 'data' not in args:
      return qmat_db
    # pull attachment from IMAP mailbox
    mailbox = None
    try:
      mailbox = self.db.get_mailbox(qmat_db['mailbox_id'])
    except GulagDBException as e:
      logging.warning(whoami(self) + e.message)
      raise GulagException(whoami(self) + e.message) from e 
    imap_mb = None
    try:
      imap_mb = IMAPmailbox(mailbox)
      qmat_db['data'] = imap_mb.get_attachment(
        qmat_db['imap_uid'],qmat_db['filename']
      )
      return qmat_db
    except IMAPmailboxException as e:
      logging.warning(whoami(self) + e.message)
      raise GulagException(whoami(self) + e.message) from e

  def get_attachment(self,args):
    at_db = None
    try:
      at_db = self.db.get_attachment({"id": args['id']})
    except GulagDBException as e:
      raise GulagException(whoami(self) + e.message) from e
    if 'data' not in args:
      return at_db

  def get_uris(self):
    # https://stackoverflow.com/questions/1792366/extract-urls-out-of-email-in-python
    return True

  def rspamd_http2imap(self,args):
    mailbox = None
    try:
      mailbox = self.db.get_mailbox(args['mailbox_id'])
    except GulagDBException as e:
      raise GulagException(whoami(self) + e.message) from e
    # check if the request comes really from rspamd´s metadata_exporter
    # default metadata_header prefix 'X-Rspamd' will be expected
    if('X-Rspamd-From' not in args['req_headers']):
      err = str(whoami(self) 
        + "Missing Rspamd-specific request header X-Rspamd-From!"
      )
      logging.error(err)
      raise GulagException(err)
    # Prepend Gulag-specific headers to rejected mail 
    # before pushing into quarantine mailbox
    msg = None
    try:
      if('X-Rspamd-From' not in args['req_headers']):
        err = str(whoami(self) 
          + "Missing Rspamd-specific request header X-Rspamd-From!"
        )
        logging.error(err)
        raise GulagException(err)
      if('X-Rspamd-Rcpt' not in args['req_headers']):
        err = str(whoami(self) 
          + "Missing Rspamd-specific request header X-Rspamd-Rcpt!"
        )
        logging.error(err)
        raise GulagException(err)
      if('X-Rspamd-Symbols' not in args['req_headers']):
        err = str(whoami(self) 
          + "Missing Rspamd-specific request header X-Rspamd-Symbols!"
        )
        logging.error(err)
        raise GulagException(err)
      if('X-Rspamd-Qid' not in args['req_headers']):
        err = str(whoami(self) 
          + "Missing Rspamd-specific request header X-Rspamd-Qid!"
        )
        logging.error(err)
        raise GulagException(err)
      if('rfc822_message' not in args['rfc822_message']):
        err = str(whoami(self) 
          + "Missing rfc822_message!"
        )
        logging.error(err)
        raise GulagException(err)
      # all mandatory request headers and body are present
      rcpts_hdr = ""
      for rcpt in json.loads(str(args['req_headers']['X-Rspamd-Rcpt'])):
        if(len(rcpts_hdr) > 0):
          rcpts_hdr += "," + rcpt
        else:
          rcpts_hdr = rcpt 
      msg = "Return-Path: <" + args['req_headers']['X-Rspamd-From'] + ">\r\n"
      msg += "Received: from rspamd_http2imap relay by gulag-mailbox " 
      msg += args['mailbox_id'] + "\r\n"
      msg += "X-Envelope-To-Blocked: " + rcpts_hdr + "\r\n"
      msg += "X-Spam-Status: " + args['req_headers']['X-Rspamd-Symbols'] + "\r\n"
      msg += "X-Spam-QID: " + args['req_headers']['X-Rspamd-Qid'] + "\r\n"
      # append original mail
      msg += args['rfc822_message']
    except GulagException as e:
      raise GulagException(e.message) from e
    except:
      raise GulagException(whoami(self) + str(sys.exc_info()))
    imap_mb = None
    try:
      imap_mb = IMAPmailbox(mailbox)
      imap_mb.append_message(msg)
    except IMAPmailboxException as e:
      raise GulagException(whoami(self) + e.message) from e

