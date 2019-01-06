import libgulag

try:
  gulag = libgulag.GulagClient({
    'api_uri': 'http://127.0.0.1:9090',
    'api_key': 'NotImplemented'
  })
  quarmails = gulag.get_quarmails({
    'filters': {"groupOp":"OR","rules":[
    #  {"field":"uri_count","op":"eq","data":"2"},
    #  {"field":"attach_count","op":"ne","data":"0"}
    #  {"field":"uri_count","op":"gt","data":"2"}
    ]},
    #'rfc822_message': 'ja, ich will',
    #'query_limit': 2,
    #'query_offset': 1
  })
  for qm in quarmails['quarmails']:
    print(
      "ID: " + str(qm['id'])
      + "\n  Subject: " + qm['hdr_subject']
      + "\n  ctime: " + qm['ctime']
      + "\n  attach_count: " + str(qm['attach_count'])
      + "\n  uri_count: " + str(qm['uri_count'])
      + "\n  imap_uid: " + str(qm['imap_uid'])
      + "\n  env_rcpt: " + qm['env_rcpt']
      + "\n  env_from: " + qm['env_from']
      + "\n  hdr_from: " + qm['hdr_from']
      + "\n  hdr_msgid: " + str(qm['hdr_msgid'])
    )
except libgulag.GulagClientException as e:
  print("ERROR: " + e.message)
