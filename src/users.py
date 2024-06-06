from typing import Tuple, Optional, Union
from random import choice, randint

from discord.ext import commands
from discord import Message, Reaction, User, Member

from topicQueue import TopicQueue
from chain import create_aniketh_ai
from database import (
    get_user_mem,
    dump_user_mem,
    get_board_message_id,
    add_starred_message,
    remove_starred_message
)
from ext import info_msg, cmd_error, star_message, topic_msg, help_command

khaledisms = [
    "We da best music :fire:",
    "God did.",
    "Tell 'em to bring out the whole ocean!",
    "DEEEJAAAYYY KKKKHHHAAALLLLLLLEEEEEED",
    "They ain't believe in us."
 ]

# Convert Flag arguments for the remove command
class RemoveFlags(commands.FlagConverter):
    span: Tuple[int, int] = None # Known type checking error
    topic: Optional[str]

class UserCog(commands.Cog):
    def __init__(
        self,
        bot: commands.Bot,
        topic_queue: TopicQueue,
        about_me: str,
        starboard_id: Optional[int]
    ) -> None:
        self.bot = bot
        self.topic_queue = topic_queue
        self.about_me = about_me
        self.star_threshold = 3
        self.starboard_id = starboard_id

    @property
    def starboard(self):
        return self.bot.get_channel(self.starboard_id) if self.starboard_id else None

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
        _topics += [self.topic_queue.remove_topic_name(flags.topic)] if flags.topic else []
        _t, _errors = self.topic_queue.remove_topics(topics)
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

    @commands.command(name="topics")
    async def list_topics(self, ctx):
        global queue
        await ctx.send(embed=topic_msg(self.topic_queue.topics))

    # Redefined help command.
    @commands.command()
    async def help(self, ctx, opt="general"):
        is_owner = await self.bot.is_owner(ctx.author)
        userHelp, adminHelp = help_command(opt, ctx.prefix, self.about_me, is_owner=is_owner)
        await ctx.send(embed=userHelp)
        if adminHelp:
            await ctx.send(embed=adminHelp, ephemeral=True)

    @commands.Cog.listener()
    async def on_message(self, message: Message):
        # ignore if self
        if message.author == self.bot.user:
            return

        if self.bot.user.mentioned_in(message): # known type checking error
            async with message.channel.typing():
                mem = get_user_mem(message.author.id)
                chain = create_aniketh_ai(mem)
                msg = chain.predict(user_message=message.clean_content)
                dump_user_mem(message.author.id, mem)
            await message.channel.send(msg)

        if "balls" in message.content:
            await message.reply("balls mentioned 🔥🔥🔥", mention_author=False)

        if "merica" in message.content or "freedom" in message.content:
            await message.reply("🦅🦅:flag_us::flag_us:💥💥'MERICA RAHHHH💥💥:flag_us::flag_us:🦅🦅", mention_author=False)

        if "believe" in message.content and randint(1, 6) == 1:
            await message.reply(choice(khaledisms))

    @commands.Cog.listener()
    async def on_reaction_add(self, reaction: Reaction, _: Union[Member, User]):
        if str(reaction.emoji) == '⭐':
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
        if str(reaction.emoji) == '⭐':
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

