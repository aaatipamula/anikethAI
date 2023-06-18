import discord
import logging
import os
import traceback as tb
from datetime import time
from os.path import join, dirname
from dotenv import load_dotenv
from discord.abc import PrivateChannel
from discord.ext import commands, tasks
from anikethChain import create_aniketh_ai
from ext import cmd_error, help_command, bot_error, info_msg, topic_msg

# Declaring gateway intents, discord.py >= 2.0 feature
intent = discord.Intents().default()
intent.message_content = True

handler = logging.FileHandler(filename='discord.log', encoding='utf-8', mode='a')

dotenv_path = join(dirname(__file__), 'data', '.env')
load_dotenv(dotenv_path=dotenv_path)

DUMP_CHANNEL = int(os.environ.get("DUMP_CHANNEL", ""))
TOKEN = os.environ.get("TOKEN", "")
COMMAND_PREFIX = os.environ.get("COMMAND_PREFIX")
ABOUT_ME = os.environ.get("ABOUT_ME", "")

time = time(hour=15, minute=0)

client = commands.Bot(
        command_prefix=COMMAND_PREFIX if COMMAND_PREFIX else ".", 
        intents=intent, case_insensitive=True, 
        help_command=None
    )

# NOTE: temp solution
topics: set[str] = set()
topics_backup = {'lexus', 'mechanical keyboards', 'neon genesis evangelion', 'spotify', 'flowers', 'interstellar'}

@tasks.loop(time=time)
async def send_thought():
    chain = create_aniketh_ai()
    backup_warn = None
    if len(topics) >= 1:
        topic = topics.pop()
    else:
        topic = topics_backup.pop()
        backup_warn = "\n\n*This message was generated using a backup topic, please request more topics!*"
    message = chain.predict(topic=topic) + backup_warn if backup_warn else ""
    channel = client.get_channel(DUMP_CHANNEL)
    if channel and not isinstance(channel, PrivateChannel):
        await channel.send(message)

@client.event
async def on_ready():
    print('I am ready')
    send_thought.start()

@client.command()
async def request(ctx, topic: str):

    if len(topic) > 50:
        await ctx.send(cmd_error("Please keep topics under 50 characters."))
        return
    elif len(topics) > 30:
        await ctx.send(cmd_error("There are more than 30 topics in queue, please request a topic after one has been used."))
        return

    topic = topic.lower()
    
    if topic in topics:
        await ctx.send(info_msg("Topic is already in queue."))
    else:
        topics.add(topic)
        await ctx.send(info_msg(f"Added {topic} to queue."))

@client.command(name="topics")
async def list_topics(ctx):

    if len(topics) >= 1:
        await ctx.send(topic_msg(topics))
    else:
        await ctx.send(info_msg("There are no topics in queue."))

@client.command()
async def remove(ctx, topic: str):

    topic = topic.lower()

    if len(topic) > 50:
        await ctx.send(cmd_error("Please keep topics under 50 characters."))
        return
    if len(topics) <= 0:
        await ctx.send(cmd_error("There are not any topics in the queue, please "))

    if topic not in topics:
        await ctx.send(info_msg(f"The topic {topic} does not exist in the queue."))
    else:
        topics.remove(topic)
        await ctx.send(info_msg(f"Added {topic} to queue."))


# Redefined help command
@client.command()
async def help(ctx, opt="general"):
    await ctx.send(embed=help_command(opt, ctx.prefix, ABOUT_ME))

# General error handling for all commands, if a command does not have error handling explicitly called this function will handle all errors.
@client.event
async def on_command_error(ctx, err):
    if isinstance(err, commands.CommandNotFound):
        await ctx.send(embed=bot_error("Not a command!"))

    elif isinstance(err, commands.errors.MissingRequiredArgument):
        await ctx.send(embed=bot_error(str(err)))

    else:
        print(err)
        err_channel = client.get_channel(DUMP_CHANNEL)
        if err_channel:
            await err_channel.send(f"```Error: {err}\nMessage: {ctx.message.content}\nAuthor: {ctx.author}\nServer: {ctx.message.guild}\nLink: {ctx.message.jump_url}\nTraceback: {''.join(tb.format_exception(None, err, err.__traceback__))}```")

# A function that runs on every message sent.
@client.event
async def on_message(message):

    # Ignores if user is client (self), generally good to have in this function.
    if message.author == client.user:
        return

    # Process any commands before on message event is processed
    await client.process_commands(message)

if __name__ == '__main__':
    client.run(TOKEN, log_handler=handler)
