# This file will deploy the appropriate asgs dataset set based on an argument
FROM alpine:3.8
LABEL maintainer="Shane Seaton <shane.seaton@csiro.au>"

ARG BRANCH_NAME

ENV APP_HOME=/app
ENV APP_DIR=${APP_HOME}/asgs_dataset/
ENV UWSGI_SOCKET_PATH=/var/run/uwsgi
ENV UWSGI_SOCKET=${UWSGI_SOCKET_PATH}/wsgi.sock
ENV SERVER_DOMAIN=localhost
ENV PYTHON_ENV=${APP_HOME}/venv
ENV PYTHONPATH=$APP_HOME
ENV APPLICATION_ROOT=/2011/
ENV SERVER_DIR=/

RUN apk upgrade --update-cache --available
RUN apk --no-cache add tini-static busybox-suid bash git ca-certificates tzdata build-base
RUN apk --no-cache add python3 python3-dev py3-virtualenv uwsgi uwsgi-python3 libxml2-dev libxslt-dev

RUN mkdir -p $APP_HOME
COPY . $APP_HOME

RUN mkdir -p ${UWSGI_SOCKET_PATH}

WORKDIR $APP_HOME
RUN rm -r venv
RUN python3 -m virtualenv -p /usr/bin/python3 venv

WORKDIR $APP_HOME
RUN source ${PYTHON_ENV}/bin/activate && pip3 install --upgrade -r ./requirements.txt

ENTRYPOINT [ "/sbin/tini-static", "--"] 
#CMD [ "bash", "-c", "/usr/sbin/uwsgi --socket ${UWSGI_SOCKET} --chmod-socket=776 --plugin python3  --virtualenv ${PYTHON_ENV} --wsgi-file ${APP_HOME}/asgs_dataset/app.py --callable app --max-requests=5000 --processes=3 -L" ]
CMD [ "bash", "-c", "/usr/sbin/uwsgi --socket ${UWSGI_SOCKET} --chmod-socket=776 --plugin python3  --virtualenv ${PYTHON_ENV}  --callable app --manage-script-name --mount /2011=asgs_dataset/app.py --enable-threads --max-requests=5000 --processes=3 -L" ]
