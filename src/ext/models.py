from typing import TypedDict, NotRequired


class CommandParam(TypedDict):
    name: str
    optional: bool
    default: NotRequired[str]
    data_type: str
    description: str
    notes: NotRequired[str | None]


class CommandHelp(TypedDict):
    hidden: bool
    has_helptext: NotRequired[bool]
    cmd_desc: str
    params: list[CommandParam] | None
    usage: list[str]
