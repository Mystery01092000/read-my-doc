import ssl

from celery import Celery

from app.config import settings

celery_app = Celery(
    "ask_my_docs",
    broker=settings.redis_url,
    include=["tasks.document_tasks"],
)

# Upstash Redis (and other managed TLS Redis) drops idle connections.
# Use ssl_cert_reqs=CERT_NONE so self-signed certs don't break the connection,
# and a small broker pool so stale connections are not reused across requests.
_is_tls = settings.redis_url.startswith("rediss://")

celery_app.conf.update(
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_acks_late=True,
    worker_prefetch_multiplier=1,
    # Document status is tracked in PostgreSQL — no need for Redis result storage.
    task_ignore_result=True,
    result_backend=None,
    # Reconnect automatically if the broker drops the connection.
    broker_connection_retry_on_startup=True,
    broker_connection_retry=True,
    broker_connection_max_retries=5,
    # Keep pool small so dropped connections are detected quickly.
    broker_pool_limit=1,
    # TLS options for Upstash / managed Redis (only applied when using rediss://).
    **({"broker_use_ssl": {"ssl_cert_reqs": ssl.CERT_NONE}} if _is_tls else {}),
)
