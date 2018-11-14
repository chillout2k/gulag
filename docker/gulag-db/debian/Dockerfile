FROM debian
RUN apt update && \
  apt -yq --no-install-recommends install procps net-tools mariadb-server mariadb-client
COPY db/gulag.sql /.
CMD ["/usr/bin/mysqld_safe"]
