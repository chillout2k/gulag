import json, sys,os,logging,re,magic
import email,email.header,email.message
from GulagDB import (
  GulagDB,GulagDBException,GulagDBNotFoundException,GulagDBBadInputException
)
from GulagMailbox import IMAPmailbox,IMAPmailboxException
from GulagMailrelay import GulagMailrelay,GulagMailrelayException
from GulagUtils import whoami,extract_uris,extract_fqdn
import ssdeep, hashlib

class GulagException(Exception):
  message = None
  def __init__(self,message):
    self.message = message

class GulagNotFoundException(Exception):
  message = None
  def __init__(self,message):
    self.message = message

class GulagBadInputException(Exception):
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
      # TODO: Exception handling
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
      self.fields['Mailrelays'] = self.db.get_fields('Mailrelays')
      self.fields['QuarMails'] = self.db.get_fields('QuarMails')
      self.fields['Attachments'] = self.db.get_fields('Attachments')
      self.fields['URIs'] = self.db.get_fields('URIs')
    except GulagDBException as e:
      logging.warning(whoami(self) + e.message)
      raise GulagException(whoami(self) + e.message) from e

  def check_filters(self,fields_target,filters):
    if fields_target not in self.fields:
      raise GulagBadInputException(
        whoami(self) + fields_target + " not found in Gulag.fields!"
      )
    if 'rules' not in filters:
      raise GulagBadInputException(whoami(self) +
        "no 'rules' found in filters!"
      )
    if 'groupOp' not in filters:
      raise GulagBadInputException(whoami(self) +
        "'groupOp' not found in filters!"
      )
    if filters['groupOp'] != 'AND' and filters['groupOp'] != 'OR':
      raise GulagBadInputException(whoami(self) +
        "invalid 'groupOp': " + filters['groupOp']
      )
    # {"groupOp":"AND","rules":[{"field":"uri_count","op":"eq","data":"3"}]}
    for rule in filters['rules']:
      if(rule['field'] in self.db.vcols):
        continue
      if rule['field'] not in self.fields[fields_target]:
        raise GulagBadInputException(whoami(self) +
          rule['field'] + " is not a valid field of " + fields_target + "!"
        )

  # Iterate through all mailboxes, extract metadata
  # from all unseen mails and pump them into database
  def import_quarmails(self):
    for mailbox in self.db.get_mailboxes():
      imap_mb = None
      messages = []
      try:
        imap_mb = IMAPmailbox(mailbox)
        messages = imap_mb.get_unseen_messages()
      except IMAPmailboxException as e:
        logging.warning(whoami(self) + e.message)
        continue
      for unseen in messages:
        quarmail_ids = []
        attachments = []
        uris = {}
        uid = unseen['imap_uid']
        msg = email.message_from_bytes(unseen['msg'])
        source_id = 'amavis'
        if 'X-Gulag-Source' in msg:
          source_id = email.header.decode_header(msg['X-Gulag-Source'])[0][0]
        r5321_from = email.header.decode_header(msg['Return-Path'])[0][0]
        if(r5321_from is not '<>'):
          r5321_from = r5321_from.replace("<","")
          r5321_from = r5321_from.replace(">","")
        r5321_rcpts = None
        try:
          r5321_rcpts = email.header.decode_header(
            msg['X-Envelope-To-Blocked'])[0][0]
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
          try:
            quarmail_id = self.db.add_quarmail({
              'mx_queue_id': mx_queue_id, 'env_from': r5321_from,
              'env_rcpt': r5321_rcpt, 'hdr_cf': x_spam_status,
              'hdr_from': r5322_from, 'hdr_subject': subject,
              'hdr_msgid': msg_id, 'hdr_date': date, 'cf_meta': 'cf_meta',
              'mailbox_id': 'quarantine@zwackl.de', 'imap_uid': uid,
              'source_id': source_id, 'msg_size': len(msg.as_string()),
              'ssdeep': ssdeep.hash(msg.as_string())
            })
          except GulagDBBadInputException as e:
            logging.warn(whoami(self) + e.message)
            raise GulagBadInputException(whoami(self) + e.message) from e
          except GulagDBException as e:
            logging.warn(whoami(self) + e.message)
            raise GulagException(whoami(self) + e.message) from e
          logging.info(whoami(self) +
            "QuarMail(%s)@Mailbox(%s) imported" % (quarmail_id,mailbox['id'])
          )
          quarmail_ids.append(quarmail_id)
        # End for rcpts
        # Iterate through all MIME-parts and extract all
        # attachments (parts with a name/filename attribute)
        for part in msg.walk():
          if part.get_filename():
            # ist ein Attachment
            filename = email.header.decode_header(part.get_filename())
            if filename[0][1]:
              # filename is encoded
              filename = filename[0][0].decode(filename[0][1])
            else:
              # filename isn´t encoded
              filename = filename[0][0]
            attach_decoded = part.get_payload(decode=True)
            attach_id = self.db.add_attachment({
              'filename': filename,
              'content_type': part.get_content_type(),
              'content_encoding': part['Content-Transfer-Encoding'],
              'magic': magic.from_buffer(attach_decoded),
              'mime_type': magic.from_buffer(attach_decoded, mime=True),
              'sha256': hashlib.sha256(attach_decoded).hexdigest(),
              'ssdeep': ssdeep.hash(attach_decoded),
              'size': len(attach_decoded)
            })
            attachments.append(attach_id)
          # End if part.get_filename()
          # get all URIs
          ctype = part.get_content_type()
          if(ctype == 'text/plain' or ctype == 'text/html'):
            curis = {}
            curis = extract_uris(
              part.get_payload(decode=True).decode("utf-8","replace")
            )
            if(len(curis) > 0):
              uris = {**uris, **curis}
        # End for msg.walk()
        # link message with attachments
        if(len(attachments) > 0):
          for quarmail_id in quarmail_ids:
            for attachment_id in attachments:
              self.db.quarmail2attachment(str(quarmail_id), str(attachment_id))
              logging.info(whoami(self) +
                "Attachment("+str(attachment_id)+")@QuarMail("+
                str(quarmail_id)+") imported"
              )
        # link message with uris
        if(len(uris) > 0):
          for quarmail_id in quarmail_ids:
            for uri in uris:
              try:
                uri_id = self.db.add_uri({
                  "uri": uri,
                  "fqdn": extract_fqdn(uri)
                })
                self.db.quarmail2uri(str(quarmail_id), str(uri_id))
                logging.info(whoami(self) +
                  "URI("+str(uri_id)+")@QuarMail("+str(quarmail_id)+") imported"
                )
              except GulagDBException as e:
                logging.error(whoami(self) + e.message)
      # End for(unseen)
      imap_mb.close()
    # End for get_mailboxes

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
    qms_db = None
    try:
      if 'filters' in args:
        self.check_filters('QuarMails',args['filters'])
      qms_db = self.db.get_quarmails(args)
    except GulagDBBadInputException as e:
      raise GulagBadInputException(whoami(self) + e.message) from e
    except(GulagException,GulagDBException) as e:
      logging.warning(whoami(self) + e.message)
      raise GulagException(whoami(self) + e.message) from e
    if 'rfc822_message' not in args and 'headers' not in args:
      return {
        'quarmails': qms_db,
        'rfc822_messages': {},
        'headers': {}
      }
    # recognize all IMAP mailboxes to read from
    # and store rfc822-messages under it
    mailboxes = {}
    headers = {}
    for qm in qms_db:
      if qm['mailbox_id'] not in mailboxes:
        mailboxes[qm['mailbox_id']] = {}
    # any qm_db with full RFC822 messages from IMAP mailbox
    for mailbox_id in mailboxes:
      try:
        mailbox = self.db.get_mailbox(mailbox_id)
      except GulagDBException as e:
        logging.warning(whoami(self) + e.message)
        raise GulagException(whoami(self) + e.message) from e
      imap_mb = None
      try:
        imap_mb = IMAPmailbox(mailbox)
      except IMAPmailboxException as e:
        logging.warning(whoami(self) + e.message)
        raise GulagException(whoami(self) + e.message) from e
      for qm_db in qms_db:
        if qm_db['imap_uid'] not in mailboxes[mailbox_id]:
          try:
            if 'rfc822_message' in args:
              mailboxes[mailbox_id][qm_db['imap_uid']] = imap_mb.get_message(
                qm_db['imap_uid']
              ).decode("utf-8")
            elif 'headers' in args:
              mailboxes[mailbox_id][qm_db['imap_uid']] = imap_mb.get_headers(
                qm_db['imap_uid']
              ).decode("utf-8")
          except IMAPmailboxException as e:
            logging.warning(whoami(self) + e.message)
            raise GulagException(whoami(self) + e.message) from e
      imap_mb.close()
    # end for mailboxes
    return {
      "quarmails": qms_db,
      "rfc822_messages": mailboxes
    }

  def get_quarmail(self,args):
    qm_db = None
    try:
      qm_db = self.db.get_quarmail({"id": args['quarmail_id']})
    except GulagDBNotFoundException as e:
      raise GulagNotFoundException(whoami(self) + e.message) from e
    except GulagDBException as e:
      logging.warning(whoami(self) + e.message)
      raise GulagException(whoami(self) + e.message) from e
    if 'rfc822_message' not in args and 'headers' not in args:
      return qm_db
    # pull full RFC822 message from IMAP mailbox
    mailbox = None
    try:
      mailbox = self.db.get_mailbox(qm_db['mailbox_id'])
    except GulagDBNotFoundException as e:
      raise GulagNotFoundException(whoami(self) + e.message) from e
    except GulagDBException as e:
      logging.warning(whoami(self) + e.message)
      raise GulagException(whoami(self) + e.message) from e
    imap_mb = None
    try:
      imap_mb = IMAPmailbox(mailbox)
      if 'rfc822_message' in args:
        qm_db['rfc822_message'] = imap_mb.get_message(
          qm_db['imap_uid']
        ).decode("utf-8")
      elif 'headers' in args:
        qm_db['rfc822_message'] = imap_mb.get_headers(
          qm_db['imap_uid']
        )
      imap_mb.close()
      return qm_db
    except IMAPmailboxException as e:
      logging.warning(whoami(self) + e.message)
      raise GulagException(whoami(self) + e.message) from e

  def modify_quarmail(self, quarmail):
    try:
      if 'id' not in quarmail:
        raise GulagBadInputException(whoami(self) + "'id' is mandatory!")
      for field in quarmail:
        if field not in self.fields['QuarMails']:
          raise GulagBadInputException(whoami(self) +
            "Unknown QuarMail field: " + field
          )
      self.db.modify_quarmail(quarmail)
    except GulagDBBadInputException as e:
      raise GulagBadInputException(whoami(self) + e.message) from e
    except GulagDBNotFoundException as e:
      raise GulagNotFoundException(whoami(self) + e.message) from e
    except GulagDBException as e:
      logging.warning(whoami(self) + e.message)
      raise GulagException(whoami(self) + e.message) from e

  def delete_quarmail(self, args):
    qm_db = None
    try:
      qm_db = self.db.get_quarmail({"id": args['quarmail_id']})
    except GulagDBNotFoundException as e:
      raise GulagNotFoundException(whoami(self) + e.message) from e
    except GulagDBException as e:
      logging.warning(whoami(self) + e.message)
      raise GulagException(whoami(self) + e.message) from e
    mailbox = None
    try:
      mailbox = self.db.get_mailbox(qm_db['mailbox_id'])
    except GulagDBNotFoundException as e:
      raise GulagNotFoundException(whoami(self) + e.message) from e
    except GulagDBException as e:
      logging.warning(whoami(self) + e.message)
      raise GulagException(whoami(self) + e.message) from e
    # Delete QuarMail from IMAP mailbox
    imap_mb = None
    try:
      imap_mb = IMAPmailbox(mailbox)
      imap_mb.delete_message(qm_db['imap_uid'])
    except IMAPmailboxException as e:
      logging.warning(whoami(self) + e.message)
      raise GulagException(whoami(self) + e.message) from e
    # Try to remove related objects (attachments, uris, ...)
    try:
      self.db.delete_quarmail_attachments(args['quarmail_id'])
    except GulagDBException as e:
      logging.warning(whoami(self) + e.message)
      # No exception, as other quarmails may pointer to one of the attachments as well
    try:
      self.db.delete_quarmail_uris(args['quarmail_id'])
    except GulagDBException as e:
      logging.warning(whoami(self) + e.message)
      # No exception, as other quarmails may pointer to one of the uris as well
    # Finally delete QuarMail from DB
    try:
      self.db.delete_quarmail(args['quarmail_id'])
    except GulagDBException as e:
      logging.warning(whoami(self) + e.message)
      raise GulagException(whoami(self) + e.message) from e
    imap_mb.close()
    return

  def release_quarmail(self,args):
    try:
      quarmail = self.get_quarmail({
        "quarmail_id": args['quarmail_id'],
        "rfc822_message": True
      })
      # the mailbox reference holds the appropriate mailrelay_id
      mailbox_ref = self.db.get_mailbox(quarmail['mailbox_id'])
      mailrelay_ref = self.db.get_mailrelay(mailbox_ref['mailrelay_id'])
      mailrelay = GulagMailrelay(mailrelay_ref)
      mailrelay.release_quarmail(quarmail)
      logging.info(whoami(self) +
        "QuarMail("+quarmail['id']+") released. env_rcpt: "+quarmail['env_rcpt']
      )
      if 'purge' in args:
        self.delete_quarmail({"quarmail_id": args['quarmail_id']})
        logging.info(whoami(self) +
          "QuarMail(" + quarmail['id'] + ") deleted"
        )
    except GulagNotFoundException as e:
      raise GulagNotFoundException(whoami(self) + e.message) from e
    except GulagException as e:
      raise GulagException(whoami(self) + e.message) from e
    except GulagDBNotFoundException as e:
      raise GulagNotFoundException(whoami(self) + e.message) from e
    except GulagMailrelayException as e:
      raise GulagException(whoami(self) + e.message) from e

  def bounce_quarmail(self,args):
    try:
      # get quarmail object with headers from mailbox
      quarmail = self.get_quarmail({
        "quarmail_id": args['quarmail_id'],
        "headers": True
      })
      # the mailbox reference holds the appropriate mailrelay_id
      mailbox_ref = self.db.get_mailbox(quarmail['mailbox_id'])
      mailrelay_ref = self.db.get_mailrelay(mailbox_ref['mailrelay_id'])
      mailrelay = GulagMailrelay(mailrelay_ref)
      mailrelay.bounce_quarmail(quarmail)
      logging.info(whoami(self) +
        "QuarMail("+quarmail['id']+") bounced back to "+quarmail['env_from']
      )
      if 'purge' in args:
        self.delete_quarmail({"quarmail_id": args['quarmail_id']})
        logging.info(whoami(self) +
          "QuarMail(" + quarmail['id'] + ") deleted"
        )
    except GulagNotFoundException as e:
      raise GulagNotFoundException(whoami(self) + e.message) from e
    except GulagException as e:
      raise GulagException(whoami(self) + e.message) from e
    except GulagDBNotFoundException as e:
      raise GulagNotFoundException(whoami(self) + e.message) from e
    except GulagMailrelayException as e:
      raise GulagException(whoami(self) + e.message) from e

  def forward_quarmail(self,args):
    try:
      quarmail = self.get_quarmail({
        "quarmail_id": args['quarmail_id'],
        "rfc822_message": True
      })
      # TODO: send quarmail to args['env_rcpt']
    except GulagNotFoundException as e:
      raise GulagNotFoundException(whoami(self) + e.message) from e
    except GulagException as e:
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
    except GulagDBNotFoundException as e:
      raise GulagNotFoundException(whoami(self) + e.message) from e
    except GulagDBException as e:
      logging.warning(whoami(self) + e.message)
      raise GulagException(whoami(self) + e.message) from e
    if 'data' not in args:
      return qmat_db
    # pull attachment from IMAP mailbox
    mailbox = None
    try:
      mailbox = self.db.get_mailbox(qmat_db['mailbox_id'])
    except GulagDBNotFoundException as e:
      raise GulagNotFoundException(whoami(self) + e.message) from e
    except GulagDBException as e:
      logging.warning(whoami(self) + e.message)
      raise GulagException(whoami(self) + e.message) from e
    imap_mb = None
    try:
      imap_mb = IMAPmailbox(mailbox)
      qmat_db['data'] = imap_mb.get_attachment(
        qmat_db['imap_uid'],qmat_db['filename']
      )
      imap_mb.close
      return qmat_db
    except IMAPmailboxException as e:
      logging.warning(whoami(self) + e.message)
      raise GulagException(whoami(self) + e.message) from e

  def get_attachment(self,args):
    at_db = None
    try:
      at_db = self.db.get_attachment({"id": args['id']})
    except GulagDBNotFoundException as e:
      raise GulagNotFoundException(whoami(self) + e.message) from e
    except GulagDBException as e:
      raise GulagException(whoami(self) + e.message) from e
    if 'data' not in args:
      return at_db
    # pull attachment from IMAP mailbox
    mailbox = None
    try:
      mailbox = self.db.get_mailbox(at_db['mailbox_id'])
    except GulagDBNotFoundException as e:
      raise GulagNotFoundException(whoami(self) + e.message) from e
    except GulagDBException as e:
      logging.warning(whoami(self) + e.message)
      raise GulagException(whoami(self) + e.message) from e
    imap_mb = None
    try:
      imap_mb = IMAPmailbox(mailbox)
      at_db['data'] = imap_mb.get_attachment(
        at_db['imap_uid'],at_db['filename']
      )
      imap_mb.close
      return at_db
    except IMAPmailboxException as e:
      logging.warning(whoami(self) + e.message)
      raise GulagException(whoami(self) + e.message) from e

  def modify_attachment(self, attachment):
    try:
      if 'id' not in attachment:
        raise GulagBadInputException(whoami(self) + "'id' is mandatory!")
      for field in attachment:
        if field not in self.fields['Attachments']:
          raise GulagBadInputException(whoami(self) +
            "Unknown Attachment field: " + field
          )
      self.db.modify_attachment(attachment)
    except GulagDBBadInputException as e:
      raise GulagBadInputException(whoami(self) + e.message) from e
    except GulagDBNotFoundException as e:
      raise GulagNotFoundException(whoami(self) + e.message) from e
    except GulagDBException as e:
      logging.warning(whoami(self) + e.message)
      raise GulagException(whoami(self) + e.message) from e

  def get_quarmail_uris(self,args):
    if('from_rfc822_message' not in args):
      try:
        return self.db.get_quarmail_uris(args['quarmail_id'])
      except GulagDBException as e:
        raise GulagException(whoami(self) + e.message) from e
    # get URIs from email@IMAP
    qm_db = None
    try:
      qm_db = self.db.get_quarmail({"id": args['quarmail_id']})
    except GulagDBNotFoundException as e:
      raise GulagNotFoundException(whoami(self) + e.message) from e
    except GulagDBException as e:
      logging.warning(whoami(self) + e.message)
      raise GulagException(whoami(self) + e.message) from e
    mailbox = None
    try:
      mailbox = self.db.get_mailbox(qm_db['mailbox_id'])
    except GulagDBNotFoundException as e:
      raise GulagNotFoundException(whoami(self) + e.message) from e
    except GulagDBException as e:
      logging.warning(whoami(self) + e.message)
      raise GulagException(whoami(self) + e.message) from e
    imap_mb = None
    try:
      imap_mb = IMAPmailbox(mailbox)
      uris = []
      for part in imap_mb.get_main_parts(qm_db['imap_uid']):
        for uri in extract_uris(part.decode("utf-8")):
          uris.append({
            "uri": uri,
            "fqdn": extract_fqdn(uri)
          })
      imap_mb.close()
      return uris
    except IMAPmailboxException as e:
      logging.warning(whoami(self) + e.message)
      raise GulagException(whoami(self) + e.message) from e

  def get_quarmail_uri(self,args):
    try:
      return self.db.get_quarmail_uri(args['quarmail_id'],args['uri_id'])
    except GulagDBNotFoundException as e:
      raise GulagNotFoundException(whoami(self) + e.message) from e
    except GulagDBException as e:
      raise GulagException(whoami(self) + e.message) from e

  def get_uri(self,uri_id):
    try:
      return self.db.get_uri(uri_id)
    except GulagDBNotFoundException as e:
      raise GulagNotFoundException(whoami(self) + e.message) from e
    except GulagDBException as e:
      raise GulagException(whoami(self) + e.message) from e

  def modify_uri(self, uri):
    try:
      if 'id' not in uri:
        raise GulagBadInputException(whoami(self) + "'id' is mandatory!")
      for field in uri:
        if field not in self.fields['URIs']:
          raise GulagBadInputException(whoami(self) +
            "Unknown URI field: " + field
          )
      self.db.modify_uri(uri)
    except GulagDBBadInputException as e:
      raise GulagBadInputException(whoami(self) + e.message) from e
    except GulagDBNotFoundException as e:
      raise GulagNotFoundException(whoami(self) + e.message) from e
    except GulagDBException as e:
      logging.warning(whoami(self) + e.message)
      raise GulagException(whoami(self) + e.message) from e

  def rspamd2mailbox(self,args):
    mailbox = None
    try:
      mailbox = self.db.get_mailbox(args['mailbox_id'])
    except GulagDBNotFoundException as e:
      raise GulagNotFoundException(whoami(self) + e.message) from e
    except GulagDBException as e:
      raise GulagException(whoami(self) + e.message) from e
    # check if the request comes really from rspamd´s metadata_exporter
    # default metadata_header prefix 'X-Rspamd' will be expected
    if('X-Rspamd-From' not in args['req_headers']):
      err = str(whoami(self)
        + "Missing Rspamd-specific request header X-Rspamd-From!"
      )
      logging.error(err)
      raise GulagBadInputException(err)
    # Prepend Gulag-specific headers to rejected mail
    # before pushing into quarantine mailbox
    msg = None
    if('X-Rspamd-From' not in args['req_headers']):
      err = str(whoami(self) +
        "Missing Rspamd-specific request header X-Rspamd-From!"
      )
      logging.error(err)
      raise GulagBadInputException(err)
    if('X-Rspamd-Rcpt' not in args['req_headers']):
      err = str(whoami(self) +
        "Missing Rspamd-specific request header X-Rspamd-Rcpt!"
      )
      logging.error(err)
      raise GulagBadInputException(err)
    if('X-Rspamd-Symbols' not in args['req_headers']):
      err = str(whoami(self) +
        "Missing Rspamd-specific request header X-Rspamd-Symbols!"
      )
      logging.error(err)
      raise GulagBadInputException(err)
    if('X-Rspamd-Qid' not in args['req_headers']):
      err = str(whoami(self) +
        "Missing Rspamd-specific request header X-Rspamd-Qid!"
      )
      logging.error(err)
      raise GulagBadInputException(err)
    if('rfc822_message' not in args):
      err = str(whoami(self) + "Missing rfc822_message!")
      logging.error(err)
      raise GulagBadInputException(err)
    # all mandatory request headers and body are present
    rcpts_hdr = ""
    rcpts = None
    try:
      rcpts = json.loads(str(args['req_headers']['X-Rspamd-Rcpt']))
    except json.JSONDecodeError as e:
      raise GulagBadInputException(e.msg) from e
    for rcpt in rcpts:
      if(len(rcpts_hdr) > 0):
        rcpts_hdr += "," + rcpt
      else:
        rcpts_hdr = rcpt
    msg = "Return-Path: <" + args['req_headers']['X-Rspamd-From'] + ">\r\n"
    msg += "Received: from Rspamd http2imap relay by gulag-mailbox IMAP: "
    msg += args['mailbox_id'] + "\r\n"
    msg += "X-Envelope-To-Blocked: " + rcpts_hdr + "\r\n"
    msg += "X-Spam-Status: " + args['req_headers']['X-Rspamd-Symbols'] + "\r\n"
    msg += "X-Spam-QID: " + args['req_headers']['X-Rspamd-Qid'] + "\r\n"
    msg += "X-Gulag-Source: rspamd\r\n"
    # append original mail
    msg += args['rfc822_message']
    imap_mb = None
    try:
      imap_mb = IMAPmailbox(mailbox)
      imap_uid = imap_mb.add_message(msg, unseen=True)
      logging.info(whoami(self) + "IMAP_UID: " + str(imap_uid))
      imap_mb.close()
    except IMAPmailboxException as e:
      raise GulagException(whoami(self) + e.message) from e

  def mailradar2mailbox(self,args):
    mailbox = None
    try:
      mailbox = self.db.get_mailbox(args['mailbox_id'])
    except GulagDBNotFoundException as e:
      raise GulagNotFoundException(whoami(self) + e.message) from e
    except GulagDBException as e:
      raise GulagException(whoami(self) + e.message) from e
    # Prepend Gulag-specific headers to rejected mail
    # before pushing into quarantine mailbox
    msg = None
    if('X-Mailradar-From' not in args['req_headers']):
      err = str(whoami(self) +
        "Missing Mailradar-specific request header X-Mailradar-From!"
      )
      logging.error(err)
      raise GulagBadInputException(err)
    if('X-Mailradar-Rcpt' not in args['req_headers']):
      err = str(whoami(self) +
        "Missing Mailradar-specific request header X-Mailradar-Rcpt!"
      )
      logging.error(err)
      raise GulagBadInputException(err)
    #if('X-Rspamd-Symbols' not in args['req_headers']):
    #  err = str(whoami(self) +
    #    "Missing Rspamd-specific request header X-Rspamd-Symbols!"
    #  )
    #  logging.error(err)
    #  raise GulagBadInputException(err)
    if('X-Mailradar-Qid' not in args['req_headers']):
      err = str(whoami(self) +
        "Missing Mailradar-specific request header X-Mailradar-Qid!"
      )
      logging.error(err)
      raise GulagBadInputException(err)
    if('rfc822_message' not in args):
      err = str(whoami(self) + "Missing rfc822_message!")
      logging.error(err)
      raise GulagBadInputException(err)
    # all mandatory request headers and body are present
    rcpts_hdr = ""
    rcpts = None
    try:
      rcpts = json.loads(str(args['req_headers']['X-Mailradar-Rcpt']))
    except json.JSONDecodeError as e:
      raise GulagBadInputException(e.msg) from e
    for rcpt in rcpts:
      if(len(rcpts_hdr) > 0):
        rcpts_hdr += "," + rcpt
      else:
        rcpts_hdr = rcpt
    msg = "Return-Path: <" + args['req_headers']['X-Mailradar-From'] + ">\r\n"
    msg += "Received: from Mailradar http2imap relay by gulag-mailbox IMAP: "
    msg += args['mailbox_id'] + "\r\n"
    msg += "X-Envelope-To-Blocked: " + rcpts_hdr + "\r\n"
#    msg += "X-Spam-Status: " + args['req_headers']['X-Rspamd-Symbols'] + "\r\n"
    msg += "X-Spam-QID: " + args['req_headers']['X-Mailradar-Qid'] + "\r\n"
    msg += "X-Gulag-Source: mailradar\r\n"
    # append original mail
    msg += args['rfc822_message']
    imap_mb = None
    try:
      imap_mb = IMAPmailbox(mailbox)
      imap_uid = imap_mb.add_message(msg, unseen=True)
      logging.info(whoami(self) + "IMAP_UID: " + str(imap_uid))
      imap_mb.close()
    except IMAPmailboxException as e:
      raise GulagException(whoami(self) + e.message) from e
