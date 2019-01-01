#!/usr/bin/env python3

import argparse,sys
from flask import Flask
from flask_restful import Api
from Gulag import Gulag,GulagException
from Resources import (ResRoot,ResMailboxes,
  ResQuarMails,ResQuarMail,ResQuarMailAttachments,
  ResQuarMailAttachment,ResAttachments,ResAttachment,
  ResRspamd2Mailbox,ResQuarMailURIs,ResQuarMailURI,
  ResMailradar2Mailbox
)
parser = argparse.ArgumentParser()
parser.add_argument('--config', required=True, help="Path to config file")
args = parser.parse_args()

try:
  try:
    gulag = Gulag(args.config)
  except GulagException as e:
    raise Exception(e.message) from e
  app = Flask(__name__)
  # https://github.com/flask-restful/flask-restful/issues/780#issuecomment-434588559
  app.config['ERROR_404_HELP'] = False
  api = Api(app, catch_all_404s=True)
  api.add_resource(ResRoot,
    '/api/v1/',
    resource_class_kwargs={'gulag_object': gulag}
  )
  api.add_resource(ResMailboxes,
    '/api/v1/mailboxes',
    resource_class_kwargs={'gulag_object': gulag}
  )
  api.add_resource(ResQuarMails,
    '/api/v1/quarmails',
    resource_class_kwargs={'gulag_object': gulag}
  )
  api.add_resource(ResQuarMail,
    '/api/v1/quarmails/<int:quarmail_id>',
    resource_class_kwargs={'gulag_object': gulag}
  )
  api.add_resource(ResQuarMailAttachments,
    '/api/v1/quarmails/<int:quarmail_id>/attachments',
    resource_class_kwargs={'gulag_object': gulag}
  )
  api.add_resource(ResQuarMailAttachment,
    '/api/v1/quarmails/<int:quarmail_id>/attachments/<int:attachment_id>',
    resource_class_kwargs={'gulag_object': gulag}
  )
  api.add_resource(ResQuarMailURIs,
    '/api/v1/quarmails/<int:quarmail_id>/uris',
    resource_class_kwargs={'gulag_object': gulag}
  )
  api.add_resource(ResQuarMailURI,
    '/api/v1/quarmails/<int:quarmail_id>/uris/<int:uri_id>',
    resource_class_kwargs={'gulag_object': gulag}
  )
  api.add_resource(ResAttachments,
    '/api/v1/attachments',
    resource_class_kwargs={'gulag_object': gulag}
  )
  api.add_resource(ResAttachment,
    '/api/v1/attachments/<int:attachment_id>',
    resource_class_kwargs={'gulag_object': gulag}
  )
  api.add_resource(ResRspamd2Mailbox,
    '/api/v1/mailboxes/<string:mailbox_id>/rspamd2mailbox',
    resource_class_kwargs={'gulag_object': gulag}
  )
  api.add_resource(ResMailradar2Mailbox,
    '/api/v1/mailboxes/<string:mailbox_id>/mailradar2mailbox',
    resource_class_kwargs={'gulag_object': gulag}
  )
  if __name__ == '__main__':
    # following code snippet will be intercepted by uwsgi!
    app.run(debug=False,
      host=gulag.config['daemon']['listen_host'],
      port=gulag.config['daemon']['listen_port']
    )
    gulag.db.close()
    sys.exit(0)
except:
  print("MAIN-EXCEPTION: " + str(sys.exc_info()))
