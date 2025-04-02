import re
import json
import random
import datetime
from pytz import timezone
from typing import Callable, List, Tuple
from os.path import join, dirname

import discord

commands: dict = json.load(open(join(dirname(__file__), 'data', 'commands.json')))

embed_color = 0x5b7da6
error_color = 0x991a2d

# embed for bot errors
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

def loop_status(running: bool, next_run: datetime.datetime | None) -> discord.Embed:
    if next_run:
        cst = timezone("America/Chicago")
        next_run = next_run.astimezone(cst)
        next_str = next_run.strftime('%A, %B %d, %I:%M:%S %p %Z')
    else:
        next_str = None
    desc = f"**Running**: {running}\n\
    **Next Run**: {next_str}"
    a = discord.Embed(color=embed_color, title="Loop Status", description=desc)
    return a

def rss_embed(
        title: str,
        desc: str,
        link: str,
        date: datetime.datetime
    ) -> discord.Embed:
    link_re = re.compile(r'<a\s+[^>]*href=["\'](.*?)["\'][^>]*>(.*?)</a>', re.IGNORECASE)
    break_re = re.compile(r'<br\s*/?>', re.IGNORECASE)

    # Function to replace match with Markdown format
    def replacement(match):
        url, text = match.groups()
        return f'[{text}]({url})'

    # Perform substitution
    desc = break_re.sub("\n\n", desc)
    desc = link_re.sub(replacement, desc)

    return discord.Embed(
        color=embed_color,
        title=title,
        description=desc,
        timestamp=date,
        url=link
    )

async def admin_dashboard(client, starttime: datetime.datetime):
    app_info = await client.application_info()
    td = datetime.datetime.now() - starttime
    hours = td.seconds//3600
    minutes = (td.seconds//60)%60
    seconds = td.seconds - hours*3600 - minutes*60
    desc = f"**Name**: {app_info.name}\n\
    **Owner**: {app_info.owner}\n\
    **Command Prefix**: {client.command_prefix}\n\n\
    **Latency**: {client.latency:0.2f} Seconds\n\
    **Uptime**: `{td.days} Days {hours} Hours {minutes} Minutes {seconds} Seconds`"
    a = discord.Embed(color=embed_color, title="Admin Dashboard", description=desc)
    return a

def star_message(message: discord.Message, count: int):
    a = discord.Embed(
        title=message.author.display_name,
        color=embed_color,
        timestamp=datetime.datetime.now(),
        description=f":star: {count}"
    )
    a.set_thumbnail(url=message.author.display_avatar.url)
    a.add_field(
        name="Message:", 
        value=message.content + f"\n\n[Jump to message!]({message.jump_url})", 
        inline=False
    )
    attachments = []
    for attachment in message.attachments:
        if attachment.content_type in ('image/png', 'image/jpeg'):
            a.set_image(url=attachment.url)
        else:
            attachments.append(f"[{attachment.filename}]({attachment.url})")
    if attachments:
        a.add_field(name="Attachments: ", value="\n".join(attachments))
    return a

# format the help embed for specific command
def format_command(name: str, command: dict) -> discord.Embed:
    opts = [param['name'] for param in command['params']] if command['params'] else []
    cmdEmbed = discord.Embed(
        title=f"{name} ({', '.join(opts)})",
         color=embed_color,
         description=command["cmd_desc"]
    )
    if command["params"]:
        for param in command["params"]:
            value_format = f"**Type**: {param['type']}\n\
                **Data**: {param['data_type']}\n\
                **Optional**: {param['optional']}\n\
                **Description**: {param['description']}"
            if param.get("notes"):
                value_format += f"\n*Notes*: {param['notes']}"
            cmdEmbed.add_field(name=param["name"], value=value_format)

    cmdEmbed.add_field(name="Usage:", value="\n".join(command["usage"]), inline=False)

    return cmdEmbed

# help command, scalable through the commands.json file
def help_command(
    opt: str, 
    command_prefix: str, 
    about_me: str, 
    is_owner: bool = False
) -> Tuple[discord.Embed, discord.Embed | None]:

    messages = ["Help Has Arrived!", "At Your Service!"]

    if opt == 'general':
        cmdEmbed = discord.Embed(title=random.choice(messages), color=embed_color, description=about_me)
        for name, command in commands.items():
            if not command.get("hidden"):
                cmdEmbed.add_field(name=name, value=command.get("cmd_desc"), inline=False)
        cmdEmbed.set_footer(text= f"Bot Command Prefix = '{command_prefix}'")
        if is_owner:
            adminEmbed = discord.Embed(
                title="Admin Commands",
                color=embed_color,
                description="Commands for the owner to use."
            )
            for name, command in commands.items():
                if command.get("hidden") and is_owner:
                    adminEmbed.add_field(name=name, value=command.get("cmd_desc"), inline=False)
        else: adminEmbed = None

        return cmdEmbed, adminEmbed

    elif opt in commands:
        cmd = commands.get(opt, "")
        return format_command(opt, cmd), None # Known type checking error

    return bot_error("Not a valid command."), None

def random_messages(
    messages: List[Tuple[str, str | Callable[[], str], float]],
    content: str
):
    for trigger, response, probability in messages:
        if random.random() < probability and trigger in content:
            yield response() if callable(response) else response

