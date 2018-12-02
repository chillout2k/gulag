create database Gulag;

use Gulag;

create table Mailboxes(
  email_address varchar(767) not null primary key collate 'ascii_general_ci',
  name varchar(256) not null,
  imap_server varchar(256) not null default '127.0.0.1',
  imap_port smallint unsigned not null default 143,
  imap_security varchar(32) not null default 'plain',
  imap_user varchar(256) not null,
  imap_pass varchar(256) not null,
  imap_mailbox varchar(256) not null default 'INBOX',
  imap_mailbox_fp varchar(256) not null default 'false-positives',
  imap_separator varchar(4) not null default '/',
  smtp_server varchar(256) default null,
  smtp_port smallint unsigned not null default 25,
  smtp_security varchar(32) not null default 'plain',
  smtp_user varchar(256) default null,
  smtp_pass varchar(2048) default null,
  comment varchar(256) default null
)ENGINE = InnoDB;
insert into Mailboxes (email_address,name,imap_user,imap_pass) 
  values('quarantine-in@example.org','E-Mail inbound quarantine','quarantine-in','quarantine-in_secure_password');
insert into Mailboxes (email_address,name,imap_user,imap_pass) 
  values('quarantine-out@example.org','E-Mail outbound quarantine','quarantine-out','quarantine-out_secure_password');
insert into Mailboxes (email_address,name,imap_user,imap_pass) 
  values('quarantine-sandbox@example.org','E-Mail sandbox quarantine','quarantine-sb','quarantine-sb_secure_password');

create table QuarMails (
  id int unsigned auto_increment primary key,
  ctime TIMESTAMP,
  mx_queue_id varchar(64) not null,
  env_from varchar(256) not null,
  env_rcpt varchar(256) not null,
  hdr_cf TEXT,
  hdr_from varchar(256) default null,
  hdr_subject varchar(1024) default null,
  hdr_msgid varchar(512) default null,
  hdr_date varchar(128) default null,
  cf_meta TEXT default null,
  mailbox_id varchar(256) not null collate 'ascii_general_ci',
  foreign key (mailbox_id) references Mailboxes (email_address) on update cascade on delete cascade,
  imap_uid int unsigned not null,
  msg_size int unsigned not null
)ENGINE = InnoDB;

create table Attachments (
  id int unsigned auto_increment primary key,
  filename varchar(256) not null,
  content_type varchar(256) not null,
  content_encoding varchar(64),
  comment varchar(256)
)ENGINE = InnoDB;

create table QuarMail2Attachment (
  quarmail_id int unsigned,
  attachment_id int unsigned,
  foreign key (quarmail_id) references QuarMails (id) on delete cascade on update cascade,
  foreign key (attachment_id) references Attachments (id) on delete cascade on update cascade
)ENGINE = InnoDB;

