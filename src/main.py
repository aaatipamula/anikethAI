import logging
import os
import sys
from os.path import dirname, join

import discord
from discord.ext import commands
from dotenv import load_dotenv

from admin import AdminCog
from database import BaseModel, engine
from ext import (
    bot_error,
    cmd_error,
)
from topicQueue import QueueError, TopicQueue
from users import UserCog
from util import normalize_tz

load_dotenv()


# ENV variable loader
def _get_env(key: str) -> str:
    val = os.environ.get(key)
    if not val:
        raise ValueError(f"Required ENV variable {key} missing!")
    return val


TOKEN = _get_env("TOKEN")
ABOUT_ME = _get_env("ABOUT_ME")
COMMAND_PREFIX = _get_env("COMMAND_PREFIX")
TIMEZONE = _get_env("TIMEZONE")
START_HOUR = int(os.environ.get("START_HOUR", "10"))
DUMP_CHANNEL = int(_get_env("DUMP_CHANNEL"))
COUNTING_CHANNEL = int(_get_env("COUNTING_CHANNEL"))
RSS_CHANNEL = int(_get_env("RSS_CHANNEL"))
RSS_FILE = join(dirname(__file__), "data", "rss.txt")

# Declaring gateway intents, discord.py >= 2.0 feature
intent = discord.Intents.default()
intent.message_content = True
intent.reactions = True
intent.members = True

# Set up logging
dt_fmt = "%Y-%m-%d %H:%M:%S"
formatter = logging.Formatter(
    "[{asctime}] [{levelname:<8}] {name}: {message}", dt_fmt, style="{"
)
handler = logging.StreamHandler(stream=sys.stdout)
handler.setFormatter(formatter)

bot_logger = logging.getLogger("discord.bot")
bot_logger.setLevel(logging.DEBUG)

if not bot_logger.hasHandlers():
    bot_logger.addHandler(handler)

# Create a global queue
GLOBAL_QUEUE = TopicQueue()

# Discord Bot instance
client = commands.Bot(
    command_prefix=COMMAND_PREFIX or ".",
    intents=intent,
    case_insensitive=True,  # case insensitive commands
    help_command=None,
)

# create our cogs
admin_cog = AdminCog(client, GLOBAL_QUEUE, DUMP_CHANNEL, RSS_FILE)
user_cog = UserCog(client, GLOBAL_QUEUE, ABOUT_ME, counting_channel_id=COUNTING_CHANNEL)

# Create the user db
BaseModel.metadata.create_all(engine)


@client.event
async def on_ready():
    if "AdminCog" not in client.cogs:
        await client.add_cog(admin_cog)
    if "UserCog" not in client.cogs:
        await client.add_cog(user_cog)

    times = normalize_tz(TIMEZONE, START_HOUR)
    admin_cog.update_rss_channel.change_interval(time=times)
    admin_cog.update_rss_channel.start()
    bot_logger.info("Started RSS task.")

    admin_cog.set_status.start()
    bot_logger.info("Started status task.")

    bot_logger.info("AnikethAI is ready...")


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
        await ctx.send(
            embed=cmd_error(
                "You likely used an argument wrong, refer to the documentation for this command."
            )
        )

    else:
        print(err)
        err_channel = client.get_channel(DUMP_CHANNEL)
        if err_channel and isinstance(err_channel, discord.TextChannel):
            # Known type checking error
            await err_channel.send(
                f"```Error: {err}\n\
                Message: {ctx.message.content}\n\
                Author: {ctx.author}\n\
                Server: {ctx.message.guild}\n\
                Link: {ctx.message.jump_url}```"
            )


if __name__ == "__main__":
    client.run(TOKEN, log_handler=handler, log_formatter=formatter)
