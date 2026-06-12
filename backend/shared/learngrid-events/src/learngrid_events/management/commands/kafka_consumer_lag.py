from __future__ import annotations

import json

from django.conf import settings
from django.core.management.base import BaseCommand

from learngrid_events.monitoring import consumer_lag_report


class Command(BaseCommand):
    help = "Print Kafka consumer lag as JSON."

    def add_arguments(self, parser):
        parser.add_argument("--group", required=True)
        parser.add_argument("--topic", action="append", dest="topics")

    def handle(self, *args, **options):
        report = consumer_lag_report(
            bootstrap_servers=getattr(settings, "KAFKA_BOOTSTRAP_SERVERS", "127.0.0.1:9092"),
            group_id=options["group"],
            topics=options.get("topics"),
        )
        self.stdout.write(json.dumps(report, sort_keys=True))
