from __future__ import annotations

import os
import socket
import sys
import time
from io import BytesIO
from pathlib import Path
from uuid import uuid4

import pytest


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "backend" / "shared" / "learngrid-events" / "src"))
sys.path.insert(0, str(ROOT / "backend" / "shared" / "learngrid-redis" / "src"))


SERVICE_DATABASES = {
    "auth_db",
    "user_db",
    "course_db",
    "content_db",
    "enrollment_db",
    "progress_db",
    "assessment_db",
    "grading_db",
    "notification_db",
    "analytics_db",
}


def _host_port_from_url(url: str, default_port: int) -> tuple[str, int]:
    from urllib.parse import urlparse

    parsed = urlparse(url)
    return parsed.hostname or "127.0.0.1", parsed.port or default_port


def _require_tcp(host: str, port: int, service: str) -> None:
    try:
        with socket.create_connection((host, port), timeout=1.5):
            return
    except OSError as exc:
        pytest.skip(f"{service} is not reachable at {host}:{port}: {exc}")


def test_postgres_service_databases_exist():
    psycopg = pytest.importorskip("psycopg")
    database_url = os.getenv(
        "INTEGRATION_DATABASE_URL",
        "postgresql://learngrid:learngrid@127.0.0.1:5432/learngrid",
    )
    host, port = _host_port_from_url(database_url, 5432)
    _require_tcp(host, port, "PostgreSQL")

    with psycopg.connect(database_url) as connection:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
            assert cursor.fetchone() == (1,)
            cursor.execute("SELECT datname FROM pg_database")
            found = {row[0] for row in cursor.fetchall()}

    assert SERVICE_DATABASES <= found


def test_redis_helpers_use_real_redis():
    import redis
    from learngrid_redis import RedisKeyBuilder, fixed_window_rate_limit, redis_client, redis_lock

    redis_url = os.getenv("INTEGRATION_REDIS_URL", "redis://127.0.0.1:6379/0")
    host, port = _host_port_from_url(redis_url, 6379)
    _require_tcp(host, port, "Redis")

    client = redis_client(redis_url)
    try:
        assert client.ping()
    except (redis.RedisError, OSError) as exc:
        pytest.skip(f"Redis is not ready: {exc}")

    key_builder = RedisKeyBuilder(service="quality-tests", env="integration")
    rate_key = key_builder.key("rate-limit", "smoke", str(uuid4()))
    first = fixed_window_rate_limit(client, rate_key, limit=2, window_seconds=30)
    second = fixed_window_rate_limit(client, rate_key, limit=2, window_seconds=30)
    third = fixed_window_rate_limit(client, rate_key, limit=2, window_seconds=30)
    assert (first.allowed, second.allowed, third.allowed) == (True, True, False)

    lock_key = key_builder.key("locks", "smoke", str(uuid4()))
    with redis_lock(client, lock_key, ttl_seconds=10) as lock:
        assert lock.acquired
        assert client.get(lock_key) == lock.token
    assert client.get(lock_key) is None


def test_kafka_adapter_round_trips_real_message():
    from kafka import KafkaConsumer
    from learngrid_events.adapters import KafkaProducerAdapter
    from learngrid_events.envelope import create_event_envelope

    bootstrap = os.getenv("INTEGRATION_KAFKA_BOOTSTRAP_SERVERS", "127.0.0.1:9092")
    host, port = bootstrap.split(",", 1)[0].split(":", 1)
    _require_tcp(host, int(port), "Kafka")

    topic = os.getenv("INTEGRATION_KAFKA_TOPIC", "analytics.events")
    event = create_event_envelope(
        event_type="QualitySmoke",
        aggregate_id=uuid4(),
        producer_service="analytics-service",
        payload={"kind": "integration"},
    ).to_dict()
    adapter = KafkaProducerAdapter(bootstrap_servers=bootstrap, client_id="quality-contract-test")
    consumer = KafkaConsumer(
        topic,
        bootstrap_servers=bootstrap.split(","),
        auto_offset_reset="earliest",
        enable_auto_commit=True,
        group_id=f"quality-contract-{uuid4()}",
        value_deserializer=lambda value: __import__("json").loads(value.decode("utf-8")),
        consumer_timeout_ms=1000,
    )
    try:
        adapter.send(topic, event, key=event["aggregate_id"])
        deadline = time.monotonic() + 10
        while time.monotonic() < deadline:
            records = consumer.poll(timeout_ms=1000)
            for messages in records.values():
                for message in messages:
                    if message.value.get("event_id") == event["event_id"]:
                        assert message.value["event_type"] == "QualitySmoke"
                        return
        pytest.fail("Kafka message was not observed before timeout.")
    finally:
        adapter.close()
        consumer.close()


def test_minio_object_round_trip():
    from minio import Minio
    from minio.error import S3Error
    from urllib.parse import urlparse

    raw_endpoint = os.getenv("INTEGRATION_MINIO_ENDPOINT", "127.0.0.1:9000")
    parsed_endpoint = urlparse(raw_endpoint)
    endpoint = parsed_endpoint.netloc or parsed_endpoint.path
    secure = os.getenv("INTEGRATION_MINIO_SECURE", "false").lower() == "true"
    if parsed_endpoint.scheme:
        secure = parsed_endpoint.scheme == "https"
    access_key = os.getenv("INTEGRATION_MINIO_ACCESS_KEY", "learngrid")
    secret_key = os.getenv("INTEGRATION_MINIO_SECRET_KEY", "learngrid-minio-secret")
    bucket = os.getenv("INTEGRATION_MINIO_BUCKET", "learngrid-content")
    host, port = endpoint.split(":", 1) if ":" in endpoint else (endpoint, "9000")
    _require_tcp(host, int(port), "MinIO")

    client = Minio(endpoint, access_key=access_key, secret_key=secret_key, secure=secure)
    object_key = f"quality/{uuid4()}.txt"
    data = b"learngrid quality smoke"
    try:
        if not client.bucket_exists(bucket):
            client.make_bucket(bucket)
        client.put_object(bucket, object_key, BytesIO(data), len(data), content_type="text/plain")
        stat = client.stat_object(bucket, object_key)
        assert stat.size == len(data)
        assert client.presigned_get_object(bucket, object_key)
    except S3Error as exc:
        pytest.skip(f"MinIO is not ready: {exc}")
    finally:
        try:
            client.remove_object(bucket, object_key)
        except Exception:
            pass
