from smtplib import (
  SMTP,SMTPRecipientsRefused,SMTPHeloError,SMTPSenderRefused, SMTPDataError,
  SMTPNotSupportedError
 )
import email
from email.message import EmailMessage
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email.mime.text import MIMEText
from email.mime.message import MIMEMessage
from email.utils import formatdate
from email import policy
import time,sys
from GulagUtils import whoami

class GulagMailrelayException(Exception):
  message = None
  def __init__(self,message):
    self.message = str(message)

class GulagMailrelay:
  id = None
  smtp_server = None
  smtp_port = None
  smtp_security = None
  smtp_user = None
  smtp_pass = None
  mailrelay = None

  def __init__(self,mailrelay_ref):
    self.id = mailrelay_ref['id']
    self.smtp_server = mailrelay_ref['smtp_server']
    self.smtp_port = mailrelay_ref['smtp_port']
    self.smtp_security = mailrelay_ref['smtp_security']
    self.smtp_user = mailrelay_ref['smtp_user']
    self.smtp_pass = mailrelay_ref['smtp_pass']

  def release_quarmail(self,quarmail):
    try:
      # FIXME: SMTP transport security and authentication!
      with SMTP(host=self.smtp_server,port=self.smtp_port) as self.mailrelay:
        self.mailrelay.sendmail(
          quarmail['env_from'],
          quarmail['env_rcpt'],
          quarmail['rfc822_message']
        )
        self.mailrelay.quit()
    except (SMTPRecipientsRefused,SMTPHeloError,SMTPSenderRefused,
            SMTPDataError,SMTPNotSupportedError) as e:
      raise GulagMailrelayException(whoami(self) + e.message) from e
    except TimeoutError as e:
      raise GulagMailrelayException(whoami(self) + e.message) from e
    except ConnectionRefusedError as e:
      raise GulagMailrelayException(whoami(self) + e.strerror) from e

  def bounce_quarmail(self,quarmail):
    msg = None
    if quarmail['env_from'] == '<>':
      raise GulagMailrelayException(whoami(self) +
        "Unwilling to double-bounce QuarMail("+quarmail['id']+")!"
    )
    try:
      # multipart/report
      msg = MIMEMultipart('report', boundary='GULAG-DSN-BOUNDARY')
      msg['Subject'] = 'Undelivered Mail Returned to Sender'
      msg['From'] = 'GULAG MAILER-DAEMON (Mail Quarantine System) <>'
      msg['To'] = quarmail['env_from']
      msg['Auto-Submitted'] = 'auto-replied'
      msg['Message-ID'] = '<TODO-something-random@kiss.ass>'
      msg['Date'] = formatdate()
      msg.preamble = 'This is a MIME-encapsulated message.\r\n'
      # text/plain
      nt = "This is the mail system at host TODO-GULAG-QUARANTINE.HOST\r\n\r\n"
      nt += "I'm sorry to have to inform you that your message could not\r\n"
      nt += "be delivered to one or more recipients. It's headers are attached "
      nt += "below.\r\n\r\n"
      nt += "For further assistance, please send mail to postmaster.\r\n\r\n"
      nt += "If you do so, please include this problem report. You can\r\n"
      nt += "delete your own text from the attached returned message.\r\n\r\n"
      nt += "<"+quarmail['env_rcpt']+">: host GULAG-QUARANTINE.HOST said: 550\r\n"
      nt += "Requested action not taken: DANGEROUS\r\n"
      msg.attach(MIMEText(nt, 'plain'))
      # message/delivery-status
      dr = "Reporting-MTA: dns; GULAG-QUARANTINE.HOST\r\n"
      dr += "Queue-ID: "+quarmail['mx_queue_id']+"\r\n"
      dr += "Sender: rfc822; "+quarmail['env_from']+"\r\n"
      dr += "Arrival-Date: "+quarmail['ctime']
      dr += "Final-Recipient: rfc822;"+quarmail['env_rcpt']+"\r\n\r\n"
      dr += "Original-Recipient: rfc822;"+quarmail['env_rcpt']+"\r\n"
      dr += "Action: failed\r\n"
      dr += "Status: 5.0.0\r\n"
      dr += "Remote-MTA: dns; GULAG-QUARANTINE.HOST\r\n"
      dr += "Diagnostic-Code: smtp; 550 Requested action not taken: DANGEROUS\r\n"
      dr_part = MIMEBase('message','delivery-status')
      dr_part.set_payload(dr)
      #dr_part.policy = policy.compat32
      #msg.attach(dr_part)
      # message/rfc822
      msg.attach(MIMEMessage(
        email.message_from_bytes(quarmail['rfc822_message'])
      ))
    except:
      raise GulagMailrelayException(whoami(self) + str(sys.exc_info()))
    try:
      # FIXME: SMTP transport security and authentication!
      with SMTP(host=self.smtp_server,port=self.smtp_port) as self.mailrelay:
        self.mailrelay.sendmail('<>', quarmail['env_from'], msg.as_string())
        self.mailrelay.quit()
        return True
    except (SMTPRecipientsRefused,SMTPHeloError,SMTPSenderRefused,
            SMTPDataError,SMTPNotSupportedError) as e:
      raise GulagMailrelayException(whoami(self) + e.message) from e
    except TimeoutError as e:
      raise GulagMailrelayException(whoami(self) + e.message) from e
    except ConnectionRefusedError as e:
      raise GulagMailrelayException(whoami(self) + e.strerror) from e
