ARG http_proxy
ARG https_proxy
FROM debian
LABEL maintainer="Dominik Chilla"

ENV DEBIAN_FRONTEND=noninteractive \
 TZ=Europe/Berlin

RUN env; set -ex ; \
    apt-get -qq update \
 && apt-get -qq --no-install-recommends install \
      uwsgi-plugin-python3 python3-setuptools python3-flask \
      python3-flask-restful python3-mysql.connector \
      uwsgi uwsgi-plugin-python3 procps net-tools \
      python3-pip libmagic1 python3-ssdeep \
 && pip3 install python-magic \
 && /bin/mkdir /config /socket /app

COPY app/*.py /app/
