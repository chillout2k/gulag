from flask import request, Response
from flask_restful import Resource, abort, reqparse
import json
from Gulag import (
  GulagException,GulagNotFoundException,GulagBadInputException
)
from GulagUtils import whoami

class GulagResource(Resource):
  gulag = None
  def __init__(self,gulag_object):
    self.gulag = gulag_object
#XXX    self.check_trusted_proxy()
#XXX    self.check_auth()
    self.check_max_body_size()

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

  def check_max_body_size(self):
    body_len = len(request.get_data(as_text=True))
    if(body_len > self.gulag.config['dos_protection']['max_body_bytes']):
      raise GulagBadInputException(whoami(self) +
        "Request exceedes maximum body size (" +
        self.gulag.config['dos_protection']['max_body_bytes'] + " bytes)!"
      )

class ResRoot(GulagResource):
  def get(self):
    return {"resource": "Root :)"}

class ResMailboxes(GulagResource):
  def get(self):
    try:
      return self.gulag.get_mailboxes()
    except GulagException as e:
      abort(500, message=whoami(self)+e.message)

class ResMailbox(GulagResource):
  def get(self,id):
    return {"resource": "Mailbox by ID"}

class ResQuarMails(GulagResource):
  def get(self):
    args = request.args.to_dict()
    if 'filters' in args:
      try:
        args['filters'] = json.loads(args['filters'])
      except json.JSONDecodeError as e:
        abort(400, message="Invalid filters: " + e.msg)
    try:
      return self.gulag.get_quarmails(args)
    except GulagBadInputException as e:
      abort(400, message=whoami(self)+e.message)
    except GulagException as e:
      abort(500, message=whoami(self)+e.message)

class ResQuarMail(GulagResource):
  def get(self,quarmail_id):
    args = {"quarmail_id": quarmail_id}
    try:
      if(request.args.get('rfc822_message')):
        args['rfc822_message'] = True
      return self.gulag.get_quarmail(args)
    except GulagNotFoundException as e:
      abort(404, message=whoami(self)+e.message)
    except GulagException as e:
      abort(500, message=whoami(self)+e.message)
  def patch(self,quarmail_id):
    try:
      args = json.loads(request.get_data(as_text=True))
      args['id'] = quarmail_id
    except json.JSONDecodeError as e:
      abort(400, message=whoami(self) + "Invalid JSON: " + e.msg)
    try:
      self.gulag.modify_quarmail(args)
      return Response(response=None,status=204,mimetype=None)
    except GulagBadInputException as e:
      abort(400, message=whoami(self)+e.message)
    except GulagNotFoundException as e:
      abort(404, message=whoami(self)+e.message)
    except GulagException as e:
      abort(500, message=whoami(self)+e.message)
  def delete(self,quarmail_id):
    args = {"quarmail_id": quarmail_id}
    try:
      self.gulag.delete_quarmail(args)
      return Response(response=None,status=202,mimetype=None)
    except GulagNotFoundException as e:
      abort(404, message=whoami(self)+e.message)
    except GulagException as e:
      abort(500, message=whoami(self)+e.message)

class ResQuarMailRelease(GulagResource):
  def post(self,quarmail_id):
    args = {"quarmail_id": quarmail_id}
    if(request.args.get('purge')):
      args['purge'] = True
    try:
      return self.gulag.release_quarmail(args)
    except GulagNotFoundException as e:
      abort(404, message=whoami(self)+e.message)
    except GulagException as e:
      abort(500, message=whoami(self)+e.message)

class ResQuarMailBounce(GulagResource):
  def post(self,quarmail_id):
    args = {"quarmail_id": quarmail_id}
    if(request.args.get('purge')):
      args['purge'] = True
    try:
      return self.gulag.bounce_quarmail(args)
    except GulagNotFoundException as e:
      abort(404, message=whoami(self)+e.message)
    except GulagException as e:
      abort(500, message=whoami(self)+e.message)

class ResQuarMailAttachments(GulagResource):
  def get(self,quarmail_id):
    args = {"quarmail_id": quarmail_id}
    if(request.args.get('data')):
      args['data'] = True
    try:
      return self.gulag.get_quarmail_attachments(args)
    except GulagException as e:
      abort(500, message=whoami(self)+e.message)

class ResQuarMailAttachment(GulagResource):
  def get(self,quarmail_id,attachment_id):
    args = {
      "quarmail_id": quarmail_id,
      "attachment_id": attachment_id
    }
    if(request.args.get('data')):
      args['data'] = True
    try:
      return self.gulag.get_quarmail_attachment(args)
    except GulagNotFoundException as e:
      abort(404, message=whoami(self)+e.message)
    except GulagException as e:
      abort(500, message=whoami(self)+e.message)

class ResQuarMailURIs(GulagResource):
  def get(self,quarmail_id):
    args = {
      "quarmail_id": quarmail_id
    }
    if(request.args.get('from_rfc822_message')):
      args['from_rfc822_message'] = True
    try:
      return self.gulag.get_quarmail_uris(args)
    except GulagException as e:
      abort(500, message=whoami(self)+e.message)

class ResQuarMailURI(GulagResource):
  def get(self,quarmail_id,uri_id):
    args = {
      "quarmail_id": quarmail_id,
      "uri_id": uri_id
    }
    try:
      return self.gulag.get_quarmail_uri(args)
    except GulagNotFoundException as e:
      abort(404, message=whoami(self)+e.message)
    except GulagException as e:
      abort(500, message=whoami(self)+e.message)

class ResAttachments(GulagResource):
  def get(self):
    return {"resource": "Attachments"}

class ResAttachment(GulagResource):
  def get(self,attachment_id):
    args = {"id": attachment_id}
    try:
      return self.gulag.get_attachment(args)
    except GulagNotFoundException as e:
      abort(404, message=whoami(self)+e.message)
    except GulagException as e:
      abort(500, message=whoami(self)+e.message)
  def patch(self,attachment_id):
    try:
      args = json.loads(request.get_data(as_text=True))
      args['id'] = attachment_id
    except json.JSONDecodeError as e:
      abort(400, message=whoami(self) + "Invalid JSON: " + e.msg)
    try:
      self.gulag.modify_attachment(args)
      return Response(response=None,status=204,mimetype=None)
    except GulagBadInputException as e:
      abort(400, message=whoami(self)+e.message)
    except GulagNotFoundException as e:
      abort(404, message=whoami(self)+e.message)
    except GulagException as e:
      abort(500, message=whoami(self)+e.message)

class ResURI(GulagResource):
  def get(self,uri_id):
    args = {"id": uri_id}
    try:
      return self.gulag.get_uri(args)
    except GulagNotFoundException as e:
      abort(404, message=whoami(self)+e.message)
    except GulagException as e:
      abort(500, message=whoami(self)+e.message)
  def patch(self,uri_id):
    try:
      args = json.loads(request.get_data(as_text=True))
      args['id'] = uri_id
    except json.JSONDecodeError as e:
      abort(400, message=whoami(self) + "Invalid JSON: " + e.msg)
    try:
      self.gulag.modify_uri(args)
      return Response(response=None,status=204,mimetype=None)
    except GulagBadInputException as e:
      abort(400, message=whoami(self)+e.message)
    except GulagNotFoundException as e:
      abort(404, message=whoami(self)+e.message)
    except GulagException as e:
      abort(500, message=whoami(self)+e.message)

class ResRspamd2Mailbox(GulagResource):
  def post(self,mailbox_id):
    try:
      self.gulag.rspamd2mailbox({
        "mailbox_id": mailbox_id,
        "req_headers": request.headers,
        "rfc822_message": request.get_data(as_text=True)
      })
      return {}
    except GulagNotFoundException as e:
      abort(404, message=whoami(self)+e.message)
    except GulagBadInputException as e:
      abort(400, message=whoami(self)+e.message)
    except GulagException as e:
      abort(500, message=whoami(self)+e.message)

class ResMailradar2Mailbox(GulagResource):
  def post(self,mailbox_id):
    try:
      self.gulag.mailradar2mailbox({
        "mailbox_id": mailbox_id,
        "req_headers": request.headers,
        "rfc822_message": request.get_data(as_text=True)
      })
      return {}
    except GulagNotFoundException as e:
      abort(404, message=whoami(self)+e.message)
    except GulagBadInputException as e:
      abort(400, message=whoami(self)+e.message)
    except GulagException as e:
      abort(500, message=whoami(self)+e.message)
