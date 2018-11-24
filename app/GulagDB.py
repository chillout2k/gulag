import mysql.connector as mariadb
from Entities import Mailbox,MailboxException,QuarMail,QuarMailException,Attachment,AttachmentException

class GulagDBException(Exception):
  message = None
  def __init__(self,message):
    self.message = str(message)

class GulagDB:
  conn = None
  uri_prefixes = None

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
      self.uri_prefixes = uri_prefixes
    except mariadb.Error as e:
      raise GulagDBException(e) from e

  def close(self):
    self.conn.close()

  def get_mailboxes(self):
    try:
      cursor = self.conn.cursor()
      cursor.execute("select * from Mailboxes;")
      results = []
      data = cursor.fetchall()
      if not data:
        raise GulagDBException("No mailboxes found in DB!")
      desc = cursor.description
      for tuple in data:
        dict = {}
        for (name, value) in zip(desc, tuple):
          dict[name[0]] = value
        dict['href'] = self.uri_prefixes['mailboxes'] + dict['email_address']
        try:
          results.append(Mailbox(dict).__dict__)
        except MailboxException as e:
          print("MailboxException: " + e.message)
          continue
      return results
    except mariadb.Error as e:
      raise GulagDBException(e) from e

  def get_mailbox(self,mailbox_id):
    try:
      cursor = self.conn.cursor()
      cursor.execute(
        "select * from Mailboxes where email_address='" + mailbox_id + "' limit 1;"
      )
      data = cursor.fetchall()
      if not data:
        raise GulagDBException("Mailbox '" + mailbox_id + "' does not exist!")
      desc = cursor.description
      tuple = data[0]
      dict = {}
      for (name, value) in zip(desc, tuple):
        dict[name[0]] = value
      dict['href'] = self.uri_prefixes['mailboxes'] + dict['email_address']
      try:
        return Mailbox(dict).__dict__
      except MailboxException as e:
        raise GulagDBException(e.message) from e
    except mariadb.Error as e:
      raise GulagDBException(e) from e

  def add_quarmail(self, quarmail):
    try:
      cursor = self.conn.cursor()
      cursor.execute("insert into QuarMails " +
          "(mx_queue_id,env_from,env_rcpt,"+
          "hdr_cf,hdr_from,hdr_subject,"+
          "hdr_msgid,hdr_date,cf_meta,"+
          "mailbox_id,imap_uid,msg_size) " +
        "values (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)",
        (quarmail['mx_queue_id'],quarmail['env_from'],quarmail['env_rcpt'],
         quarmail['hdr_cf'],quarmail['hdr_from'],quarmail['hdr_subject'],
         quarmail['hdr_msgid'],quarmail['hdr_date'],quarmail['cf_meta'],
         quarmail['mailbox_id'],quarmail['imap_uid'],quarmail['msg_size']
        )
      )
      id = cursor.lastrowid
      cursor.close()
      return id
    except mariadb.Error as e:
      raise GulagDBException(e) from e

  def del_quarmail(self, id):
    try:
      cursor = self.conn.cursor()
      cursor.execute("delete from QuarMails where id=%s;", (id))
      cursor.close()
      return True
    except mariadb.Error as e:
      raise GulagDBException(e) from e

  def get_quarmails(self):
    try:
      cursor = self.conn.cursor()
#      cursor.execute("select * from QuarMails;")
      query = "select *,(select count(*) from QuarMail2Attachment"
      query += " where QuarMails.id=QuarMail2Attachment.quarmail_id) as attach_count"
      query += " from QuarMails;"
      cursor.execute(query)
      results = []
      data = cursor.fetchall()
      if not data:
        raise GulagDBException("No Quarmails found in DB!")
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
    except mariadb.Error as e:
      raise GulagDBException(e) from e

  def get_quarmail(self,args):
    try:
      cursor = self.conn.cursor()
      # TODO: build SQL query by args
      #query = "select * from QuarMails where id='" + args['id'] + "';"
      query = "select *,(select count(*) from QuarMail2Attachment"
      query += " where QuarMails.id=QuarMail2Attachment.quarmail_id) as attach_count"
      query += " from QuarMails where QuarMails.id="+ str(args['id']) +";"
      cursor.execute(query)
      data = cursor.fetchall()
      if not data:
        raise GulagDBException("Quarmail with id '"+ args['id'] + "' does not exist!")
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
      try:
        dict['attachments'] = self.get_attachments_by_quarmail(args['id'])
      except GulagDBException as e:
        pass
      return QuarMail(dict).__dict__
    except mariadb.Error as e:
      raise GulagDBException(e) from e

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
      raise GulagDBException(e) from e

  def add_attachment(self, attach):
    try:
      cursor = self.conn.cursor()
      cursor.execute("insert into Attachments " +
        "(filename, content_type) values (%s,%s)",
        (attach['filename'], attach['content_type'])
      )
      return cursor.lastrowid
    except mariadb.Error as e:
      raise GulagDBException(e) from e
  
  def get_attachment(self, args):
    try:
      cursor = self.conn.cursor()
      cursor.execute("select * from Attachments where id=" + str(args['id']) + ";")
      data = cursor.fetchall()
      if not data:
        raise GulagDBException("Attachment("+ str(args['id']) +") does not exist!")
      desc = cursor.description
      tuple = data[0]
      dict = {}
      for (name, value) in zip(desc, tuple):
        dict[name[0]] = value
      dict['href'] = self.uri_prefixes['attachments'] + str(dict['id'])
      return Attachment(dict).__dict__
    except mariadb.Error as e:
      raise GulagDBException(e) from e
  
  def get_attachments_by_quarmail(self,quarmail_id):
    try:
      query = "select Attachments.* from QuarMail2Attachment"
      query += " left join QuarMails ON QuarMails.id = QuarMail2Attachment.quarmail_id"
      query += " left join Attachments ON Attachments.id = QuarMail2Attachment.attachment_id"
      query += " where QuarMails.id = " + str(quarmail_id) + ";"
      cursor = self.conn.cursor()
      cursor.execute(query)
      results = []
      data = cursor.fetchall()
      if not data:
        raise GulagDBException("QuarMail("+ str(quarmail_id) +") has no attachments!")
      desc = cursor.description
      for tuple in data:
        dict = {}
        for (name, value) in zip(desc, tuple):
          dict[name[0]] = value
        dict['href'] = self.uri_prefixes['attachments'] + str(dict['id'])
        results.append(Attachment(dict).__dict__)
      return results
    except mariadb.Error as e:
      raise GulagDBException(e) from e
  
  def quarmail2attachment(self,quarmail_id,attachment_id):
    try:
      cursor = self.conn.cursor()
      cursor.execute("insert into QuarMail2Attachment " +
        "(quarmail_id, attachment_id) values (%s,%s)",
        (quarmail_id, attachment_id)
      )
    except mariadb.Error as e:
      raise GulagDBException(e) from e

