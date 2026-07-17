FROM redis:7-alpine

COPY entrypoint.sh /usr/local/bin/kinlin-redis-entrypoint
COPY healthcheck.sh /usr/local/bin/kinlin-redis-healthcheck
RUN apk add --no-cache su-exec \
    && chmod 0755 /usr/local/bin/kinlin-redis-entrypoint /usr/local/bin/kinlin-redis-healthcheck

ENTRYPOINT ["/usr/local/bin/kinlin-redis-entrypoint"]
