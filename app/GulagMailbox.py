import imaplib
import email
import email.header
import time
from GulagUtils import whoami

class IMAPmailboxException(Exception):
  message = None
  def __init__(self,message):
    self.message = str(message)

class IMAPmailbox:
  email_address = None
  imap_server = None
  imap_user = None
  imap_pass = None
  imap_mailbox = None
  mailbox = None

  def __init__(self, mb_ref):
    self.email_address = mb_ref['email_address']
    self.imap_server = mb_ref['imap_server']
    self.imap_user = mb_ref['imap_user']
    self.imap_pass = mb_ref['imap_pass']
    self.imap_mailbox = mb_ref['imap_mailbox']
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

    rv, data = self.mailbox.select(self.imap_mailbox)
    if rv != 'OK':
      raise IMAPmailboxException(whoami(self) +
        "ERROR: Unable to select mailbox: " + self.imap_mailbox
      )

  def close(self):
    self.mailbox.close()
    self.mailbox.logout()

  def get_unseen_messages(self):
    results = []
    rv, data = self.mailbox.uid('SEARCH', 'UNSEEN')
    if rv != 'OK':
      return
    for uid in data[0].split():
      rv, data = self.mailbox.uid('FETCH', uid, '(RFC822)')
      if rv != 'OK':
        print("ERROR getting message", str(uid))
        continue
      results.append({
        'imap_uid': uid,
        'msg': data[0][1]
      })
    return results

  def add_message(self,message):
    rv, data = self.mailbox.append(
      self.imap_mailbox,
      'UNSEEN',
      imaplib.Time2Internaldate(time.time()),
      str(message).encode('utf-8')
    )
    if rv != 'OK':
      raise IMAPmailboxException(whoami(self)+
        "ERROR appending message: " + rv
      )

  def get_message(self,imap_uid):
    rv, data = self.mailbox.uid('FETCH', str(imap_uid), '(RFC822)')
    if rv != 'OK':
      raise IMAPmailboxException(whoami(self) +
        "ERROR getting message: %s", str(imap_uid)
      )
    return data[0][1]

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
        print("C-T-E: " + str(part['Content-Transfer-Encoding']))
        if(part_fn == filename):
          return part.get_payload(decode=False)
      # End if part.get_filename()
    # End msg.walk() loop
    raise IMAPmailboxException(whoami(self) +
      "Attachment ("+ str(filename) +")@IMAP UID(" + str(imap_uid) + ")@"
      + str(self.email_address) + " not found!"
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
      "IMAP_UID(" + str(imap_uid)+")@"+str(self.email_address)+" has no main parts!"
    )
