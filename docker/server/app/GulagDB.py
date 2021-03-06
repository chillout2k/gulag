import mysql.connector as mariadb
from Entities import(
  Mailbox,MailboxException,QuarMail,
  QuarMailException,Attachment,
  AttachmentException,URI,URIException,
  Mailrelay,MailrelayException
)
from GulagUtils import whoami

class GulagDBException(Exception):
  message = None
  def __init__(self,message):
    self.message = str(message)

class GulagDBNotFoundException(Exception):
  message = None
  def __init__(self,message):
    self.message = str(message)

class GulagDBBadInputException(Exception):
  message = None
  def __init__(self,message):
    self.message = str(message)

class GulagDB:
  conn = None
  uri_prefixes = None
  vcols = {}

  def __init__(self, args, uri_prefixes):
    try:
      if 'unix_socket' in args:
        self.conn = mariadb.connect(
          unix_socket=args['unix_socket'],
          user=args['user'],
          password=args['password'],
          database=args['name'],
          autocommit=True
        )
      else:
        self.conn = mariadb.connect(
          host=args['server'],
          user=args['user'],
          password=args['password'],
          database=args['name'],
          autocommit=True
        )
    except mariadb.Error as e:
      raise GulagDBException(whoami(self) + str(e.msg)) from e
    self.uri_prefixes = uri_prefixes
    # virtual columns
    self.vcols['attach_count'] = {}
    self.vcols['uri_count'] = {}

  def close(self):
    self.conn.close()

  def get_fields(self,table_name):
    try:
      cursor = self.conn.cursor()
      query = "describe " + str(table_name) + ";"
      cursor.execute(query)
      data = cursor.fetchall()
      if not data:
        raise GulagDBNotFoundException(whoami(self)
          + "describe ''" + table_name + "'' failed: got no fields!"
        )
      desc = cursor.description
      cursor.close()
      results = {}
      for tuple in data:
        for (name, value) in zip(desc, tuple):
          if(name[0] == "Field"):
            results[value] = True
      return results
    except mariadb.Error as e:
      raise GulagDBException(whoami(self) + str(e.msg)) from e

  def get_limit_clause(self,args):
    if('query_offset' in args and 'query_limit' in args):
      try:
        int(args['query_offset'])
      except ValueError:
        raise GulagDBBadInputException(whoami(self) +
          "'query_offset' must be numeric!"
        )
      try:
        int(args['query_limit'])
      except ValueError:
        raise GulagDBBadInputException(whoami(self) +
          "'query_limit' must be numeric!"
        )
      return "limit "+args['query_offset']+","+args['query_limit']
    elif('query_offset' in args and 'query_limit' not in args):
      raise GulagDBBadInputException(whoami(self) +
        "'query_offset' without 'query_limit' is useless!"
      )
    elif('query_limit' in args and 'query_offset' not in args):
      try:
        int(args['query_limit'])
      except ValueError:
        raise GulagDBBadInputException(whoami(self) +
          "query_limit must be numeric!"
        )
      return "limit " + args['query_limit']
    else:
      return ""

  def get_where_clause_from_filters(self,filters):
    # {"groupOp":"AND","rules":[{"field":"uri_count","op":"eq","data":"3"}]}
    where_clause = ""
    for rule in filters['rules']:
      if 'field' not in rule:
        raise GulagDBBadInputException(whoami(self) +
          "'field' not found in rule!"
        )
      if 'op' not in rule:
        raise GulagDBBadInputException(whoami(self) +
          "'op' not found in rule!"
        )
      if 'data' not in rule:
        raise GulagDBBadInputException(whoami(self) +
          "'data' not found in rule!"
        )
      field_op_data = None
      if(rule['op'] == 'eq'):
        field_op_data = rule['field'] + "='" + rule['data'] + "'"
      elif(rule['op'] == 'bw'):
        field_op_data =  rule['field'] + " like '" + rule['data'] + "%'"
      elif(rule['op'] == 'ew'):
        field_op_data = rule['field'] + " like '%" + rule['data'] + "'"
      elif(rule['op'] == 'cn'):
        field_op_data = rule['field'] + " like '%" + rule['data'] + "%'"
      elif(rule['op'] == 'ne'):
        field_op_data = rule['field'] + " <>'" + rule['data'] + "'"
      elif(rule['op'] == 'gt'):
        field_op_data = rule['field'] + " > '" + rule['data'] + "'"
      elif(rule['op'] == 'lt'):
        field_op_data = rule['field'] + " < '" + rule['data'] + "'"
      if(field_op_data == None):
        raise GulagDBBadInputException(whoami(self) +
          "invalid rule-op: " + rule['op']
        )
      if(len(filters['rules']) == 1 or len(where_clause) == 0):
        if rule['field'] in self.vcols:
          where_clause = "having " + field_op_data
        else:
          where_clause = "where " + field_op_data
      else:
        where_clause += " " + filters['groupOp'] + " " + field_op_data
    return where_clause

  def add_mailrelay(self,args):
    pass

  def delete_mailrelay(self,mailrelay_id):
    pass

  def get_mailrelays(self):
    try:
      cursor = self.conn.cursor()
      cursor.execute("select * from Mailrelays;")
      results = []
      data = cursor.fetchall()
      if not data:
        return results
      desc = cursor.description
      for tuple in data:
        dict = {}
        for (name, value) in zip(desc, tuple):
          dict[name[0]] = value
        dict['href'] = self.uri_prefixes['mailrelays'] + dict['id']
        try:
          results.append(Mailrelay(dict).__dict__)
        except MailboxException as e:
          print("MailrelayException: " + e.message)
          continue
      return results
    except mariadb.Error as e:
      raise GulagDBException(whoami(self) + str(e.msg)) from e

  def get_mailrelay(self,mailrelay_id):
    try:
      cursor = self.conn.cursor()
      cursor.execute(
        "select * from Mailrelays where id='" + mailrelay_id + "' limit 1;"
      )
      data = cursor.fetchall()
      if not data:
        raise GulagDBNotFoundException(whoami(self)
          + "Mailrelay '" + mailrelay_id + "' does not exist!"
        )
      desc = cursor.description
      tuple = data[0]
      dict = {}
      for (name, value) in zip(desc, tuple):
        dict[name[0]] = value
      dict['href'] = self.uri_prefixes['mailrelays'] + dict['id']
      try:
        return Mailrelay(dict).__dict__
      except MailrelayException as e:
        raise GulagDBException(whoami(self) + e.message) from e
    except mariadb.Error as e:
      raise GulagDBException(whoami(self) + str(e.msg)) from e

  def add_mailbox(self,args):
    pass

  def delete_mailbox(self,mailbox_id):
    pass

  def get_mailboxes(self):
    try:
      cursor = self.conn.cursor()
      cursor.execute("select * from Mailboxes;")
      results = []
      data = cursor.fetchall()
      if not data:
        return results
      desc = cursor.description
      for tuple in data:
        dict = {}
        for (name, value) in zip(desc, tuple):
          dict[name[0]] = value
        dict['href'] = self.uri_prefixes['mailboxes'] + dict['id']
        try:
          results.append(Mailbox(dict).__dict__)
        except MailboxException as e:
          print("MailboxException: " + e.message)
          continue
      return results
    except mariadb.Error as e:
      raise GulagDBException(whoami(self) + str(e.msg)) from e

  def get_mailbox(self,mailbox_id):
    try:
      cursor = self.conn.cursor()
      cursor.execute(
        "select * from Mailboxes where id='" + mailbox_id + "' limit 1;"
      )
      data = cursor.fetchall()
      if not data:
        raise GulagDBNotFoundException(whoami(self)
          + "Mailbox '" + mailbox_id + "' does not exist!"
        )
      desc = cursor.description
      tuple = data[0]
      dict = {}
      for (name, value) in zip(desc, tuple):
        dict[name[0]] = value
      dict['href'] = self.uri_prefixes['mailboxes'] + dict['id']
      try:
        return Mailbox(dict).__dict__
      except MailboxException as e:
        raise GulagDBException(whoami(self) + e.message) from e
    except mariadb.Error as e:
      raise GulagDBException(whoami(self) + str(e.msg)) from e

  def add_quarmail(self, quarmail):
    try:
      cursor = self.conn.cursor()
      cursor.execute("insert into QuarMails " +
          "(mx_queue_id,env_from,env_rcpt,"+
          "hdr_cf,hdr_from,hdr_subject,"+
          "hdr_msgid,hdr_date,cf_meta,"+
          "mailbox_id,imap_uid,msg_size,ssdeep,"+
          "source_id) " +
        "values (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)",
        (quarmail['mx_queue_id'],quarmail['env_from'],quarmail['env_rcpt'],
         quarmail['hdr_cf'],quarmail['hdr_from'],quarmail['hdr_subject'],
         quarmail['hdr_msgid'],quarmail['hdr_date'],quarmail['cf_meta'],
         quarmail['mailbox_id'],quarmail['imap_uid'],quarmail['msg_size'],
         quarmail['ssdeep'],quarmail['source_id']
        )
      )
      id = cursor.lastrowid
      cursor.close()
      return id
    except mariadb.Error as e:
      raise GulagDBException(whoami(self) + (e.msg)) from e

  def modify_quarmail(self, quarmail):
    try:
      cursor = self.conn.cursor()
      mod_fields = ""
      if 'id' not in quarmail:
        raise GulagDBBadInputException("Missing QuarMail-ID!")
      if len(quarmail) < 2:
        raise GulagDBBadInputException("No fields specified to modify!")
      for field in quarmail:
        if field == 'id':
          continue
        mod_fields += " " + field + "='" + quarmail[field] + "',"
      mod_fields = str(mod_fields).rstrip(',')
      cursor.execute(
        "update QuarMails set "+mod_fields+" where id="+str(quarmail['id'])
      )
      if(cursor.rowcount == 0):
        raise GulagDBNotFoundException(whoami(self) + "No QuarMails modified!")
      cursor.close()
      return True
    except GulagDBBadInputException as e:
      raise GulagDBBadInputException(whoami(self) + e.message) from e
    except mariadb.Error as e:
      raise GulagDBException(whoami(self) + str(e.msg)) from e

  def delete_quarmail(self, id):
    try:
      cursor = self.conn.cursor()
      cursor.execute("delete from QuarMails where id=" + str(id))
      if(cursor.rowcount == 0):
        raise GulagDBNotFoundException(whoami(self) + "No QuarMails deleted!")
      cursor.close()
      return True
    except mariadb.Error as e:
      raise GulagDBException(whoami(self) + str(e.msg)) from e

  def get_quarmails(self,args):
    try:
      where_clause = ""
      if 'filters' in args:
        where_clause = self.get_where_clause_from_filters(args['filters'])
      cursor = self.conn.cursor()
      query = "select *,(select count(*) from QuarMail2Attachment"
      query += " where QuarMails.id=QuarMail2Attachment.quarmail_id) as attach_count,"
      query += " (select count(*) from QuarMail2URI"
      query += " where QuarMails.id=QuarMail2URI.quarmail_id) as uri_count"
      query += " from QuarMails " + where_clause
      query += " " + self.get_limit_clause(args) + " ;"
      cursor.execute(query)
      results = []
      data = cursor.fetchall()
      if not data:
        return results
      desc = cursor.description
      cursor.close()
      for tuple in data:
        dict = {}
        for (name, value) in zip(desc, tuple):
          if(name[0] == 'ctime'):
            dict[name[0]] = value.strftime('%Y-%m-%d %H:%M:%S')
          else:
            dict[name[0]] = value
        dict['href'] = self.uri_prefixes['quarmails'] + str(dict['id'])
        results.append(QuarMail(dict).__dict__)
      return results
    except GulagDBBadInputException as e:
      raise GulagDBBadInputException(whoami(self) + e.message) from e
    except GulagDBException as e:
      raise GulagDBException(whoami(self) + e.message) from e
    except mariadb.Error as e:
      raise GulagDBException(whoami(self) + str(e.msg)) from e

  def get_quarmail(self,args):
    try:
      cursor = self.conn.cursor()
      query = "select *,(select count(*) from QuarMail2Attachment"
      query += " where QuarMails.id=QuarMail2Attachment.quarmail_id) as attach_count,"
      query += " (select count(*) from QuarMail2URI"
      query += " where QuarMails.id=QuarMail2URI.quarmail_id) as uri_count"
      query += " from QuarMails where QuarMails.id="+ str(args['id']) +";"
      cursor.execute(query)
      data = cursor.fetchall()
      if not data:
        raise GulagDBNotFoundException(whoami(self)
          + "Quarmail with id '"+ str(args['id']) + "' does not exist!"
        )
      desc = cursor.description
      cursor.close()
      tuple = data[0]
      dict = {}
      for (name, value) in zip(desc, tuple):
        if(name[0] == 'ctime'):
          dict[name[0]] = value.strftime('%Y-%m-%d %H:%M:%S')
        else:
          dict[name[0]] = value
      dict['href'] = self.uri_prefixes['quarmails'] + str(dict['id'])
      return QuarMail(dict).__dict__
    except mariadb.Error as e:
      raise GulagDBException(whoami(self) + str(e.msg)) from e

  def get_deprecated_mails(self,retention_period):
    try:
      cursor = self.conn.cursor()
      query = "select ctime,mailbox_id,imap_uid from QuarMails"
      query += " where ctime < date_sub(NOW(), INTERVAL "+ str(retention_period) +");"
      cursor.execute(query)
      results = []
      data = cursor.fetchall()
      if not data:
        return results
      desc = cursor.description
      for tuple in data:
        dict = {}
        for (name, value) in zip(desc, tuple):
          dict[name[0]] = value
        results.append(dict)
      return results
    except mariadb.Error as e:
      raise GulagDBException(whoami(self) + str(e.msg)) from e

  def add_attachment(self, attach):
    try:
      cursor = self.conn.cursor()
      cursor.execute("insert into Attachments " +
        "(filename,content_type,content_encoding,magic,sha256,"+
        "ssdeep,size,mime_type) " +
        "values (%s,%s,%s,%s,%s,%s,%s,%s)",
        (attach['filename'],attach['content_type'],
         attach['content_encoding'],attach['magic'],
         attach['sha256'],attach['ssdeep'],attach['size'],
         attach['mime_type']
        )
      )
      return cursor.lastrowid
    except mariadb.Error as e:
      raise GulagDBException(whoami(self) + str(e.msg)) from e

  def modify_attachment(self, attachment):
    try:
      cursor = self.conn.cursor()
      mod_fields = ""
      if 'id' not in attachment:
        raise GulagDBBadInputException("Missing Attachment-ID!")
      if len(attachment) < 2:
        raise GulagDBBadInputException("No fields specified to modify!")
      for field in attachment:
        if field == 'id':
          continue
        mod_fields += " " + field + "='" + attachment[field] + "',"
      mod_fields = str(mod_fields).rstrip(',')
      cursor.execute(
        "update Attachment set "+mod_fields+" where id="+str(attachment['id'])
      )
      if(cursor.rowcount == 0):
        raise GulagDBNotFoundException(whoami(self) + "No attachments modified!")
      cursor.close()
      return True
    except GulagDBBadInputException as e:
      raise GulagDBBadInputException(whoami(self) + e.message) from e
    except mariadb.Error as e:
      raise GulagDBException(whoami(self) + str(e.msg)) from e

  def get_attachments(self):
    try:
      query = "select Attachments.*,QuarMails.mailbox_id,QuarMails.imap_uid"
      query += " from QuarMail2Attachment"
      query += " left join QuarMails ON QuarMails.id = QuarMail2Attachment.quarmail_id"
      query += " left join Attachments ON Attachments.id = QuarMail2Attachment.attachment_id"
      query += " group by id;"
      cursor = self.conn.cursor()
      cursor.execute(query)
      results = []
      data = cursor.fetchall()
      if not data:
        return results
      desc = cursor.description
      for tuple in data:
        dict = {}
        for (name, value) in zip(desc, tuple):
          dict[name[0]] = value
        #dict['href'] = self.uri_prefixes['attachments'] + str(dict['id'])
        dict['href'] = self.uri_prefixes['quarmails'] + str(quarmail_id)
        dict['href'] += "/attachments/" + str(dict['id'])
        results.append(Attachment(dict).__dict__)
      return results
    except mariadb.Error as e:
      raise GulagDBException(whoami(self) + str(e.msg)) from e

  def get_attachment(self, args):
    try:
      cursor = self.conn.cursor()
      query = "select Attachments.*,QuarMails.mailbox_id,QuarMails.imap_uid"
      query += " from QuarMail2Attachment"
      query += " left join QuarMails ON QuarMails.id = QuarMail2Attachment.quarmail_id"
      query += " left join Attachments ON Attachments.id = QuarMail2Attachment.attachment_id"
      query += " where attachment_id=" + str(args['id']) + ";"
      cursor.execute(query)
      data = cursor.fetchall()
      if not data:
        raise GulagDBNotFoundException(whoami(self)
          + "Attachment("+ str(args['id']) +") does not exist!"
        )
      desc = cursor.description
      tuple = data[0]
      dict = {}
      for (name, value) in zip(desc, tuple):
        dict[name[0]] = value
      #dict['href'] = self.uri_prefixes['attachments'] + str(dict['id'])
      dict['href'] = self.uri_prefixes['attachments'] + str(dict['id'])
      return Attachment(dict).__dict__
    except mariadb.Error as e:
      raise GulagDBException(whoami(self) + str(e.msg)) from e

  def get_quarmail_attachments(self,quarmail_id):
    try:
      query = "select Attachments.*,QuarMails.mailbox_id,QuarMails.imap_uid"
      query += " from QuarMail2Attachment"
      query += " left join QuarMails ON QuarMails.id = QuarMail2Attachment.quarmail_id"
      query += " left join Attachments ON Attachments.id = QuarMail2Attachment.attachment_id"
      query += " where QuarMails.id = " + str(quarmail_id) + ";"
      cursor = self.conn.cursor()
      cursor.execute(query)
      results = []
      data = cursor.fetchall()
      if not data:
        return results
      desc = cursor.description
      for tuple in data:
        dict = {}
        for (name, value) in zip(desc, tuple):
          dict[name[0]] = value
        dict['href'] = self.uri_prefixes['quarmails'] + str(quarmail_id)
        dict['href'] += "/attachments/" + str(dict['id'])
        results.append(Attachment(dict).__dict__)
      return results
    except mariadb.Error as e:
      raise GulagDBException(whoami(self) + str(e.msg)) from e
    except AttachmentException as e:
      raise GulagDBException(whoami(self) + e.message) from e

  def get_quarmail_attachment(self,quarmail_id,attachment_id):
    try:
      query = "select Attachments.*,QuarMails.mailbox_id,QuarMails.imap_uid"
      query += " from QuarMail2Attachment"
      query += " left join QuarMails ON QuarMails.id = QuarMail2Attachment.quarmail_id"
      query += " left join Attachments ON Attachments.id = QuarMail2Attachment.attachment_id"
      query += " where QuarMails.id = " + str(quarmail_id)
      query += " and Attachments.id = " + str(attachment_id) + ";"
      cursor = self.conn.cursor()
      cursor.execute(query)
      data = cursor.fetchall()
      if not data:
        raise GulagDBNotFoundException(whoami(self) +
          "QuarMail("+ str(quarmail_id) +") " +
          "has no attachment (" + str(attachment_id) + ")!"
        )
      desc = cursor.description
      tuple = data[0]
      dict = {}
      for (name, value) in zip(desc, tuple):
        dict[name[0]] = value
      dict['href'] = self.uri_prefixes['quarmails'] + str(quarmail_id)
      dict['href'] += "/attachments/" + str(dict['id'])
      return Attachment(dict).__dict__
    except mariadb.Error as e:
      raise GulagDBException(whoami(self) + str(e.msg)) from e
    except AttachmentException as e:
      raise GulagDBException(whoami(self) + e.message) from e

  def delete_quarmail_attachments(self, quarmail_id):
    cursor = None
    try:
      cursor = self.conn.cursor()
    except mariadb.Error as e:
      raise GulagDBException(whoami(self) + str(e)) from e
    for qm_at in self.get_quarmail_attachments(quarmail_id):
      try:
        cursor.execute("delete from Attachments where id=" + str(qm_at['id']))
      except mariadb.Error as e:
        raise GulagDBException(whoami(self) + str(e.msg)) from e
    cursor.close()
    return True

  def quarmail2attachment(self,quarmail_id,attachment_id):
    try:
      cursor = self.conn.cursor()
      cursor.execute("insert into QuarMail2Attachment " +
        "(quarmail_id, attachment_id) values (%s,%s)",
        (quarmail_id, attachment_id)
      )
    except mariadb.Error as e:
      raise GulagDBException(whoami(self) + str(e.msg)) from e

  def add_uri(self,args):
    try:
      cursor = self.conn.cursor()
      cursor.execute("insert into URIs " +
        "(uri, fqdn) values (%s,%s)",
        (args['uri'], args['fqdn'])
      )
      return cursor.lastrowid
    except mariadb.Error as e:
      raise GulagDBException(whoami(self) + str(e.msg)) from e

  def get_uri(self,uri_id):
    try:
      query = "select * from URIs where id=" + str(uri_id) + ";"
      cursor = self.conn.cursor()
      cursor.execute(query)
      data = cursor.fetchall()
      if not data:
        raise GulagDBNotFoundException(whoami(self) +
          "URI(" + str(uri_id) + ") not found!"
        )
      desc = cursor.description
      tuple = data[0]
      dict = {}
      for (name, value) in zip(desc, tuple):
        dict[name[0]] = value
        dict['href'] = self.uri_prefixes['uris'] + str(dict['id'])
      try:
        return URI(dict).__dict__
      except URIException as e:
        raise GulagDBException(whoami(self) + e.message) from e
    except mariadb.Error as e:
      raise GulagDBException(whoami(self) + str(e.msg)) from e

  def modify_uri(self, uri):
    try:
      cursor = self.conn.cursor()
      mod_fields = ""
      if 'id' not in uri:
        raise GulagDBBadInputException("Missing URI-ID!")
      if len(uri) < 2:
        raise GulagDBBadInputException("No fields specified to modify!")
      for field in uri:
        if field == 'id':
          continue
        mod_fields += " " + field + "='" + uri[field] + "',"
      mod_fields = str(mod_fields).rstrip(',')
      cursor.execute("update URI set "+mod_fields+" where id="+str(uri['id']))
      if(cursor.rowcount == 0):
        raise GulagDBNotFoundException(whoami(self) + "No URIs modified!")
      cursor.close()
      return True
    except GulagDBBadInputException as e:
      raise GulagDBBadInputException(whoami(self) + e.message) from e
    except mariadb.Error as e:
      raise GulagDBException(whoami(self) + str(e.msg)) from e

  def quarmail2uri(self,quarmail_id,uri_id):
    try:
      cursor = self.conn.cursor()
      cursor.execute("insert into QuarMail2URI " +
        "(quarmail_id, uri_id) values (%s,%s)",
        (quarmail_id, uri_id)
      )
    except mariadb.Error as e:
      raise GulagDBException(whoami(self) + str(e.msg)) from e

  def get_quarmail_uris(self,quarmail_id):
    try:
      query = "select URIs.*"
      query += " from QuarMail2URI"
      query += " left join QuarMails ON QuarMails.id = QuarMail2URI.quarmail_id"
      query += " left join URIs ON URIs.id = QuarMail2URI.uri_id"
      query += " where QuarMails.id = " + str(quarmail_id) + ";"
      cursor = self.conn.cursor()
      cursor.execute(query)
      results = []
      data = cursor.fetchall()
      if not data:
        return results
      desc = cursor.description
      for tuple in data:
        dict = {}
        for (name, value) in zip(desc, tuple):
          dict[name[0]] = value
        #dict['href'] = self.uri_prefixes['uris'] + str(dict['id'])
        dict['href'] = self.uri_prefixes['quarmails'] + str(quarmail_id)
        dict['href'] += "/uris/" + str(dict['id'])
        results.append(URI(dict).__dict__)
      return results
    except mariadb.Error as e:
      raise GulagDBException(whoami(self) + str(e.msg)) from e
    except URIException as e:
      raise GulagDBException(whoami(self) + e.message) from e

  def get_quarmail_uri(self,quarmail_id,uri_id):
    try:
      query = "select URIs.*"
      query += " from QuarMail2URI"
      query += " left join QuarMails ON QuarMails.id = QuarMail2URI.quarmail_id"
      query += " left join URIs ON URIs.id = QuarMail2URI.uri_id"
      query += " where QuarMails.id = " + str(quarmail_id)
      query += " and URIs.id = " + str(uri_id) + ";"
      cursor = self.conn.cursor()
      cursor.execute(query)
      data = cursor.fetchall()
      if not data:
        raise GulagDBNotFoundException(whoami(self) +
          "QuarMail("+ str(quarmail_id) +")" +
          " has no uri (" + str(uri_id) + ")!"
        )
      desc = cursor.description
      tuple = data[0]
      dict = {}
      for (name, value) in zip(desc, tuple):
        dict[name[0]] = value
        #dict['href'] = self.uri_prefixes['uris'] + str(dict['id'])
        dict['href'] = self.uri_prefixes['quarmails'] + str(quarmail_id)
        dict['href'] += "/uris/" + str(dict['id'])
      try:
        return URI(dict).__dict__
      except URIException as e:
        raise GulagDBException(whoami(self) + e.message) from e
    except mariadb.Error as e:
      raise GulagDBException(whoami(self) + str(e.msg)) from e

  def delete_quarmail_uris(self, quarmail_id):
    cursor = None
    try:
      cursor = self.conn.cursor()
    except mariadb.Error as e:
      raise GulagDBException(whoami(self) + str(e)) from e
    for qm_uri in self.get_quarmail_uris(quarmail_id):
      try:
        cursor.execute("delete from URIs where id=" + str(qm_uri['id']))
      except mariadb.Error as e:
        raise GulagDBException(whoami(self) + str(e.msg)) from e
    cursor.close()
    return True
