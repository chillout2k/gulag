import re

class MailrelayException(Exception):
  message = None
  def __init__(self,message):
    self.message = message

class Mailrelay:
  id = None
  smtp_server = None
  smtp_port = None
  smtp_security = None
  smtp_user = None
  smtp_pass = None
  comment = None
  href = None

  def __init__(self,mr_ref):
    if 'id' not in mr_ref:
      raise MailrelayException("'id' is mandatory!")
    self.id = mr_ref['id']
    if 'smtp_server' not in mr_ref:
      raise MailrelayException("'smtp_server' is mandatory!")
    self.smtp_server = mr_ref['smtp_server']
    if 'smtp_security' in mr_ref:
      if re.match("^(plain|starttls|tls)$",mr_ref['smtp_security']) is not None:
        self.smtp_security = mr_ref['smtp_security']
      else:
        raise MailrelayException('smtp_security: {} is invalid! '+
          'Valid values: plain,starttls,tls'.format(mr_ref['smtp_security'])
        )
    else:
      raise MailrelayException("'smtp_security' is a mandatory!")
    if 'smtp_port' in mr_ref:
      self.smtp_port = mr_ref['smtp_port']
    if 'smtp_user' not in mr_ref:
      raise MailrelayException("'smtp_user' is mandatory!")
    self.smtp_user = mr_ref['smtp_user']
    if 'smtp_pass' not in mr_ref:
      raise MailrelayException("'smtp_pass' is mandatory!")
    self.smtp_pass = mr_ref['smtp_pass']
    if 'comment' in mr_ref:
      self.comment = mr_ref['comment']
    if 'href' in mr_ref:
      self.href = mr_ref['href']

class MailboxException(Exception):
  message = None
  def __init__(self,message):
    self.message = message

class Mailbox:
  id = None
  imap_server = None
  imap_port = None
  imap_security = None
  imap_user = None
  imap_pass = None
  imap_mailbox = None
  imap_mailbox_fp = None
  imap_separator = None
  mailrelay_id = None
  comment = None
  href = None

  def __init__(self,mb_ref):
    if 'id' not in mb_ref:
      raise MailboxException("'id' is mandatory!")
    self.id = mb_ref['id']
    if 'name' not in mb_ref:
      raise MailboxException("'name' is mandatory!")
    self.name = mb_ref['name']
    if 'imap_server' not in mb_ref:
      raise MailboxException("'imap_server' is mandatory!")
    self.imap_server = mb_ref['imap_server']
    if 'imap_security' in mb_ref:
      if re.match("^(plain|starttls|tls)$", mb_ref['imap_security']) is not None:
        self.imap_security = mb_ref['imap_security']
      else:
        raise MailboxException('imap_security: {} is invalid! '+
          'Valid values: plain,starttls,tls'.format(mb_ref['imap_security'])
        )
    else:
      raise MailboxException("'imap_security' is a mandatory!")
    if 'imap_port' in mb_ref:
      self.imap_port = mb_ref['imap_port']
    if 'imap_user' not in mb_ref:
      raise MailboxException("'imap_user' is mandatory!")
    self.imap_user = mb_ref['imap_user']
    if 'imap_pass' not in mb_ref:
      raise MailboxException("'imap_pass' is mandatory!")
    self.imap_pass = mb_ref['imap_pass']
    if 'imap_mailbox' not in mb_ref:
      raise MailboxException("'imap_mailbox' is mandatory!")
    self.imap_mailbox = mb_ref['imap_mailbox']
    if 'imap_mailbox_fp' not in mb_ref:
      raise MailboxException("'imap_mailbox_fp' is mandatory!")
    self.imap_mailbox_fp = mb_ref['imap_mailbox_fp']
    if 'imap_separator' not in mb_ref:
      raise MailboxException("'imap_separator' is mandatory!")
    self.imap_seperator = mb_ref['imap_separator']
    if 'mailrelay_id' not in mb_ref:
      raise MailboxException("'mailrelay_id' is mandatory!")
    self.mailrelay_id = mb_ref['mailrelay_id']
    if 'comment' in mb_ref:
      self.comment = mb_ref['comment']
    if 'href' in mb_ref:
      self.href = mb_ref['href']

class QuarMailException(Exception):
  message = None
  def __init__(self,message):
    self.message = message

class QuarMail:
  id = None
  ctime = None
  mx_queue_id = None
  env_from = None
  env_rcpt = None
  hdr_cf = None
  hdr_from = None
  hdr_subject = None
  hdr_msgid = None
  hdr_date = None
  cf_meta = None
  mailbox_id = None
  imap_uid = None
  msg_size = None
  href = None
  attach_count = None
  uri_count = None
  source_id = None
  ssdeep = None
  release_time = None

  def __init__(self,qm_ref):
    if 'id' not in qm_ref:
      raise QuarMailException("'id' is mandatory!")
    self.id = qm_ref['id']
    if 'ctime' not in qm_ref:
      raise QuarMailException("'ctime' is mandatory!")
    self.ctime = qm_ref['ctime']
    if 'mx_queue_id' not in qm_ref:
      raise QuarMailException("'mx_queue_id' is mandatory!")
    self.mx_queue_id = qm_ref['mx_queue_id']
    if 'env_from' not in qm_ref:
      raise QuarMailException("'env_from' is mandatory!")
    self.env_from = qm_ref['env_from']
    if 'env_rcpt' not in qm_ref:
      raise QuarMailException("'env_rcpt' is mandatory!")
    self.env_rcpt = qm_ref['env_rcpt']
    if 'hdr_cf' in qm_ref:
      self.hdr_cf = qm_ref['hdr_cf']
    if 'hdr_from' in qm_ref:
      self.hdr_from = qm_ref['hdr_from']
    if 'hdr_subject' in qm_ref:
      self.hdr_subject = qm_ref['hdr_subject']
    if 'hdr_msgid' in qm_ref:
      self.hdr_msgid = qm_ref['hdr_msgid']
    if 'hdr_date' in qm_ref:
      self.hdr_date = qm_ref['hdr_date']
    if 'cf_meta' in qm_ref:
      self.cf_meta = qm_ref['cf_meta']
    if 'mailbox_id' not in qm_ref:
      raise QuarMailException("'mailbox_id' is mandatory!")
    self.mailbox_id = qm_ref['mailbox_id']
    if 'imap_uid' not in qm_ref:
      raise QuarMailException("'imap_uid' is mandatory!")
    self.imap_uid = qm_ref['imap_uid']
    if 'msg_size' not in qm_ref:
      raise QuarMailException("'msg_size' is mandatory!")
    self.msg_size = qm_ref['msg_size']
    if 'href' in qm_ref:
      self.href = qm_ref['href']
    if 'attach_count' in qm_ref:
      self.attach_count = qm_ref['attach_count']
    if 'uri_count' in qm_ref:
      self.uri_count = qm_ref['uri_count']
    if 'source_id' not in qm_ref:
      raise QuarMailException("'source_id' is mandatory!")
    self.source_id = qm_ref['source_id']
    if 'ssdeep' not in qm_ref:
      raise QuarMailException("'ssdeep' is mandatory!")
    self.ssdeep = qm_ref['ssdeep']
    if 'release_time' not in qm_ref:
      raise QuarMailException("'release_time' is mandatory!")

class AttachmentException(Exception):
  message = None
  def __init__(self,message):
    self.message = message

class Attachment:
  id = None
  filename = None
  content_type = None
  content_encoding = None
  magic = None
  mime_type = None
  comment = None
  mailbox_id = None
  imap_uid = None
  size = None
  sha256 = None
  ssdeep = None
  sandbox_results = None
  href = None

  def __init__(self,at_ref):
    if 'id' not in at_ref:
      raise AttachmentException("'id' is mandatory!")
    self.id = at_ref['id']
    if 'filename' not in at_ref:
      raise AttachmentException("'filename' is mandatory!")
    self.filename = at_ref['filename']
    if 'content_type' not in at_ref:
      raise AttachmentException("'content_type' is mandatory!")
    self.content_type = at_ref['content_type']
    if 'content_encoding' in at_ref:
      self.content_encoding = at_ref['content_encoding']
    if 'magic' not in at_ref:
      raise AttachmentException("'magic' is mandatory!")
    self.magic = at_ref['magic']
    if 'mime_type' not in at_ref:
      raise AttachmentException("'mime_type' is mandatory!")
    self.mime_type = at_ref['mime_type']
    if 'comment' in at_ref:
      self.comment = at_ref['comment']
    if 'mailbox_id' not in at_ref:
      raise AttachmentException("'mailbox_id' is mandatory!")
    self.mailbox_id = at_ref['mailbox_id']
    if 'imap_uid' not in at_ref:
      raise AttachmentException("'imap_uid' is mandatory!")
    self.imap_uid = at_ref['imap_uid']
    if 'size' not in at_ref:
      raise AttachmentException("'size' is mandatory!")
    if 'sha256' not in at_ref:
      raise AttachmentException("'sha256' is mandatory!")
    self.sha256 = at_ref['sha256']
    if 'ssdeep' not in at_ref:
      raise AttachmentException("'ssdeep' is mandatory!")
    self.ssdeep = at_ref['ssdeep']
    if 'sandbox_results' in at_ref:
      self.sandbox_results = at_ref['sandbox_results']
    if 'href' in at_ref:
      self.href = at_ref['href']

class URIException(Exception):
  message = None
  def __init__(self,message):
    self.message = message

class URI:
  id = None
  uri = None
  fqdn = None
  sandbox_results = None
  href = None

  def __init__(self,uri_ref):
    if 'id' not in uri_ref:
      raise URIException("'id' is mandatory!")
    self.id = uri_ref['id']
    if 'uri' not in uri_ref:
      raise URIException("'uri' is mandatory!")
    self.uri = uri_ref['uri']
    if 'fqdn' not in uri_ref:
      raise URIException("'fqdn' is mandatory!")
    self.fqdn = uri_ref['fqdn']
    if 'sandbox_results' in uri_ref:
      self.sandbox_results = uri_ref['sandbox_results']
    if 'href' in uri_ref:
      self.href = uri_ref['href']
