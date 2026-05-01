import datetime
import json
import random
from pathlib import Path
from pytz import timezone
from typing import List, Tuple

import discord

from ext.html_parser import HtmlToMarkdown
from ext.models import CommandHelp


commands_json = Path() / "src/data/commands.json"
commands: dict[str, CommandHelp] = json.load(open(commands_json))

embed_color = 0x5B7DA6
error_color = 0x991A2D


####################
#  Generic Embeds  #
####################


def bot_error(desc: str):
    a = discord.Embed(color=error_color, title="Bot Error", description=desc)
    return a


def cmd_error(desc: str):
    a = discord.Embed(color=error_color, title="Command Error", description=desc)
    return a


def info_msg(desc: str):
    a = discord.Embed(color=embed_color, title="Info", description=desc)
    return a


def topic_msg(topics: List[str]) -> discord.Embed:
    desc = "\n".join([f"{num}. {topic}" for num, topic in enumerate(topics)])
    a = discord.Embed(color=embed_color, title="Topics in queue:", description=desc)
    return a



###########
#  Tasks  #
###########


def loop_status(
    name: str, running: bool, next_run: datetime.datetime | None
) -> discord.Embed:
    if next_run:
        cst = timezone("America/Chicago")
        next_run = next_run.astimezone(cst)
        next_str = next_run.strftime("%A, %B %d, %I:%M:%S %p %Z")
    else:
        next_str = None
    desc = f"**Running**: {running}\n\
    **Next Run**: {next_str}"
    a = discord.Embed(color=embed_color, title=name, description=desc)
    return a


def rss_embed(
    post: dict[str, str], timestamp: datetime.datetime, post_id: str
) -> discord.Embed:
    desc = HtmlToMarkdown.parse_html(post.get("description", ""))

    # Create the discord embed
    a = discord.Embed(
        color=embed_color,
        title=post.get("title", "N/A"),
        description=desc,
        timestamp=timestamp,
        url=post.get("link"),
    )

    a.set_footer(text=post_id)

    # Get Object items
    for item in post.get("enclosures", []):
        assert isinstance(item, dict)
        if item.get("type", "").startswith("image/"):
            a.set_image(url=item.get("url") or item.get("href") or item.get("src"))
            break

    return a


###########
#  Admin  #
###########


async def admin_dashboard(client, starttime: datetime.datetime):
    app_info = await client.application_info()
    td = datetime.datetime.now() - starttime
    hours = td.seconds // 3600
    minutes = (td.seconds // 60) % 60
    seconds = td.seconds - hours * 3600 - minutes * 60
    desc = f"**Name**: {app_info.name}\n\
    **Owner**: {app_info.owner}\n\
    **Command Prefix**: {client.command_prefix}\n\n\
    **Latency**: {client.latency:0.2f} Seconds\n\
    **Uptime**: `{td.days} Days {hours} Hours {minutes} Minutes {seconds} Seconds`"
    a = discord.Embed(color=embed_color, title="Admin Dashboard", description=desc)
    return a


##############
#  Counting  #
##############


def counting_err(reason: str, correct_count: int, high_score: int) -> discord.Embed:
    a = discord.Embed(color=error_color, title=reason)
    a.add_field(name="Correct Count", value=correct_count, inline=False)
    a.add_field(name="High Score", value=high_score, inline=False)
    return a


#############
#  Banking  #
#############


def bank_embed(moners: int, last_reloaded: datetime.datetime):
    next_reload_time = last_reloaded + datetime.timedelta(days=1)
    next_reload_str = next_reload_time.strftime("%A, %B %d, %I:%M:%S %p %Z")

    desc = f"**Balance**: ${moners:,d}\n**Next Reload Time**: {next_reload_str}"

    a = discord.Embed(
        title="Bank Account 💰",
        description=desc,
        color=0x7BD389,
    )

    if moners > 1_000_000:
        a.set_thumbnail(url="")

    elif 500_000 < moners <= 999_999:
        a.set_thumbnail(url="")

    elif 100_000 < moners <= 499_999:
        a.set_thumbnail(url="")

    elif 50_000 < moners <= 99_999:
        a.set_thumbnail(url="")

    elif 10_000 < moners <= 49_999:
        a.set_thumbnail(url="")

    elif 500 < moners <= 9999:
        a.set_thumbnail(url="")

    elif 100 < moners <= 499:
        a.set_thumbnail(url="")

    elif 50 < moners <= 99:
        a.set_thumbnail(url="")

    elif 10 < moners <= 49:
        a.set_thumbnail(url="")

    else:
        a.set_thumbnail(url="")

    return a


################
#  Star Board  #
################


def star_message(message: discord.Message, count: int):
    a = discord.Embed(
        title=message.author.display_name,
        color=embed_color,
        timestamp=datetime.datetime.now(),
        description=f":star: {count}",
    )
    a.set_thumbnail(url=message.author.display_avatar.url)
    a.add_field(
        name="Message:",
        value=message.content + f"\n\n[Jump to message!]({message.jump_url})",
        inline=False,
    )
    attachments = []
    for attachment in message.attachments:
        if attachment.content_type in ("image/png", "image/jpeg"):
            a.set_image(url=attachment.url)
        else:
            attachments.append(f"[{attachment.filename}]({attachment.url})")
    if attachments:
        a.add_field(name="Attachments: ", value="\n".join(attachments))
    return a


###################
#  Help Commands  #
###################


# format the help embed for specific command
def format_command(name: str, command: CommandHelp, prefix: str) -> discord.Embed:
    opts = [param["name"] for param in command["params"]] if command["params"] else []
    cmdEmbed = discord.Embed(
        title=f"{name} ({', '.join(opts)})",
        color=embed_color,
        description=command["cmd_desc"],
    )
    if command["params"]:
        for param in command["params"]:
            value_format = f"**Type**: {param['type']}\n\
                **Data**: {param['data_type']}\n\
                **Optional**: {param['optional']}\n\
                **Description**: {param['description']}"
            if param.get("notes"):
                value_format += f"\n**Notes**: {param['notes']}"
            cmdEmbed.add_field(name=param["name"], value=value_format)

    usageStr = ""
    for usage in command["usage"]:
        usageStr += f"`{prefix}{usage}`\n"

    cmdEmbed.add_field(name="Usage:", value=usageStr, inline=False)

    return cmdEmbed


# help command, scalable through the commands.json file
def help_command(
    opt: str, command_prefix: str, about_me: str, is_owner: bool = False
) -> Tuple[discord.Embed, discord.Embed | None]:

    messages = ["Help Has Arrived!", "At Your Service!"]

    if opt == "general":
        cmdEmbed = discord.Embed(
            title=random.choice(messages), color=embed_color, description=about_me
        )
        for name, command in commands.items():
            if not command.get("hidden"):
                cmdEmbed.add_field(
                    name=name, value=command.get("cmd_desc"), inline=False
                )
        cmdEmbed.set_footer(text=f"Bot Command Prefix = '{command_prefix}'")
        if is_owner:
            adminEmbed = discord.Embed(
                title="Admin Commands",
                color=embed_color,
                description="Commands for the owner to use.",
            )
            for name, command in commands.items():
                if command.get("hidden") and is_owner:
                    adminEmbed.add_field(
                        name=name, value=command.get("cmd_desc"), inline=False
                    )
        else:
            adminEmbed = None

        return cmdEmbed, adminEmbed

    elif opt in commands:
        cmd = commands.get(opt)
        assert cmd is not None
        return format_command(
            opt, cmd, command_prefix
        ), None

    return bot_error("Not a valid command."), None
