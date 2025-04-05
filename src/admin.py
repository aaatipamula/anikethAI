import datetime as dt
from time import gmtime, struct_time
from asyncio import TimeoutError#, sleep as async_sleep
from typing import List, Tuple

from discord.utils import TimestampStyle
import feedparser
from discord import Game, TextChannel, Embed
from discord.ext import commands, tasks
from langchain.memory import ConversationBufferWindowMemory

from topicQueue import TopicQueue
from chain import create_aniketh_ai
from ext import admin_dashboard, cmd_error, info_msg, loop_status, rss_embed
from users import UserCog

UPDATE_WAIT = 18

# Defaults to 12 hours ago
class TimeFlags(commands.FlagConverter):
    days: int = 0
    hours: int = 12
    minutes: int = 0

class AdminCog(commands.Cog):
    def __init__(
        self, 
        bot: commands.Bot, 
        topic_queue: TopicQueue,
        log_channel_id: int,
        # NOTE: Make the following environment variables
        confirmation_emote_id: int = 1136812895859134555, #:L_: emoji
        rss_feeds: List[str] | None = None
    ) -> None:
        self.bot = bot
        self.topic_queue = topic_queue
        self.log_channel_id = log_channel_id
        self.confim_emote_id = confirmation_emote_id

        # TODO: Persist RSS feeds to database/file
        self.rss_feeds = rss_feeds or ["https://www.autosport.com/rss/f1/news/"]
        self.rss_channel_id = log_channel_id # Default the RSS channel for now
        self.rss_last_updated = dt.datetime.now(tz=dt.timezone.utc)

        # Set state
        self.start_datetime = dt.datetime.now()
        self.locked = False

    @property
    def log_channel(self):
        c = self.bot.get_channel(self.log_channel_id)
        assert isinstance(c, TextChannel) # Channel must be a text channel
        return c

    @property
    def rss_channel(self):
        c = self.bot.get_channel(self.log_channel_id)
        assert isinstance(c, TextChannel) # Channel must be a text channel
        return c

    @property
    def confim_emote(self):
        e = self.bot.get_emoji(self.confim_emote_id)
        assert e is not None
        return e

    def get_rss_updates(self, time_flags: TimeFlags | None = None) -> Tuple[List[Embed], List[str]]:
        posts = []
        invalid_urls = []

        # Some time ago...
        if time_flags:
            self.rss_last_updated -= dt.timedelta(
                days=time_flags.days,
                hours=time_flags.hours,
                minutes=time_flags.minutes
            )

        for url in self.rss_feeds:
            source = feedparser.parse(url)
            if (source.bozo):
                invalid_urls.append(url)
                continue

            # NOTE: feedparser library is horribly typed
            for entry in source.entries:
                published_dt = dt.datetime(*entry['published_parsed'][:6], tzinfo=dt.timezone.utc)
                if published_dt >= self.rss_last_updated:
                    post = rss_embed(entry, published_dt)
                    posts.insert(0, post)
                else:
                    break # We can ignore the rest of the posts

        self.rss_last_updated = dt.datetime.now(tz=dt.timezone.utc)
        return posts, invalid_urls

    @tasks.loop(hours=UPDATE_WAIT)
    async def set_status(self):
        chain = create_aniketh_ai(ConversationBufferWindowMemory(return_messages=True))
        topic = self.topic_queue.pick_topic()
        message = chain.predict(user_message=f"Write a short (5-6 word) sentence on {topic}")
        game = Game(message)
        await self.bot.change_presence(activity=game)

    # NOTE: Possibly update every 6 hours
    @tasks.loop()
    async def update_rss_channel(self):
        try:
            posts, errs = self.get_rss_updates()
        except AttributeError as err:
            await self.log_channel.send(embed=cmd_error(f"There was an error grabbing some post information:\n\n{err}"))
            return

        if errs:
            f_errs = ", ".join(errs)
            await self.log_channel.send(embed=cmd_error(f"The following are invalid URLS:\n\n{f_errs}"))

        start = 0
        while start < len(posts):
            stop = start + 5 if start + 5 < len(posts) else len(posts)
            await self.rss_channel.send(embeds=posts[start:stop])
            start = stop

    @commands.group(pass_context=True)
    async def admin(self, ctx: commands.Context):
        if not ctx.invoked_subcommand:
            embed = await admin_dashboard(self.bot, self.start_datetime)
            await ctx.send(embed=embed)

    @admin.command(name="getrss")
    async def get_rss_from(self, _: commands.Context, time_flags: TimeFlags):
        try:
            posts, errs = self.get_rss_updates(time_flags)
        except AttributeError as err:
            await self.log_channel.send(embed=cmd_error(f"There was an error grabbing some post information:\n\n{err}"))
            return

        if errs:
            f_errs = ", ".join(errs)
            await self.log_channel.send(embed=cmd_error(f"The following are invalid URLS:\n\n{f_errs}"))

        start = 0
        while start < len(posts):
            stop = start + 5 if start + 5 < len(posts) else len(posts)
            await self.rss_channel.send(embeds=posts[start:stop])
            start = stop

    @admin.command(name="setrss")
    async def set_rss_channel(self, ctx: commands.Context, chan: TextChannel):
        self.rss_channel_id = chan.id
        await ctx.send(embed=info_msg(f"Set RSS channel to #{chan}"))

    @admin.command(name="addfeed")
    async def add_rss_feed(self, ctx: commands.Context, url: str):
        self.rss_feeds.append(url)
        await ctx.send(embed=info_msg(f"Added URL: `{url}`"))

    @admin.command(name="stopl")
    async def stop_loop(self, ctx: commands.Context):
        if self.set_status.is_running():
            self.set_status.cancel()
        else:
            await ctx.send(embed=cmd_error("Task is already stopped."))
            return
        await ctx.send(embed=info_msg("Stopped updating status"))

    @admin.command(name="startl")
    async def start_loop(self, ctx: commands.Context):
        if self.set_status.is_running():
            await ctx.send(embed=cmd_error("Task is already running."))
            return
        else:
            self.set_status.start()
        await ctx.send(embed=info_msg("Started updating status."))

    @admin.command(name="statusl")
    async def status_loop(self, ctx: commands.Context):
        status_embed = loop_status(
            "Status Updates",
            self.set_status.is_running(), 
            self.set_status.next_iteration
        )
        rss_embed = loop_status(
            "RSS Update Feed",
            self.update_rss_channel.is_running(), 
            self.update_rss_channel.next_iteration
        )
        await ctx.send(embeds=[status_embed, rss_embed])

    @admin.command(name="kill")
    async def kill_bot(self, ctx: commands.Context):
        await ctx.send(f"NOOOOO PLEASE {self.bot.get_emoji(1145147159260450907)}") # :cri: emoji

        def check(reaction, user):
            return self.bot.is_owner(user) and reaction.emoji == self.confim_emote

        try:
            await self.bot.wait_for("reaction_add", timeout=10.0, check=check)
        except TimeoutError:
            await ctx.send(str(self.bot.get_emoji(994378239675990029)))
        else:
            await ctx.send(str(self.bot.get_emoji(1145090024333918320)))
            exit(0)

    @admin.command()
    async def lock(self, ctx: commands.Context):
        if self.locked:
            await ctx.send(embed=cmd_error("Commands already locked."))
        else:
            self.locked = True
            await ctx.send(embed=info_msg("Commands now locked."))

    @admin.command()
    async def unlock(self, ctx: commands.Context):
        if not self.locked:
            await ctx.send(embed=cmd_error("Commands already unlocked."))
        else:
            self.locked = False
            await ctx.send(embed=info_msg("Commands now unlocked."))

    @admin.command()
    async def starboard(self, ctx: commands.Context, channel: TextChannel):
        user_cog = self.bot.get_cog('UserCog')
        assert isinstance(user_cog, UserCog)
        user_cog.starboard_id = channel.id
        await ctx.send(embed=info_msg(f"Set starboard to {channel}"))

    @admin.command()
    async def minstars(self, ctx: commands.Context, minstars: int):
        user_cog = self.bot.get_cog('UserCog')
        assert isinstance(user_cog, UserCog)
        user_cog.star_threshold = minstars
        await ctx.send(embed=info_msg(f"Set minimum stars to {minstars}"))

    # check if commands are locked
    async def bot_check(self, ctx: commands.Context):
        if await self.bot.is_owner(ctx.author):
            return True
        return not self.locked

    # checks if the author is the owner
    async def cog_check(self, ctx):
        return await self.bot.is_owner(ctx.author)

