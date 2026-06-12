from __future__ import annotations

import json

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError

from learngrid_events.adapters import KafkaProducerAdapter, decode_headers, encode_headers
from learngrid_events.topics import retry_topic


class Command(BaseCommand):
    help = "Replay one event from a dead-letter topic to its retry topic."

    def add_arguments(self, parser):
        parser.add_argument("--topic", required=True)
        parser.add_argument("--event-id", required=True)
        parser.add_argument("--max-scan", type=int, default=500)

    def handle(self, *args, **options):
        from kafka import KafkaConsumer

        bootstrap_servers = getattr(settings, "KAFKA_BOOTSTRAP_SERVERS", "127.0.0.1:9092")
        producer = KafkaProducerAdapter(
            bootstrap_servers=bootstrap_servers,
            client_id=f"{getattr(settings, 'SERVICE_NAME', 'learngrid')}-dlq-retry",
        )
        consumer = KafkaConsumer(
            options["topic"],
            bootstrap_servers=bootstrap_servers.split(","),
            group_id=None,
            enable_auto_commit=False,
            auto_offset_reset="earliest",
            consumer_timeout_ms=5000,
            value_deserializer=lambda value: json.loads(value.decode("utf-8")),
        )
        try:
            for index, message in enumerate(consumer):
                if index >= options["max_scan"]:
                    break
                if str(message.value.get("event_id")) != options["event_id"]:
                    continue
                headers = decode_headers(message.headers)
                original_topic = headers.get("x-original-topic") or options["topic"].removesuffix(
                    ".dlq"
                )
                producer.send(
                    retry_topic(original_topic),
                    message.value,
                    key=message.value["aggregate_id"],
                    headers=encode_headers(
                        {
                            "x-retry-attempt": 0,
                            "x-original-topic": original_topic,
                            "x-replayed-from-dlq": "true",
                        }
                    ),
                )
                self.stdout.write(
                    json.dumps(
                        {
                            "status": "replayed",
                            "event_id": options["event_id"],
                            "topic": retry_topic(original_topic),
                        },
                        sort_keys=True,
                    )
                )
                return
        finally:
            consumer.close()
            producer.close()
        raise CommandError(f"Event {options['event_id']} was not found in {options['topic']}.")
