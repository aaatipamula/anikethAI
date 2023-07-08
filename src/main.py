import os
import sys
import discord
import logging
import traceback as tb
from datetime import time
from typing import Optional
from dotenv import load_dotenv
from os.path import join, dirname
from discord.abc import PrivateChannel
from discord.ext import commands, tasks
from anikethChain import create_aniketh_ai
from ext import cmd_error, help_command, bot_error, info_msg, topic_msg
from topicQueue import FullQueue, InQueue, EmptyQueue, OutQueue, LengthError, TopicQueue

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
    'lexus', 
    'mechanical keyboards', 
    'neon genesis evangelion', 
    'python the coding language', 
    'flowers', 
    'interstellar the movie'
]
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

@client.command()
async def remove(ctx, *, topic):
    global queue
    topic = topic.lower()
    queue.remove_topic(topic)
    await ctx.send(embed=info_msg(f"Removed {topic} from queue."))

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
    await ctx.send(embed=help_command(opt, ctx.prefix, ABOUT_ME))

# General error handling for all commands.
@client.event
async def on_command_error(ctx, err):
    if isinstance(err, commands.CommandNotFound):
        await ctx.send(embed=bot_error("Not a command!"))

    elif isinstance(err, commands.errors.MissingRequiredArgument):
        await ctx.send(embed=bot_error(str(err)))

    elif isinstance(err, LengthError):
        await ctx.send(embed=cmd_error("Please keep topics under 50 characters."))

    elif isinstance(err, FullQueue):
        await ctx.send(embed=cmd_error("There are more than 30 topics in queue, please request a topic after one has been used."))

    elif isinstance(err, InQueue):
        await ctx.send(embed=info_msg("Topic is already in queue."))

    elif isinstance(err, EmptyQueue):
        await ctx.send(embed=cmd_error("There are not any topics in the queue, please add some topics."))

    elif isinstance(err, OutQueue):
        await ctx.send(embed=cmd_error(f"Topic does not exist in the queue."))

    elif isinstance(err, commands.errors.CheckFailure):
        await ctx.seend(embed=cmd_error("Commands are currently locked."))

    elif isinstance(err, commands.errors.NotOwner):
        await ctx.seend(embed=cmd_error("You are not allowed to use this command."))

    else:
        print(err)
        err_channel = client.get_channel(DUMP_CHANNEL)
        if err_channel:
            await err_channel.send(f"```Error: {err}\nMessage: {ctx.message.content}\nAuthor: {ctx.author}\nServer: {ctx.message.guild}\nLink: {ctx.message.jump_url}\nTraceback: {''.join(tb.format_exception(None, err, err.__traceback__))}```")

if __name__ == '__main__':
    client.run(TOKEN, log_handler=handler)
