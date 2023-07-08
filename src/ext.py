import json
import random
from typing import Iterable
from os.path import join, dirname
import discord

commands = json.load(open(join(dirname(__file__), 'data', 'commands.json')))

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

def topic_msg(topics: Iterable[str]):
    desc = "\n".join(topics)
    a = discord.Embed(color=embed_color, title="Topics in queue:", description=desc)
    return a 

# format the help embed for specific command
def format_command(name: str, command: dict) -> discord.Embed:
    opts = [option['name'] for option in command['options']]
    cmdEmbed = discord.Embed(
        title=f"{name} ({', '.join(opts)})", 
         color=embed_color, 
         description=command["description"]
    )
    if command["options"]:
        for option in command["options"]:
            cmdEmbed.add_field(name=option["name"], value=option["description"])

    return cmdEmbed

# help command, scalable through the commands.json file
def help_command(opt: str, command_prefix: str, about_me: str) -> discord.Embed:

    messages = ["Help Has Arrived!", "At Your Service!"]

    if opt == 'general':
        cmdEmbed = discord.Embed(title=random.choice(messages), color=embed_color, description=about_me)
        for command in commands:
            cmdEmbed.add_field(name=command, value="\u200b", inline=False)
        cmdEmbed.set_footer(text= f"Bot Command Prefix = '{command_prefix}'")
        return cmdEmbed

    elif opt in commands:
        cmd = commands.get(opt)
        return format_command(opt, cmd)

    return bot_error("Not a valid command.")

