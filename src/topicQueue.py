from typing import Iterable, Optional
from random import choice

class QueueError(BaseException): ...

class EmptyQueue(QueueError): ...

class FullQueue(QueueError): ...

class InQueue(QueueError): ...

class OutQueue(QueueError): ...

class LengthError(ValueError): ...

class TopicQueue:
    """A simple wrapper to make queueing topics easier."""

    def __init__(self, preload: Optional[Iterable[str]] = None) -> None:
        self._backup_topics = list(preload) if preload else None
        self._topics: list[str] = list()

    @property
    def backup_topics(self) -> list[str]:
        """The topics property."""
        if not self._backup_topics:
            raise EmptyQueue
        return self._topics

    @property
    def topics(self) -> list[str]:
        """The topics property."""
        if len(self._topics) <= 0:
            raise EmptyQueue
        return self._topics

    def add_topic(self, topic: str) -> None:
        if len(topic) > 50:
            raise LengthError
        elif len(self._topics) > 30:
            raise FullQueue
        elif topic in self._topics:
            raise InQueue

        self._topics.append(topic)

    def remove_topic(self, topic: str) -> None:
        if len(topic) > 50:
            raise LengthError
        elif len(self._topics) <= 0:
            raise EmptyQueue
        elif topic not in self._topics:
            raise OutQueue

        self._topics.remove(topic)

    def pick_topic(self) -> str:
        try:
            topic = choice(self.topics)
            self.remove_topic(topic)
        except EmptyQueue:
            topic = choice(self.backup_topics)

        return topic

