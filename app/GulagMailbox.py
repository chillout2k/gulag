import imaplib
import email
import email.header
import time

class IMAPmailboxException(Exception):
  message = None
  def __init__(self,message):
    self.message = str(message)

class IMAPmailbox:
  imap_server = None
  imap_user = None
  imap_pass = None
  imap_mailbox = None
  mailbox = None

  def __init__(self, imap_server, imap_user, imap_pass, imap_mailbox):
    self.imap_server = imap_server
    self.imap_user = imap_user
    self.imap_pass = imap_pass
    self.imap_mailbox = imap_mailbox
    try:
      self.mailbox = imaplib.IMAP4(self.imap_server)
      rv, data = self.mailbox.login(self.imap_user, self.imap_pass)
    except imaplib.IMAP4.error as e:
      raise IMAPmailboxException(
        "LOGIN FAILED FOR " + self.imap_user + '@' + self.imap_server
      ) from e
    except ConnectionRefusedError as e:
      raise IMAPmailboxException(
        self.imap_user + ": IMAP server " + self.imap_server + " refused connection"
      ) from e
    
    rv, data = self.mailbox.select(self.imap_mailbox)
    if rv != 'OK':
      raise IMAPmailboxException(
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
        'msg': email.message_from_bytes(data[0][1])
      })
    return results

  def get_message(self,imap_uid):
    rv, data = self.mailbox.uid('FETCH', imap_uid, '(RFC822)')
    if rv != 'OK':
      raise IMAPmailboxException("ERROR getting message: %s", str(imap_uid))
    return email.message_from_bytes(data[0][1])

  def get_attachments(self,imap_uid):
    results = []
    rv, data = self.mailbox.uid('FETCH', imap_uid, '(RFC822)')
    if rv != 'OK':
      raise IMAPmailboxException("ERROR getting message: %s", str(imap_uid))
    msg = email.message_from_bytes(data[0][1])
    for part in msg.walk():
      if part.get_filename():
        # let´s define parts with filename as attachments
        filename = email.header.decode_header(part.get_filename())
        if filename[0][1]:
          # Encoded -> decode
          filename = filename[0][0].decode(filename[0][1])
        else:
          # not encoded
          filename = filename[0][0]
        results.append({
          'filename': filename,
          'content-type': part.get_content_type(), 
          'content': part.get_payload(decode=True)
        })
      # End if part.get_filename()
    return results

  def append_message(self,message):
    rv, data = self.mailbox.append(
      self.imap_mailbox,
      'UNSEEN',
      imaplib.Time2Internaldate(time.time()),
      str(message).encode('utf-8')
    )
    if rv != 'OK':
      raise IMAPmailboxException("ERROR appending message!")

