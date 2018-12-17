import sys,re,urllib
from urllib.parse import urlparse
from smtplib import SMTP

def whoami(obj):
  return type(obj).__name__ + "::" + sys._getframe(1).f_code.co_name + "(): "

def send_mail(args):
  try:
  # FIXME: SMTP transport security and authentication!
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

def extract_uris(input_text):
  uris = {}
  uri_pattern = r'(https?:\/\/[^\s<>"]+)'
  suburi_pattern = r'^.+(https?:\/\/[^\s<>"]+)'
  for m in re.finditer(uri_pattern, input_text):
    uri = urllib.parse.unquote(m.group(0))
    uris[uri] = {}
    # extract sub-URIs (google redirector: https://www.google.de/url?sa=t&url=...)
    for m2 in re.finditer(suburi_pattern, uri):
      suburi = urllib.parse.unquote(m2.group(1))
      uris[suburi] = {"suburi": True}
  return uris

def extract_fqdn(uri):
  puri = None
  try:
    puri = urlparse(uri)
    return puri.hostname
  except ValueError as e:
    return None
