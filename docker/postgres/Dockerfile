FROM postgres:15-alpine

COPY secret-entrypoint.sh /usr/local/bin/kinlin-postgres-entrypoint
RUN chmod 0755 /usr/local/bin/kinlin-postgres-entrypoint

ENTRYPOINT ["/usr/local/bin/kinlin-postgres-entrypoint"]
CMD ["postgres"]
