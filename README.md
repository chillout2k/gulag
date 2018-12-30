# gulag
Gulag quarantine

## curl examples

### get all QuarMail metadata
```curl -v -s http://127.0.0.1:9090/api/v1/quarmails | jq
```

### get all QuarMail metadata + RFC822 messages
```curl -v -s http://127.0.0.1:9090/api/v1/quarmails?rfc822_message=1 | jq
```

### get QuarMails metadata by (jqgrid-style) filter
```curl -v -s -G --data-urlencode 'filters={"groupOp":"OR","rules":[{"field":"hdr_subject","op":"eq","data":"996 test from quar mit sync xyz"}]}' http://127.0.0.1:9090/api/v1/quarmails | jq
```

### delete a QuarMail by ID
```curl -v -s -X DELETE http://127.0.0.1:9090/api/v1/quarmails/141 | jq
```

### get a QuarMail´s metadata by ID
```curl -v -s http://127.0.0.1:9090/api/v1/quarmails/136 | jq
```

### get a QuarMail´s metadata by ID + RFC822 message
```curl -v -s http://127.0.0.1:9090/api/v1/quarmails/136?rfc822_message=1 | jq
```

### get all URIs of a QuarMail
```curl -v -s http://127.0.0.1:9090/api/v1/quarmails/136/uris | jq
```

### get an URI of a QuarMail by ID
```curl -v -s http://127.0.0.1:9090/api/v1/quarmails/136/uris/249 | jq
```

### get all attachments metadata of a QuarMail
```curl -v -s http://127.0.0.1:9090/api/v1/quarmails/136/attachments | jq
```

### get an attachments metadata of a QuarMail by ID
```curl -v -s http://127.0.0.1:9090/api/v1/quarmails/136/attachments/71 | jq
```

### get an attachments metadata of a QuarMail by ID + attachment data
```curl -v -s http://127.0.0.1:9090/api/v1/quarmails/136/attachments/71?data=1 | jq
```
