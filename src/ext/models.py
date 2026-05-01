from typing import TypedDict


class CommandParam(TypedDict):
    name: str
    optional: bool
    type: str
    data_type: str
    description: str
    notes: str | None


class CommandHelp(TypedDict):
    hidden: bool
    cmd_desc: str
    params: list[CommandParam] | None
    usage: list[str]
