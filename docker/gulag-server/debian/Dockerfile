ARG http_proxy
ARG https_proxy
FROM debian:buster
LABEL maintainer="Dominik Chilla"

ENV DEBIAN_FRONTEND=noninteractive \
 TZ=Europe/Berlin

RUN env; set -ex ; \
    apt-get -qq update \
 && apt-get -qq --no-install-recommends install \
      uwsgi-plugin-python3 python3-setuptools python3-flask \
      python3-flask-restful \
      uwsgi uwsgi-plugin-python3 procps net-tools \
      python3-pip libmagic1 python3-ssdeep \
 && pip3 install python-magic mysql-connector \
 && /bin/mkdir /config /socket /app \
 && apt-get clean \
 && rm -rf /var/lib/apt/lists/*

COPY app/*.py /app/

CMD ["/usr/bin/uwsgi","--emperor","/config/vassals"]
