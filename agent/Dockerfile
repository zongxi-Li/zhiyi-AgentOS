FROM python:3.14-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app/agentOS/src:/app \
    AGENTOS_PACKS_DIR=/app/packs

WORKDIR /app

RUN apt-get update \
    && apt-get install -y --no-install-recommends gosu \
    && rm -rf /var/lib/apt/lists/* \
    && groupadd --gid 10002 kinlin \
    && useradd --uid 10002 --gid 10002 --no-create-home --shell /usr/sbin/nologin kinlin

COPY agent/requirements_minimal.txt ./requirements_minimal.txt
RUN pip install --no-cache-dir -r requirements_minimal.txt

COPY agent/app ./app
COPY agent/packs ./packs
COPY agent/knowledge ./knowledge
COPY agent/agentos.py ./agentos.py
COPY agentOS/src ./agentOS/src

RUN mkdir -p /app/data /app/logs
RUN mkdir -p /app/.cache /run/kinlin-secrets \
    && chown -R 10002:10002 /app /run/kinlin-secrets

COPY agent/docker-entrypoint.sh /usr/local/bin/kinlin-entrypoint
RUN sed -i 's/su-exec/gosu/g' /usr/local/bin/kinlin-entrypoint \
    && chmod 0755 /usr/local/bin/kinlin-entrypoint

EXPOSE 8000

ENTRYPOINT ["/usr/local/bin/kinlin-entrypoint"]
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "1"]
