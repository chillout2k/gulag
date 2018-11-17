from flask import request
from flask_restful import Resource, abort
import json

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
    return {"resource": "Mailboxes"}

class ResMailbox(GulagResource):
  def get(self,id):
    return {"resource": "Mailbox by ID"}

class ResQuarMails(GulagResource):
  def get(self):
    return {"resource": "QuarMails"}

class ResQuarMail(GulagResource):
  def get(self,id):
    return {"resource": "QuarMail by ID"}

class ResAttachments(GulagResource):
  def get(self):
    return {"resource": "Attachments"}

class ResAttachment(GulagResource):
  def get(self,id):
    return {"resource": "Attachment by ID"}

