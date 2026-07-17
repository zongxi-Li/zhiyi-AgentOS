FROM flyway/flyway:9.22.3-alpine

USER root
COPY entrypoint.sh /usr/local/bin/kinlin-flyway-entrypoint
RUN apk add --no-cache su-exec \
    && addgroup -g 10004 -S kinlin \
    && adduser -S -D -H -u 10004 -G kinlin kinlin \
    && chmod 0755 /usr/local/bin/kinlin-flyway-entrypoint
ENTRYPOINT ["/usr/local/bin/kinlin-flyway-entrypoint"]
