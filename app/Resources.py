from flask import request, Response
from flask_restful import Resource, abort, reqparse
import json
from Gulag import (
  GulagException,GulagNotFoundException,GulagBadInputException
)

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
    args = request.args.to_dict()
    if 'filters' in args:
      try:
        args['filters'] = json.loads(args['filters'])
      except json.JSONDecodeError as e:
        abort(400, message="Invalid filters: " + e.msg)
    try:
      return self.gulag.get_quarmails(args)
    except GulagBadInputException as e:
      abort(400, message=e.message)
    except GulagException as e:
      abort(500, message=e.message)

class ResQuarMail(GulagResource):
  def get(self,quarmail_id):
    args = {"quarmail_id": quarmail_id}
    try:
      if(request.args.get('rfc822_message')):
        args['rfc822_message'] = True
      return self.gulag.get_quarmail(args)
    except GulagNotFoundException as e:
      abort(404, message=e.message)
    except GulagException as e:
      abort(500, message=e.message)
  def delete(self,quarmail_id):
    args = {"quarmail_id": quarmail_id}
    try:
      self.gulag.delete_quarmail(args)
      return Response(response=None,status=202,mimetype=None)
    except GulagNotFoundException as e:
      abort(404, message=e.message)
    except GulagException as e:
      abort(500, message=e.message)

class ResQuarMailAttachments(GulagResource):
  def get(self,quarmail_id):
    args = {"quarmail_id": quarmail_id}
    if(request.args.get('data')):
      args['data'] = True
    try:
      return self.gulag.get_quarmail_attachments(args)
    except GulagException as e:
      abort(500, message=e.message)

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
      abort(404, message=e.message)
    except GulagException as e:
      abort(500, message=e.message)

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
      abort(500, message=e.message)

class ResQuarMailURI(GulagResource):
  def get(self,quarmail_id,uri_id):
    args = {
      "quarmail_id": quarmail_id,
      "uri_id": uri_id
    }
    try:
      return self.gulag.get_quarmail_uri(args)
    except GulagNotFoundException as e:
      abort(404, message=e.message)
    except GulagException as e:
      abort(500, message=e.message)

class ResAttachments(GulagResource):
  def get(self):
    return {"resource": "Attachments"}

class ResAttachment(GulagResource):
  def get(self,attachment_id):
    args = {"id": attachment_id}
    try:
      return self.gulag.get_attachment(args)
    except GulagNotFoundException as e:
      abort(404, message=e.message)
    except GulagException as e:
      abort(500, message=e.message)

class ResRSPAMDImporter(GulagResource):
  def post(self,mailbox_id):
    try:
      self.gulag.rspamd_http2imap({
        "mailbox_id": mailbox_id,
        "req_headers": request.headers,
        "rfc822_message": request.get_data(as_text=True)
      })
      return {}
    #  response = Response(
    #    response=json.dumps(resp),
    #    status=201,
    #    mimetype='application/json',
    #    headers=Headers([
    #      ('Location', 'https://invalid.local/api/v1/blablabla/123')
    #    ])
    #  )
    #  return response
    except GulagException as e:
      abort(500, message=e.message)
