from typing import Tuple, Optional, Union
from random import choice as randChoice
from asyncio import sleep as asyncSleep

from discord.ext import commands
from discord import Message, Reaction, TextChannel, User, Member
from openai.error import RateLimitError

from consts import NO_TOKENS, RANDOM_REPLYS
from topicQueue import TopicQueue
from chain import create_aniketh_ai
from util import random_messages, convert_to_int
from database import (
    get_user_mem,
    dump_user_mem,
    get_board_message_id,
    add_starred_message,
    remove_starred_message,
)
from ext import (
    info_msg,
    cmd_error, 
    star_message, 
    topic_msg, 
    help_command,
    counting_err,
)


# Convert Flag arguments for the remove command
class RemoveFlags(commands.FlagConverter):
    span: Optional[Tuple[int, int]] = None
    topic: Optional[str] = None


class UserCog(commands.Cog):
    def __init__(
        self,
        bot: commands.Bot,
        topic_queue: TopicQueue,
        about_me: str,
        *,
        starboard_channel_id: Optional[int] = None,
        counting_channel_id: Optional[int] = None,
    ) -> None:
        self.bot = bot
        self.topic_queue = topic_queue
        self.about_me = about_me
        self.star_threshold = 3
        self.starboard_id = starboard_channel_id
        self.counting_channel_id = counting_channel_id

        self.counting_current_number = 1
        self.counting_last_author: Optional[Union[User, Member]] = None
        self.counting_high_score = 1

    @property
    def starboard(self):
        c = self.bot.get_channel(self.starboard_id or 0)
        assert isinstance(c, TextChannel) or c is None
        return c

    @property
    def counting(self):
        c = self.bot.get_channel(self.counting_channel_id or 0)
        assert isinstance(c, TextChannel) or c is None
        return c

    @commands.command()
    async def request(self, ctx, *, topic):
        global queue

        topic = topic.lower()
        self.topic_queue.add_topic(topic)

        await ctx.send(embed=info_msg(f"Added {topic} to queue."))

    @commands.command(name="rm")
    async def remove(self, ctx, topics: commands.Greedy[int], *, flags: RemoveFlags):
        global queue

        embeds = []

        _topics = self.topic_queue.remove_range(*flags.span) if flags.span else []
        _topics += (
            [self.topic_queue.remove_topic_name(flags.topic)] if flags.topic else []
        )
        _t, _errors = self.topic_queue.remove_topics(topics)
        _topics += _t

        if _errors:
            error_str = "\n".join(_errors)
            embeds.append(cmd_error((f"The Following Errors Occured:\n\n{error_str}")))

        if _topics:
            topic_str = "\n".join(_topics)
            embeds.append(info_msg(f"Removed the Following:\n\n{topic_str}"))
        else:
            raise commands.errors.UserInputError(
                "No arguments were parsed, please refer to the help manual."
            )

        await ctx.send(embeds=embeds)

    @commands.command(name="topics")
    async def list_topics(self, ctx):
        global queue
        await ctx.send(embed=topic_msg(self.topic_queue.topics))

    # Redefined help command.
    @commands.command()
    async def help(self, ctx, opt="general"):
        is_owner = await self.bot.is_owner(ctx.author)
        userHelp, adminHelp = help_command(
            opt, ctx.prefix, self.about_me, is_owner=is_owner
        )
        await ctx.send(embed=userHelp)
        if adminHelp is not None:
            await ctx.send(embed=adminHelp, ephemeral=True)

    @commands.Cog.listener()
    async def on_message(self, message: Message):
        # ignore if self
        if message.author == self.bot.user:
            return

        # Counting channel
        if message.channel == self.counting:
            number = convert_to_int(message.content)
            print("COUNTING NUMBER: ", number)

            if number is None:
                pass
            elif number == self.counting_current_number and message.author != self.counting_last_author:
                await message.add_reaction("✅")
                self.counting_current_number += 1
                self.counting_last_author = message.author
                if self.counting_current_number > self.counting_high_score:
                    self.counting_high_score = self.counting_current_number
            elif number == self.counting_current_number:
                # Right number but same author
                await message.add_reaction("❌")
                err_embed = counting_err(
                    "No double posting!",
                    self.counting_current_number, 
                    self.counting_high_score - 1
                )
                await message.channel.send(embed=err_embed)
                self.counting_current_number = 1
                self.counting_last_author = None
            else:
                # Wrong number
                await message.add_reaction("❌")
                err_embed = counting_err(
                    "Invalid count!",
                    self.counting_current_number, 
                    self.counting_high_score - 1
                )
                await message.channel.send(embed=err_embed)
                self.counting_current_number = 1
                self.counting_last_author = None

        if self.bot.user.mentioned_in(message):  # known type checking error
            async with message.channel.typing():
                mem = get_user_mem(
                    message.channel.id
                )  # Use channel ids to gather messages
                chain = create_aniketh_ai(mem)
                try:
                    msg = chain.predict(user_message=message.clean_content)
                except RateLimitError:
                    msg = randChoice(NO_TOKENS)
                dump_user_mem(message.channel.id, mem)
            await message.channel.send(msg)

        for reply_message in random_messages(RANDOM_REPLYS, message.content):
            await message.reply(reply_message, mention_author=False)
            await asyncSleep(0.5)

    @commands.Cog.listener()
    async def on_reaction_add(self, reaction: Reaction, _: Union[Member, User]):
        if str(reaction.emoji) == "⭐":
            if self.starboard is None:
                return
            elif self.starboard == reaction.message.channel:
                return

            if reaction.count == self.star_threshold:
                star_embed = star_message(reaction.message, reaction.count)
                board_message = await self.starboard.send(embed=star_embed)
                add_starred_message(reaction.message.id, board_message.id)
            elif reaction.count > self.star_threshold:
                star_embed = star_message(reaction.message, reaction.count)
                board_id = get_board_message_id(reaction.message.id)
                message = await self.starboard.fetch_message(board_id)
                await message.edit(embed=star_embed)

    @commands.Cog.listener()
    async def on_reaction_remove(self, reaction: Reaction, _: Union[Member, User]):
        if str(reaction.emoji) == "⭐":
            if self.starboard is None:
                return
            elif self.starboard == reaction.message.channel:
                return

            if reaction.count < self.star_threshold:
                board_id = get_board_message_id(reaction.message.id)
                remove_starred_message(reaction.message.id)
                message = await self.starboard.fetch_message(board_id)
                await message.delete()
            else:
                star_embed = star_message(reaction.message, reaction.count)
                board_id = get_board_message_id(reaction.message.id)
                message = await self.starboard.fetch_message(board_id)
                await message.edit(embed=star_embed)
