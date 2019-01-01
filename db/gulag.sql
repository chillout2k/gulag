create database Gulag;

use Gulag;

create table Mailrelays(
  id varchar(64) not null primary key,
  smtp_server varchar(256) default '127.0.0.1' collate 'ascii_general_ci',
  smtp_port smallint unsigned not null default 25,
  smtp_security varchar(32) not null default 'plain' collate 'ascii_general_ci',
  smtp_user varchar(256) default null collate 'ascii_general_ci',
  smtp_pass varchar(1024) default null collate 'ascii_general_ci',
  comment varchar(256) default null
)ENGINE = InnoDB;

create table Mailboxes(
  email_address varchar(767) not null primary key collate 'ascii_general_ci',
  name varchar(256) not null,
  imap_server varchar(256) not null default '127.0.0.1' collate 'ascii_general_ci',
  imap_port smallint unsigned not null default 143,
  imap_security varchar(32) not null default 'plain' collate 'ascii_general_ci',
  imap_user varchar(256) not null collate 'ascii_general_ci',
  imap_pass varchar(1024) not null collate 'ascii_general_ci',
  imap_mailbox varchar(256) not null default 'INBOX',
  imap_mailbox_fp varchar(256) not null default 'false-positives',
  imap_separator varchar(4) not null default '/',
  comment varchar(256) default null
)ENGINE = InnoDB;
insert into Mailboxes (email_address,name,imap_user,imap_pass)
  values('quarantine@example.org','E-Mail inbound quarantine','quarantine','quarantine_secure_password');

create table Sources (
  id varchar(32) not null collate 'ascii_general_ci' primary key
)ENGINE=InnoDB;
insert into Sources (id) values ('amavis');
insert into Sources (id) values ('rspamd');
insert into Sources (id) values ('mailradar');

create table QuarMails (
  id int unsigned auto_increment primary key,
  ctime TIMESTAMP,
  mx_queue_id varchar(64) not null collate 'ascii_general_ci',
  env_from varchar(256) not null ,
  env_rcpt varchar(256) not null,
  hdr_cf TEXT,
  hdr_from varchar(256) default null,
  hdr_subject varchar(1024) default null,
  hdr_msgid varchar(512) default null,
  hdr_date varchar(128) default null collate 'ascii_general_ci',
  cf_meta TEXT default null,
  imap_uid int unsigned not null,
  mailbox_id varchar(256) not null collate 'ascii_general_ci',
  foreign key (mailbox_id) references Mailboxes (email_address) on update cascade on delete cascade,
  source_id varchar(32) not null collate 'ascii_general_ci',
  foreign key (source_id) references Sources (id) on update cascade on delete cascade,
  msg_size int unsigned not null,
  ssdeep varchar(592) not null collate 'ascii_general_ci'
)ENGINE = InnoDB;

create table Attachments (
  id int unsigned auto_increment primary key,
  filename varchar(256) not null,
  content_type varchar(256) not null collate 'ascii_general_ci',
  content_encoding varchar(64) collate 'ascii_general_ci',
  magic varchar(128),
  comment varchar(256),
  size int unsigned not null,
  sandbox_results varchar(1024) default null collate 'ascii_general_ci',
  sha256 varchar(64) not null collate 'ascii_general_ci',
  ssdeep varchar(592) not null collate 'ascii_general_ci'
)ENGINE = InnoDB;

create table QuarMail2Attachment (
  quarmail_id int unsigned,
  attachment_id int unsigned,
  foreign key (quarmail_id) references QuarMails (id) on delete cascade on update cascade,
  foreign key (attachment_id) references Attachments (id) on delete cascade on update cascade
)ENGINE = InnoDB;

create table URIs (
  id int unsigned auto_increment primary key,
  uri varchar(2048) not null collate 'ascii_general_ci',
  fqdn varchar(512) not null collate 'ascii_general_ci',
  sandbox_results varchar(1024) default null collate 'ascii_general_ci'
)ENGINE = InnoDB;

create table QuarMail2URI (
  quarmail_id int unsigned,
  uri_id int unsigned,
  foreign key (quarmail_id) references QuarMails (id) on delete cascade on update cascade,
  foreign key (uri_id) references URIs (id) on delete cascade on update cascade
)ENGINE = InnoDB;
