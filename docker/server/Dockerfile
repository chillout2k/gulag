FROM dockreg-zdf.int.zwackl.de/alpine/amd64:prod
LABEL maintainer="Dominik Chilla"

RUN env; set -ex ; \
    apk update \
 && apk add gcc python3-dev libc-dev uwsgi-python py3-flask-restful libmagic

RUN apk add libffi-dev
# ALPINE-TBD: ssdeep
RUN pip3 install python-magic mysql-connector
RUN pip3 install six

RUN /bin/mkdir /config /socket /app

ADD ./app/*.py /app/
ADD ./config/ /config/

CMD ["/usr/sbin/uwsgi","--emperor","/config/vassals"]
