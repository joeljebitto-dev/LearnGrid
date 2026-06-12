from __future__ import annotations

from typing import Any


def consumer_lag_report(
    *, bootstrap_servers: str, group_id: str, topics: list[str] | None = None
) -> dict[str, Any]:
    from kafka import KafkaAdminClient, KafkaConsumer, TopicPartition

    consumer = KafkaConsumer(
        bootstrap_servers=bootstrap_servers.split(","),
        group_id=group_id,
        enable_auto_commit=False,
    )
    admin = KafkaAdminClient(bootstrap_servers=bootstrap_servers.split(","))
    try:
        selected_topics = topics or list(consumer.topics())
        partitions = []
        for topic in selected_topics:
            for partition in consumer.partitions_for_topic(topic) or []:
                partitions.append(TopicPartition(topic, partition))
        end_offsets = consumer.end_offsets(partitions) if partitions else {}
        group_offsets = {
            topic_partition: offset_metadata.offset
            for topic_partition, offset_metadata in admin.list_consumer_group_offsets(
                group_id
            ).items()
        }
        rows = []
        total_lag = 0
        for partition in partitions:
            current_offset = group_offsets.get(partition, 0) or 0
            end_offset = end_offsets.get(partition, 0) or 0
            lag = max(end_offset - current_offset, 0)
            total_lag += lag
            rows.append(
                {
                    "topic": partition.topic,
                    "partition": partition.partition,
                    "current_offset": current_offset,
                    "end_offset": end_offset,
                    "lag": lag,
                }
            )
        return {"group": group_id, "total_lag": total_lag, "partitions": rows}
    finally:
        consumer.close()
        admin.close()
