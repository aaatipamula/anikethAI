import os
import sys
import discord
import logging
import traceback as tb
from datetime import time
from typing import Literal, Optional, Union, Tuple
from dotenv import load_dotenv
from os.path import join, dirname
from discord.abc import PrivateChannel
from discord.ext import commands, tasks
from anikethChain import create_aniketh_ai
from ext import cmd_error, help_command, bot_error, info_msg, topic_msg
from topicQueue import QueueError, IndexError, TopicQueue

# NOTE: SETUP
# Declaring gateway intents, discord.py >= 2.0 feature
intent = discord.Intents().default()
intent.message_content = True

handler = logging.StreamHandler(stream=sys.stdout)

dotenv_path = join(dirname(__file__), 'data', '.env')
load_dotenv(dotenv_path=dotenv_path)

DUMP_CHANNEL = int(os.environ.get("DUMP_CHANNEL", ""))
TOKEN = os.environ.get("TOKEN", "")
COMMAND_PREFIX = os.environ.get("COMMAND_PREFIX")
ABOUT_ME = os.environ.get("ABOUT_ME", "")
LOCK = False

time = time(hour=15, minute=0)
client = commands.Bot(
    command_prefix=COMMAND_PREFIX if COMMAND_PREFIX else ".",
    intents=intent, case_insensitive=True,
    help_command=None
)

preload_topics = [
    'neon genesis evangelion',
    'stuff',
    'more stuff',
    'blah',
    'word'
]

# Convert Flag arguments for the remove command
class RemoveFlags(commands.FlagConverter):
    span: Tuple[int, int] = None # Known type checking error
    topic: Optional[str]

queue = TopicQueue(preload=preload_topics)
# NOTE: END SETUP

@client.check
async def is_locked(ctx):
    if await client.is_owner(ctx.author):
        return True

    return not LOCK

@tasks.loop(time=time)
async def send_thought(topic: Optional[str] = None):
    global queue
    chain = create_aniketh_ai()
    topic = topic if topic else queue.pick_topic()
    message = chain.predict(topic=topic)
    channel = client.get_channel(DUMP_CHANNEL)
    if channel and not isinstance(channel, PrivateChannel):
        await channel.send(message)

@client.event
async def on_ready():
    print('I am ready')
    send_thought.start()

@client.command()
async def request(ctx, *, topic):
    global queue

    topic = topic.lower()
    queue.add_topic(topic)

    await ctx.send(embed=info_msg(f"Added {topic} to queue."))

@client.command(name="rm")
async def remove(ctx, topics: commands.Greedy[int], *, flags: RemoveFlags):
    global queue

    embeds = []

    _topics = queue.remove_range(*flags.span) if flags.span else []
    _topics += [queue.remove_topic_name(flags.topic)] if flags.topic else []
    _t, _errors = queue.remove_topics(topics)
    _topics += _t

    if _errors:
        error_str = "\n".join(_errors)
        embeds.append(cmd_error((f"The Following Errors Occured:\n\n{error_str}")))

    if _topics:
        topic_str = "\n".join(_topics)
        embeds.append(info_msg(f"Removed the Following:\n\n{topic_str}"))
    else:
        raise commands.errors.UserInputError("No arguments were parsed, please refer to the help manual.")


    await ctx.send(embeds=embeds)


@client.command(name="topics")
async def list_topics(ctx):
    global queue
    await ctx.send(embed=topic_msg(queue.topics))

@client.command()
@commands.is_owner()
async def thought(ctx, topic: Optional[str] = None):
    await send_thought(topic)

@client.command()
@commands.is_owner()
async def lock(ctx):
    global LOCK
    if LOCK:
        await ctx.send(embed=cmd_error("Commands already locked."))
    else:
        LOCK = True
        await ctx.send(embed=info_msg("Commands are now locked."))

@client.command()
@commands.is_owner()
async def unlock(ctx):
    global LOCK
    if not LOCK:
        await ctx.send(embed=cmd_error("Commands are already unlocked."))
    else:
        LOCK = False
        await ctx.send(embed=info_msg("Commands are now unlocked."))

# Redefined help command.
@client.command()
async def help(ctx, opt="general"):
    is_owner = await client.is_owner(ctx.author)
    await ctx.send(embed=help_command(opt, ctx.prefix, ABOUT_ME, is_owner=is_owner))

# General error handling for all commands.
# NOTE: Change this soon
@client.event
async def on_command_error(ctx, err):
    if isinstance(err, commands.CommandNotFound):
        await ctx.send(embed=bot_error("Not a command!"))

    elif isinstance(err, commands.errors.MissingRequiredArgument):
        await ctx.send(embed=cmd_error(str(err)))

    elif isinstance(err, commands.errors.UserInputError):
        await ctx.send(embed=cmd_error(str(err)))

    elif isinstance(err, QueueError):
        await ctx.send(embed=cmd_error(str(err)))

    elif isinstance(err, commands.errors.CheckFailure):
        await ctx.send(embed=cmd_error("Commands are currently locked."))

    elif isinstance(err, commands.errors.NotOwner):
        await ctx.send(embed=cmd_error("You are not allowed to use this command."))

    elif isinstance(err, commands.errors.BadArgument):
        await ctx.send(embed=cmd_error("You likely used an argument wrong, refer to the documentation for this command."))

    else:
        print(err)
        err_channel = client.get_channel(DUMP_CHANNEL)
        if err_channel:
            await err_channel.send(f"```Error: {err}\nMessage: {ctx.message.content}\nAuthor: {ctx.author}\nServer: {ctx.message.guild}\nLink: {ctx.message.jump_url}\nTraceback: {''.join(tb.format_exception(None, err, err.__traceback__))}```")
            return

if __name__ == '__main__':
    client.run(TOKEN, log_handler=handler)
