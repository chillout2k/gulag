import libgulag

try:
  gulag = libgulag.GulagClient({
    'api_uri': 'http://127.0.0.1:9090',
    'api_key': 'NotImplemented'
  })
  quarmails = gulag.get_quarmails({
    'filters': {"groupOp":"AND","rules":[
      {"field":"uri_count","op":"eq","data":"2"}
    ]},
    'rfc822_message': 'ja, ich will',
    'query_limit': 2
  })
  for qm in quarmails['quarmails']:
    print(
      "ID: " + str(qm['id'])
      + "\n  Subject: " + qm['hdr_subject']
      + "\n  ctime: " + qm['ctime']
    )
except libgulag.GulagClientException as e:
  print("ERROR: " + e.message)
