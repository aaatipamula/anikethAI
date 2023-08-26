from typing import Optional, List, Tuple
from discord.ext.commands import CommandError
from random import choice

class QueueError(CommandError):
    pass

class EmptyQueue(QueueError):
    pass

class FullQueue(QueueError):
    pass

class InQueue(QueueError):
    pass

class OutQueue(QueueError):
    pass

class LengthError(QueueError):
    pass

class IndexError(QueueError):
    num: int

class TopicQueue:
    """A simple class to make queueing topics easier."""

    def __init__(self, preload: Optional[List[str]] = None) -> None:
        self._topics: list[str] = preload if preload else []

    @property
    def length(self) -> int:
        """The number of topics in queue."""
        return len(self._topics)

    @property
    def topics(self) -> list[str]:
        """A list of topics avalible."""
        if self.length <= 0:
            raise EmptyQueue("There are not any topics in the queue.")

        return self._topics

    def flush_queue(self) -> None:
        """Clean out all the empty strings."""
        self._topics = [topic for topic in self._topics if topic != ""]

    def valid_index(self, index: int) -> bool:
        """If index is within the bounds of 1 to the lenth of the topic list."""
        return index >= 1 and index <= self.length

    def remove_topics(self, topics: List[int]) -> Tuple[List[str], List[str]]:
        """Remove a list of topics from an index. Numbering starts at one instead of 0."""
        _topics, _errors = [], []

        for index in topics:
            if self.valid_index(index):
                _topics.append(self._topics[index - 1])
                self._topics[index - 1] = ""
            else:
                _errors.append(f"{index} is not a valid index.")

        self.flush_queue()
        return _topics, _errors

    def remove_range(self, start: int, end: int) -> List[str]:
        """Remove a range of topics. Index starts at 1 and includes the start and end index."""
        if self.valid_index(start) and self.valid_index(end):
            removed = self._topics[start-1:end]
            # Filter the topics by ones that are not in the given range.
            self._topics = [val for index, val in enumerate(self._topics, 1) if index not in range(start, end+1)]
        else:
            if self.valid_index(start):
                index = end
            else:
                index = start
            raise IndexError(f"{index} is not a valid index.")

        return removed

    def remove_topic_name(self, topic: str) -> str:
        """Remove a topic, raise error if invalid."""
        if len(topic) > 50:
            raise LengthError("Topics must be under 50 characters.")
        elif topic not in self._topics:
            raise OutQueue("Topic does not exist in queue.")

        self._topics.remove(topic)
        return topic

    def add_topic(self, topic: str) -> None:
        """Add a topic, raise error if invalid."""
        if len(topic) > 50:
            raise LengthError("Topics must be under 50 characters.")
        elif topic in self._topics:
            raise InQueue("Topic is already in queue.")
        elif len(self._topics) > 30:
            raise FullQueue("Cannot add more topics!")

        self._topics.append(topic)


    def pick_topic(self) -> str:
        """Pick a random topic and remove it from the list. Generate one if it doesn't exist."""
        try:
            topic = choice(self.topics)
            self.remove_topic_name(topic)
        except EmptyQueue:
            # NOTE: Temporary, come up with a system to generate a topic based on trends
            topic = "come up with your own"

        return topic

