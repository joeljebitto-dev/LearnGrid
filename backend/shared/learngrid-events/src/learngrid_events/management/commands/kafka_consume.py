from __future__ import annotations

import json

from django.conf import settings
from django.core.management.base import BaseCommand

from learngrid_events.adapters import KafkaProducerAdapter, decode_headers
from learngrid_events.consumer import consume_event
from learngrid_events.handlers import load_handler


class Command(BaseCommand):
    help = "Consume Kafka events with a configured LearnGrid handler."

    def add_arguments(self, parser):
        parser.add_argument("--topic", required=True)
        parser.add_argument("--group", required=True)
        parser.add_argument("--handler", required=True)
        parser.add_argument("--max-messages", type=int, default=0)

    def handle(self, *args, **options):
        from kafka import KafkaConsumer

        bootstrap_servers = getattr(settings, "KAFKA_BOOTSTRAP_SERVERS", "127.0.0.1:9092")
        handler = load_handler(options["handler"])
        producer_adapter = KafkaProducerAdapter(
            bootstrap_servers=bootstrap_servers,
            client_id=f"{options['group']}-retry-producer",
        )
        consumer = KafkaConsumer(
            options["topic"],
            bootstrap_servers=bootstrap_servers.split(","),
            group_id=options["group"],
            enable_auto_commit=False,
            value_deserializer=lambda value: json.loads(value.decode("utf-8")),
        )
        max_messages = options["max_messages"]
        seen = 0
        try:
            for message in consumer:
                result = consume_event(
                    topic=options["topic"],
                    event=message.value,
                    handler=handler,
                    adapter=producer_adapter,
                    headers=decode_headers(message.headers),
                    max_retry_attempts=getattr(settings, "KAFKA_MAX_RETRY_ATTEMPTS", 3),
                )
                consumer.commit()
                seen += 1
                self.stdout.write(json.dumps(result.__dict__, sort_keys=True))
                if max_messages and seen >= max_messages:
                    break
        finally:
            consumer.close()
            producer_adapter.close()
