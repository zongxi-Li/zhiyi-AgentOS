#!/bin/sh
set -eu

manifest=/app/requirements.lock
venv=/opt/kinlin-venv
expected=$(sha256sum "$manifest" | cut -d ' ' -f 1)
actual=$(cat "$venv/.kinlin-requirements.sha256" 2>/dev/null || true)
if [ "$expected" != "$actual" ]; then
  echo "Python dependency manifest changed; synchronizing the named virtualenv volume"
  "$venv/bin/pip" install --cache-dir /pip-cache --require-hashes --only-binary=:all: -r "$manifest"
  printf '%s\n' "$expected" > "$venv/.kinlin-requirements.sha256"
else
  echo "Python dependency volume is current; skipping pip install"
fi

exec /usr/local/bin/kinlin-entrypoint "$@"
