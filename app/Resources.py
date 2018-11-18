#from flask import request
from flask_restful import Resource, abort, reqparse
from Gulag import GulagException

class GulagResource(Resource):
  gulag = None
  def __init__(self,gulag_object):
    self.gulag = gulag_object
#XXX    self.check_trusted_proxy()
#XXX    self.check_auth()

  def check_trusted_proxy(self):
    remote_ip = request.remote_addr
    if 'trusted_proxies' not in self.gulag.config:
      # Trusted-proxies not configured
      return True
    for proxy in self.gulag.config['trusted_proxies']:
      for trusted_proxy_ip in self.gulag.config['trusted_proxies'][proxy]:
        if(remote_ip == trusted_proxy_ip):
          return True
    abort(403, message="Untrusted client IP-address!")

  def check_auth(self):
    if not 'API-KEY' in request.headers:
      abort(400, message="API-KEY header missing!")
    api_key = request.headers['API-KEY']
    if api_key not in self.gulag.config['api_keys']:
      abort(401, message="NOT AUTHORIZED!")

class ResRoot(GulagResource):
  def get(self):
    return {"resource": "Root :)"}

class ResMailboxes(GulagResource):
  def get(self):
    try:
      return self.gulag.get_mailboxes()
    except GulagException as e:
      abort(500, message=e.message)

class ResMailbox(GulagResource):
  def get(self,id):
    return {"resource": "Mailbox by ID"}

class ResQuarMails(GulagResource):
  def get(self):
    try:
      return self.gulag.get_quarmails()
    except GulagException as e:
      abort(500, message=e.message)

class ResQuarMail(GulagResource):
  def get(self,id):
    return {"resource": "QuarMail by ID"}

class ResAttachments(GulagResource):
  def get(self):
    return {"resource": "Attachments"}

class ResAttachment(GulagResource):
  def get(self,id):
    return {"resource": "Attachment by ID"}

class ResRSPAMDImporter(GulagResource):
  def post(self,mailbox_id):
    try:
      self.gulag.rspamd_http2smtp(mailbox_id)
      # TODO: Response mit Location-Header?
      return {"resource: ": "HTTP2SMTP for RSPAMD"}
    except GulagException as e:
      abort(400, message=e.message)

