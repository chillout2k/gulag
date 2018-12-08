import sys
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

