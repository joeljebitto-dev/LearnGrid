from __future__ import annotations

from enum import StrEnum


class TopicName(StrEnum):
    USER = "user.events"
    COURSE = "course.events"
    ENROLLMENT = "enrollment.events"
    CONTENT = "content.events"
    PROGRESS = "progress.events"
    ASSESSMENT = "assessment.events"
    GRADING = "grading.events"
    NOTIFICATION = "notification.events"
    AUDIT = "audit.events"
    ANALYTICS = "analytics.events"


BASE_TOPICS = tuple(topic.value for topic in TopicName)
RETRY_TOPICS = tuple(f"{topic}.retry" for topic in BASE_TOPICS)
DEAD_LETTER_TOPICS = tuple(f"{topic}.dlq" for topic in BASE_TOPICS)
ALL_TOPICS = BASE_TOPICS + RETRY_TOPICS + DEAD_LETTER_TOPICS

TOPIC_BY_SERVICE = {
    "auth-service": TopicName.AUDIT.value,
    "user-service": TopicName.USER.value,
    "course-service": TopicName.COURSE.value,
    "content-service": TopicName.CONTENT.value,
    "enrollment-service": TopicName.ENROLLMENT.value,
    "progress-service": TopicName.PROGRESS.value,
    "assessment-service": TopicName.ASSESSMENT.value,
    "grading-service": TopicName.GRADING.value,
    "notification-service": TopicName.NOTIFICATION.value,
    "analytics-service": TopicName.ANALYTICS.value,
}


def retry_topic(topic: str) -> str:
    base_topic = base_topic_name(topic)
    return f"{base_topic}.retry"


def dead_letter_topic(topic: str) -> str:
    base_topic = base_topic_name(topic)
    return f"{base_topic}.dlq"


def base_topic_name(topic: str) -> str:
    if topic.endswith(".retry"):
        return topic.removesuffix(".retry")
    if topic.endswith(".dlq"):
        return topic.removesuffix(".dlq")
    return topic
