import json
import random
from typing import List
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

def topic_msg(topics: List[str]):
    desc = "\n".join([f"{num}. {topic}" for num, topic in enumerate(topics)])
    a = discord.Embed(color=embed_color, title="Topics in queue:", description=desc)
    return a

# format the help embed for specific command
def format_command(name: str, command: dict) -> discord.Embed:
    opts = [param['name'] for param in command['params']]
    cmdEmbed = discord.Embed(
        title=f"{name} ({', '.join(opts)})",
         color=embed_color,
         description=command["cmd_desc"]
    )
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
def help_command(opt: str, command_prefix: str, about_me: str, is_owner: bool = False) -> discord.Embed:

    messages = ["Help Has Arrived!", "At Your Service!"]

    if opt == 'general':
        cmdEmbed = discord.Embed(title=random.choice(messages), color=embed_color, description=about_me)
        for name, command in commands.items():
            if is_owner:
                cmdEmbed.add_field(name=name, value=command.get("cmd_desc"), inline=False)
            elif not command.get("hidden"):
                cmdEmbed.add_field(name=name, value=command.get("cmd_desc"), inline=False)
        cmdEmbed.set_footer(text= f"Bot Command Prefix = '{command_prefix}'")
        return cmdEmbed

    elif opt in commands:
        cmd = commands.get(opt)
        return format_command(opt, cmd) # Known type checking error

    return bot_error("Not a valid command.")

