import os
import sys
import traceback as tb
from typing import Optional, Tuple
import asyncio
from datetime import datetime

from sqlalchemy.engine import create


from anikethChain import create_aniketh_ai
from topicQueue import QueueError, TopicQueue
from database import BaseModel, dump_user_mem, get_user_mem, engine
from ext import (
    cmd_error,
    help_command,
    bot_error,
    info_msg,
    topic_msg,
    loop_status,
    admin_dashboard
)

import discord
import logging
from datetime import time
from dotenv import load_dotenv
from os.path import join, dirname
from discord.ext import commands, tasks
from langchain.memory import ConversationBufferWindowMemory

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
START_DATETIME = datetime.now()

# how many hours to wait inbetween loops
waitTime = time(hour=15, minute=0)
client = commands.Bot(
    command_prefix=COMMAND_PREFIX if COMMAND_PREFIX else ".",
    intents=intent, case_insensitive=True,
    help_command=None
)

preload_topics = [
    'neon genesis evangelion',
    'relationships',
    'san francisco'
]

# Convert Flag arguments for the remove command
class RemoveFlags(commands.FlagConverter):
    span: Tuple[int, int] = None # Known type checking error
    topic: Optional[str]

queue = TopicQueue(preload=preload_topics)

# Create the user db
BaseModel.metadata.create_all(engine)
# NOTE: END SETUP

@client.check
async def is_locked(ctx):
    if await client.is_owner(ctx.author):
        return True

    return not LOCK

# NOTE: Deprecated
@tasks.loop(time=waitTime)
async def send_thought(topic: Optional[str] = None):
    global queue
    channel = client.get_channel(DUMP_CHANNEL)
    async with channel.typing(): # Known type checking error
        chain = create_aniketh_ai(ConversationBufferWindowMemory())
        topic = topic if topic else queue.pick_topic()
        message = chain.predict(user_message=f"What are your thoughts on {topic}")
    await channel.send(f"**Topic**: {topic}\n" + message) # Known type checking error

@client.event
async def on_ready():
    print('I am ready')
    # Deprecated
    # send_thought.start()

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

# Redefined help command.
@client.command()
async def help(ctx, opt="general"):
    is_owner = await client.is_owner(ctx.author)
    embeds = help_command(opt, ctx.prefix, ABOUT_ME, is_owner=is_owner)
    await ctx.send(embeds=embeds)

###################################
# Admin Commands and Sub Commands #
###################################

@client.group()
@commands.is_owner()
async def admin(ctx):
    if not ctx.invoked_subcommand:
        embed = await admin_dashboard(client, START_DATETIME)
        await ctx.send(embed=embed)

@admin.command(name="stopl")
async def stop_loop(ctx):
    if send_thought.is_running():
        send_thought.cancel()
    else:
        await ctx.send(embed=cmd_error("Task is already stopped."))
        return
    await ctx.send(embed=info_msg("Stopped sending daily thoughts."))

@admin.command(name="startl")
async def start_loop(ctx):
    await ctx.send(embed=cmd_error("WARNING: This loop is deprecated!!"))
    if send_thought.is_running():
        await ctx.send(embed=cmd_error("Task is already running."))
        return
    else:
        send_thought.start()
    await ctx.send(embed=info_msg("Started sending daily thoughts."))

@admin.command(name="statusl")
async def status_loop(ctx):
    embed = loop_status(send_thought.is_running(), send_thought.next_iteration) # Known type checking error
    await ctx.send(embed=embed)

@admin.command(name="kill")
async def kill_bot(ctx):
    await ctx.send(f"NOOOOO PLEASE {client.get_emoji(1145147159260450907)}") # :cri: emoji

    def check(reaction, user):
        return client.is_owner(user) and reaction.emoji == client.get_emoji(1136812895859134555) #:L_: emoji

    try:
        await client.wait_for("reaction_add", timeout=10.0, check=check)
    except asyncio.TimeoutError:
        await ctx.send(client.get_emoji(994378239675990029))
    else:
        await ctx.send(client.get_emoji(1145090024333918320))
        exit()

@admin.command()
async def lock(ctx):
    global LOCK
    if LOCK:
        await ctx.send(embed=cmd_error("Commands already locked."))
    else:
        LOCK = True
        await ctx.send(embed=info_msg("Commands are now locked."))

@admin.command()
async def unlock(ctx):
    global LOCK
    if not LOCK:
        await ctx.send(embed=cmd_error("Commands are already unlocked."))
    else:
        LOCK = False
        await ctx.send(embed=info_msg("Commands are now unlocked."))

@client.event
async def on_message(message: discord.Message):

    # ignore if self
    if message.author == client.user:
        return

    await client.process_commands(message)

    if client.user.mentioned_in(message): # known type error
        async with message.channel.typing():
            mem = get_user_mem(message.author.id)
            chain = create_aniketh_ai(mem)
            msg = chain.predict(user_message=message.clean_content)
            dump_user_mem(message.author.id, mem)
        await message.channel.send(msg)

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
        await ctx.send(embed=cmd_error("You are not allowed to use this command."))

    elif isinstance(err, commands.errors.NotOwner):
        await ctx.send(embed=cmd_error("You are not allowed to use this command."))

    elif isinstance(err, commands.errors.BadArgument):
        await ctx.send(embed=cmd_error("You likely used an argument wrong, refer to the documentation for this command."))

    else:
        print(err)
        err_channel = client.get_channel(DUMP_CHANNEL)
        if err_channel:
            # Known type checking error
            await err_channel.send(f"```Error: {err}\n\
                Message: {ctx.message.content}\n\
                Author: {ctx.author}\n\
                Server: {ctx.message.guild}\n\
                Link: {ctx.message.jump_url}\n\
                Traceback: {''.join(tb.format_exception(None, err, err.__traceback__))}```")

if __name__ == '__main__':
    client.run(TOKEN, log_handler=handler)
