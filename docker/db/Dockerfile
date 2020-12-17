ARG http_proxy
ARG https_proxy
FROM debian
RUN apt update && \
  apt -yq --no-install-recommends install procps net-tools \
    mariadb-server mariadb-client \
 && apt-get clean \
 && rm -rf /var/lib/apt/lists/*
COPY db/gulag.sql /.
CMD ["/usr/bin/mysqld_safe"]

### FIXME: /var/run/mysqld ist nur für root beschreibbar!
