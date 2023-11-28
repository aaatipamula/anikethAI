from typing import Tuple, Optional, Union
from asyncio import sleep as asyncsleep
import random

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

boomin_tags = [
    "This beat is so, Metro",
    "Metro boomin want some more n*gga",
    "If Young Metro don't trust you I'm gon' shoot you",
    "Young Metro, young metro, young metro",
    "Metro!",
    "Metro in this bitch goin' crazy"
]

khalidisms = [
    "Anotha' One",
    "We da best music",
    "Tell em to bring out the whole ocean",
    "Bumbaclat",
    "And perhaps what is is?",
    "Sunday morning, sunday brunch",
    "I call her chandelier",
    "Life...is Roblox",
    "Tell em' to bring out the lobster",
    "Roses are red, violets are blue"
    "Tell em' to bring the yacht out",
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

    @staticmethod
    async def randomsg(channel: discord.TextChannel, count=5):
        async with channel.typing():
            while count > 0:
                time = random.randint(1, 10)
                await asyncsleep(time)
                rand_msg = random.choice(khalidisms)
                await channel.send(rand_msg)
                count -= 1
    
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
        embeds = help_command(opt, ctx.prefix, self.about_me, is_owner=is_owner)
        await ctx.send(embeds=embeds)

    @commands.Cog.listener()
    async def on_message(self, message: Message):
        # ignore if self
        if message.author == self.bot.user:
            return

        owner = await self.bot.is_owner(message.author)

        if self.bot.user.mentioned_in(message): # known type error
            async with message.channel.typing():
                mem = get_user_mem(message.author.id)
                chain = create_aniketh_ai(mem)
                msg = chain.predict(user_message=message.clean_content)
                dump_user_mem(message.author.id, mem)
            await message.channel.send(msg)

        if owner and "khaled" in message.content.lower():
            await self.randomsg(message.channel)

        if "metro" in message.content.lower():
            tag = random.choice(boomin_tags)
            await message.reply(tag, mention_author=False)

        if "balls" in message.content:
            async with message.channel.typing():
                await asyncsleep(1)
                await message.reply("balls mentioned 🔥🔥🔥", mention_author=False)

        if "merica" in message.content or "freedom" in message.content:
            await message.reply("🦅🦅:flag_us::flag_us:💥💥'MERICA RAHHHH💥💥:flag_us::flag_us:🦅🦅", mention_author=False)

    @commands.Cog.listener()
    async def on_reaction_add(self, reaction: Reaction, user: Union[Member, User]):
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
    async def on_reaction_remove(self, reaction: Reaction, user: Union[Member, User]):
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

