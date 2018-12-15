import sys,re
from smtplib import SMTP

def whoami(obj):
  return type(obj).__name__ + "::" + sys._getframe(1).f_code.co_name + "(): "

def send_mail(args):
  try:
  # FIXME: SMTP tranaport security and authentication!
  # with SMTP(host=mailbox['smtp_server'],port=mailbox['smtp_port']) as smtp:
  #   try:
  #     smtp.sendmail(
  #       request.headers.get('X-Rspamd-From'),
  #       mailbox_id,
  #       msg
  #     )
  #   except (SMTPRecipientsRefused,SMTPHeloError,SMTPSenderRefused,SMTPDataError) as e:
  #     raise GulagException(str(e)) from e
    print("TODO")
  except TimeoutError as e:
    raise Exception('xyz') from e

def extract_uris(string):
  uris = {}
  uri_pattern = r'(https?:\/\/[^\s<>"]+)'
  for m in re.finditer(uri_pattern, string):
    uris[m.group(0)] = {}
  return uris

def extract_fqdn(uri):
  uri_pattern = r'(https?:\/\/[^\s<>"]+)'
  if(re.match(uri_pattern,uri)):
    m = re.match(r'https?:\/\/([^:\/]+)', uri)
    return m.group(1)
  else:
    return None
