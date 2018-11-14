FROM debian
LABEL maintainer="Dominik Chilla"

ENV DEBIAN_FRONTEND=noninteractive \
 TZ=Europe/Berlin

RUN set -ex ; \
      apt-get -qq update \
    && apt-get -qq --no-install-recommends install \
       uwsgi-plugin-python3 python3-setuptools python3-flask \
       python3-flask-restful python3-mysql.connector \
       uwsgi uwsgi-plugin-python3

RUN /bin/mkdir /config /socket /app
COPY app/*.py /app/
