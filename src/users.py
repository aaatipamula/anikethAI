from asyncio import sleep as asyncSleep
from random import choice as randChoice
from typing import Optional, Tuple, Union

from discord import Message, Reaction, TextChannel, User, Member
from discord.ext import commands
from openai.error import RateLimitError

from chain import create_aniketh_ai
from consts import NO_TOKENS, RANDOM_REPLYS
from gambling import (
    deal_cards,
    gambling_embed,
    gambling_error,
    get_multiplier,
    parse_raw_guess,
)
from topicQueue import TopicQueue
from util import convert_to_int, random_messages
from database import (
    get_user_mem,
    dump_user_mem,
    get_board_message_id,
    add_starred_message,
    get_user_moner,
    remove_starred_message,
    update_user_moner,
    reload_user_account,
    get_user_bank_info,
)
from ext.embeds import (
    info_msg,
    cmd_error,
    star_message,
    topic_msg,
    help_command,
    counting_err,
    bank_embed,
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

    @commands.command()
    async def gamble(
        self,
        ctx: commands.Context,
        amount: Optional[int] = None,
        *args,
    ):
        # Ignore if a subcommand was invoked
        if ctx.invoked_subcommand:
            return

        author_id = ctx.author.id
        rank, suit, all_in = parse_raw_guess(list(args))

        # Both rank and suit cannot be empty
        if rank is None and suit is None:
            err_msg = gambling_error("You must specify a rank, suit, or card")
            await ctx.channel.send(embed=err_msg)
            return

        total_moners = get_user_moner(author_id)
        gambled_amount = total_moners if all_in else amount or 50

        # Deduct moners if possible
        if gambled_amount > total_moners:
            err_msg = gambling_error("You can't gamble more than you have!")
            await ctx.channel.send(embed=err_msg)
            return

        total_moners = total_moners - gambled_amount

        # Gamble
        cards = deal_cards(4)
        multiplier = get_multiplier(cards, rank, suit)

        # Calculations
        is_winner = multiplier > 0
        profit = multiplier * gambled_amount
        total_moners += profit
        update_user_moner(author_id, total_moners)

        embed = gambling_embed(
            cards,
            rank,
            suit,
            is_winner,
            profit if is_winner else gambled_amount,
            total_moners,
        )

        await ctx.channel.send(embed=embed)

    @commands.group(pass_context=True)
    async def bank(self, ctx: commands.Context):
        if not ctx.invoked_subcommand:
            reload_time, total_moners = get_user_bank_info(ctx.author.id)
            embed = bank_embed(total_moners, reload_time)
            await ctx.send(embed=embed)

    @bank.command(name="reload")
    async def reload_bank(self, ctx: commands.Context):
        reload_amount = reload_user_account(ctx.author.id)

        if reload_amount > 0:
            announcement_str = f"# Added ${reload_amount:,d} to account!\n"
        else:
            announcement_str = "# You are still ineligible to reload your account!\n"

        reload_time, total_moners = get_user_bank_info(ctx.author.id)
        embed = bank_embed(total_moners, reload_time)
        await ctx.send(announcement_str, embed=embed)

    @commands.Cog.listener()
    async def on_message(self, message: Message):
        # ignore if self
        if message.author == self.bot.user:
            return

        # Counting channel
        if message.channel == self.counting:
            number = convert_to_int(message.content)

            if number is None:
                pass
            elif (
                number == self.counting_current_number
                and message.author != self.counting_last_author
            ):
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
                    self.counting_high_score - 1,
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
                    self.counting_high_score - 1,
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
