import pytz
import random
from datetime import datetime, time
from typing import List, Tuple, Callable, Annotated

MessageValues = Tuple[str, str | Callable[[], str], float]
LowerStr = Annotated[str, lambda x: x.lower()]

def random_messages(messages: List[MessageValues], content: str):
    for trigger, response, probability in messages:
        if random.random() < probability and trigger in content:
            yield response() if callable(response) else response

def normalize_tz(timezone: str, start_hour: int):
    try:
        tz = pytz.timezone(timezone)
    except pytz.UnknownTimeZoneError:
        tz = pytz.utc

    # Create a dummy datetime and localize it.
    dummy_date = datetime(2000, 1, 1, start_hour, 0)  # January 1, 2000
    local_tzinfo = tz.localize(dummy_date).tzinfo

    return (
        time(hour=start_hour, tzinfo=local_tzinfo),
        time(hour=(start_hour + 6) % 24, tzinfo=local_tzinfo),
        time(hour=(start_hour + 12) % 24, tzinfo=local_tzinfo),
        time(hour=(start_hour + 18) % 24, tzinfo=local_tzinfo),
    )

