import mysql.connector as mariadb

class GulagDBException(Exception):
  message = None
  def __init__(self,message):
    self.message = str(message)

class GulagDB:
  conn = None

  def __init__(self, server, user, password, name):
    try:
      self.conn = mariadb.connect(
        host=server,
        user=user,
        password=password,
        database=name
      )
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
      if data == None:
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
      self.conn.commit()
      return cursor.lastrowid
    except mariadb.Error as e:
      raise GulagDBException(e) from e

  def del_quarmail(self, id):
    try:
      cursor = self.conn.cursor()
      cursor.execute("delete from QuarMails where id=%s;", (id))
      self.conn.commit()
      return cursor.lastrowid
    except mariadb.Error as e:
      raise GulagDBException(e) from e

  def get_quarmails(self, mailbox_id):
    try:
      cursor = self.conn.cursor()
      cursor.execute(
        "select * from QuarMails where mailbox_id='%s';",
        (mailbox_id)
      )
      results = []
      data = cursor.fetchall()
      if data == None:
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

  def get_deprecated_mails(self,retention_period):
    try:
      cursor = self.conn.cursor()
      query = "select ctime,mailbox_id,imap_uid from QuarMails where ctime < date_sub(NOW(), INTERVAL "+ retention_period +");"
      cursor.execute(query)
      results = []
      data = cursor.fetchall()
      if data == None:
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
      self.conn.commit()
      return cursor.lastrowid
    except mariadb.Error as e:
      raise GulagDBException(e) from e

  def quarmail2attachment(self,quarmail_id,attachment_id):
    try:
      cursor = self.conn.cursor()
      cursor.execute("insert into QuarMail2Attachment " +
        "(quarmail_id, attachment_id) values (%s,%s)",
        (quarmail_id, attachment_id)
      )
      self.conn.commit()
    except mariadb.Error as e:
      raise GulagDBException(e) from e

