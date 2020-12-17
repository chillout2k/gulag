import imaplib
import email
import email.header
from email.parser import HeaderParser
import time
import re
from GulagUtils import whoami
import logging


class IMAPmailboxException(Exception):
  message = None
  def __init__(self,message):
    self.message = str(message)

class IMAPmailbox:
  id = None
  imap_server = None
  imap_user = None
  imap_pass = None
  imap_inbox = None
  mailbox = None
  tags = (
    'gulag_quarantined',
    'gulag_released',
    'gulag_bounced'
  )

  def __init__(self, mb_ref):
    self.id = mb_ref['id']
    self.imap_server = mb_ref['imap_server']
    self.imap_user = mb_ref['imap_user']
    self.imap_pass = mb_ref['imap_pass']
    self.imap_inbox = mb_ref['imap_inbox']
    try:
      self.mailbox = imaplib.IMAP4(self.imap_server)
      rv, data = self.mailbox.login(self.imap_user, self.imap_pass)
    except imaplib.IMAP4.error as e:
      raise IMAPmailboxException(whoami(self) +
        "LOGIN FAILED FOR " + self.imap_user + '@' + self.imap_server
      ) from e
    except ConnectionRefusedError as e:
      raise IMAPmailboxException(whoami(self) +
        self.imap_user + ": IMAP server " + self.imap_server + " refused connection"
      ) from e
    rv, data = self.mailbox.select(self.imap_inbox)
    if rv != 'OK':
      raise IMAPmailboxException(whoami(self) +
        "ERROR: Unable to select mailbox: " + self.imap_inbox
      )

  def init_folders(self):
    # Check for all mandatory folders
    mandatory_folders = {
      "failed": False
    }
    rv, data = self.mailbox.list('""', '*')
    if rv != 'OK':
      raise IMAPmailboxException(whoami(self) +
        "ERROR: Unable to list mailbox: " + self.imap_inbox
      )
    for folder in data:
      # (\HasChildren \Trash) "." Trash
      p = re.compile(r'^.+".+" (\S+)$')
      m = p.search(folder.decode())
      name = m.group(1)
      if name == 'failed':
        mandatory_folders['failed'] = True
    # create mandatory folders if needed
    for folder in mandatory_folders:
      if mandatory_folders[folder] == False:
        rv, data = self.mailbox.create(folder)
        if rv != 'OK':
          raise IMAPmailboxException(whoami(self) +
            "ERROR: Unable to create folder: " + folder
          )

  def close(self):
    self.mailbox.close()
    self.mailbox.logout()

  def get_new_messages(self):
    results = []
    search_criteria = str(
      'UNKEYWORD gulag_quarantined'
      + ' UNKEYWORD gulag_released'
      + ' UNKEYWORD gulag_bounced'
    )
    rv, data = self.mailbox.uid('SEARCH', search_criteria)
    if rv != 'OK':
      return
    for uid in data[0].split():
      rv, data = self.mailbox.uid('FETCH', uid, '(RFC822)')
      if rv != 'OK':
        raise IMAPmailboxException(whoami(self) +
          str(data) + ", IMAP_UID: " + str(uid)
        )
      results.append({
        'imap_uid': uid,
        'msg': data[0][1]
      })
    return results

  def add_message(self,message,unseen=False):
    rv, data = self.mailbox.select(self.imap_inbox)
    if rv != 'OK':
      raise IMAPmailboxException(whoami(self) +
        "ERROR: Unable to select mailbox: " + self.imap_inbox
      )
    flags = ''
    if(unseen == True):
      flags = 'UNSEEN'
    rv, data = self.mailbox.append(
      self.imap_inbox,
      flags ,
      imaplib.Time2Internaldate(time.time()),
      str(message).encode('utf-8')
    )
    if rv != 'OK':
      raise IMAPmailboxException(whoami(self)+
        "ERROR appending message: " + rv
      )
    p = re.compile(r'^\[APPENDUID\s+\d+\s+(\d+)\].+$')
    m = p.search(data[0].decode())
    imap_uid = m.group(1)
    return imap_uid

  def get_message(self,imap_uid):
    rv, data = self.mailbox.uid('FETCH', str(imap_uid), '(RFC822)')
    if rv != 'OK':
      raise IMAPmailboxException(whoami(self) +
        "ERROR getting message: %s", str(imap_uid)
      )
    return data[0][1]

  def move_message(self,imap_uid,dest_mbox):
    rv, data = self.mailbox.uid('MOVE', str(imap_uid), dest_mbox)
    if rv != 'OK':
      raise IMAPmailboxException(whoami(self) +
        "ERROR moving message: %s", str(imap_uid)
      )

  def retag_message(self,imap_uid,tag):
    logging.info(whoami(self) + "UID: " + str(imap_uid))
    rv, data = self.mailbox.uid('STORE', str(imap_uid.decode()), 'FLAGS', tag)
    if rv != 'OK':
      raise IMAPmailboxException(whoami(self) +
        "ERROR flagging message for deletion: %s", str(imap_uid)
      )

  def delete_message(self,imap_uid):
    rv, data = self.mailbox.uid('STORE', str(imap_uid), '+FLAGS', '(\\Deleted)')
    if rv != 'OK':
      raise IMAPmailboxException(whoami(self) +
        "ERROR flagging message for deletion: %s", str(imap_uid)
      )
    rv, data = self.mailbox.expunge()
    if rv != 'OK':
      raise IMAPmailboxException(whoami(self) +
        "ERROR expunging mailbox"
      )
    return True

  def get_headers(self,imap_uid):
    rv, data = self.mailbox.uid('FETCH', str(imap_uid), '(BODY[HEADER])')
    if rv != 'OK':
      raise IMAPmailboxException(whoami(self) +
        "ERROR getting headers: %s", str(imap_uid)
      )
    return data[0][1]

  def get_attachment(self,imap_uid,filename):
    msg = email.message_from_bytes(self.get_message(imap_uid))
    for part in msg.walk():
      if part.get_filename():
        # let´s define parts with filename as attachments
        part_fn = email.header.decode_header(part.get_filename())
        if part_fn[0][1]:
          # Encoded -> decode
          part_fn = part_fn[0][0].decode(part_fn[0][1])
        else:
          # not encoded
          part_fn = part_fn[0][0]
        if(part_fn == filename):
          return part.get_payload(decode=False)
      # End if part.get_filename()
    # End msg.walk() loop
    raise IMAPmailboxException(whoami(self) +
      "Attachment ("+ str(filename) +")@IMAP UID(" + str(imap_uid) + ")@"
      + str(self.id) + " not found!"
    )

  def get_main_parts(self,imap_uid):
    msg = email.message_from_bytes(self.get_message(imap_uid))
    mparts = []
    for part in msg.walk():
      ctype = part.get_content_type()
      if(ctype == 'text/plain' or ctype == 'text/html'):
        mparts.append(part.get_payload(decode=True))
    if(len(mparts) > 0):
      return mparts
    raise IMAPmailboxException(whoami(self) +
      "IMAP_UID(" + str(imap_uid)+")@"+str(self.id)+" has no main parts!"
    )
