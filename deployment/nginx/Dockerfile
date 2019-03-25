FROM alpine:3.8
LABEL Shane Seaton <shane.seaton@csiro.au>
# Nginx Dockerfile 

RUN apk upgrade --update-cache --available
RUN apk --no-cache add tini-static busybox-suid bash ca-certificates tzdata nginx gettext

ADD ./asgs.conf.template /etc/nginx/conf.d/
ADD ./uwsgi_params /etc/nginx/conf.d/

RUN mkdir -p /run/nginx
RUN rm /etc/nginx/conf.d/default.conf

EXPOSE 80
ENTRYPOINT [ "/sbin/tini-static", "--" ] 
CMD ["sh", "-c", "env && envsubst \"$(env | sed -e 's/=.*//' -e 's/^/\\$/g')\" < /etc/nginx/conf.d/asgs.conf.template > /etc/nginx/conf.d/asgs.conf && exec /usr/sbin/nginx -g 'daemon off;' -c /etc/nginx/nginx.conf" ]
