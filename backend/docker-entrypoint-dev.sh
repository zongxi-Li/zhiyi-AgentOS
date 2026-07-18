#!/bin/sh
set -eu

install -d -m 0750 -o 10001 -g 10001 /home/kinlin /home/kinlin/.m2 /app/target /app/target/.jansi
chown 10001:10001 /home/kinlin /home/kinlin/.m2 /app/target /app/target/.jansi
exec /usr/local/bin/kinlin-entrypoint "$@"
