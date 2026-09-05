from __future__ import annotations

from datetime import datetime, timezone
from io import BytesIO
from typing import Optional

import discord
from redbot.core import Config, commands
from redbot.core.bot import Red

from .dashboard import ContactDashboard


class Contact(ContactDashboard, commands.Cog):
    """A small DM-based support inbox for staff."""

    def __init__(self, bot: Red):
        self.bot = bot
        self.config = Config.get_conf(self, identifier=9182736450)
        self.config.register_guild(staff_channel=None)
        self.config.register_global(tickets={})

    @staticmethod
    def _timestamp() -> str:
        return datetime.now(timezone.utc).isoformat(timespec="seconds")

    async def _configured_guild(self) -> Optional[discord.Guild]:
        for guild in self.bot.guilds:
            if await self.config.guild(guild).staff_channel():
                return guild
        return None

    async def _create_thread(self, guild: discord.Guild, user: discord.abc.User) -> Optional[discord.Thread]:
        channel_id = await self.config.guild(guild).staff_channel()
        channel = guild.get_channel(channel_id) if channel_id else None
        if not isinstance(channel, discord.TextChannel):
            return None

        return await channel.create_thread(
            name=f"contact-{user.name}"[:100],
            type=discord.ChannelType.public_thread,
            auto_archive_duration=1440,
            reason="New DM support conversation",
        )

    async def _send_staff_message(self, guild: discord.Guild, ticket: dict, message: discord.Message):
        thread_id = ticket.get("thread_id")
        thread = guild.get_thread(thread_id) if isinstance(thread_id, int) else None
        if thread is None:
            thread = await self._create_thread(guild, message.author)
            if thread is None:
                return
            async with self.config.tickets() as tickets:
                tickets[str(message.author.id)]["thread_id"] = thread.id

        embed = discord.Embed(
            title="New support message",
            description=message.content or "(attachment only)",
            color=discord.Color.blurple(),
            timestamp=message.created_at,
        )
        embed.set_author(name=str(message.author), icon_url=message.author.display_avatar.url)
        embed.add_field(name="User ID", value=str(message.author.id), inline=True)
        if message.attachments:
            embed.add_field(
                name="Attachments",
                value="\n".join(attachment.url for attachment in message.attachments),
                inline=False,
            )
        await thread.send(embed=embed)

    async def _append_message(self, user_id: int, author: str, content: str, direction: str):
        async with self.config.tickets() as tickets:
            ticket = tickets.setdefault(str(user_id), {"status": "open", "messages": []})
            ticket["status"] = "open"
            ticket["messages"].append(
                {
                    "author": author,
                    "content": content,
                    "direction": direction,
                    "timestamp": self._timestamp(),
                }
            )
            return dict(ticket)

    @commands.command()
    @commands.guild_only()
    @commands.has_permissions(manage_guild=True)
    async def contactsetup(self, ctx: commands.Context, channel: discord.TextChannel):
        """Set the channel where support DMs are delivered."""
        await self.config.guild(ctx.guild).staff_channel.set(channel.id)
        await ctx.send(f"Support messages will be delivered to {channel.mention}.")

    @commands.command()
    @commands.guild_only()
    @commands.has_permissions(manage_guild=True)
    async def contactdashboard(self, ctx: commands.Context):
        """Show the support dashboard and open conversation count."""
        await ctx.send(embed=await self.dashboard_embed(ctx.guild))

    @commands.command(name="support")
    @commands.guild_only()
    @commands.has_permissions(manage_messages=True)
    async def support(
        self,
        ctx: commands.Context,
        action: str,
        user: Optional[discord.User] = None,
        *,
        message: str = "Hello, how can we help you?",
    ):
        """Open, reply to, close, or list support conversations."""
        action = action.lower()
        if action == "list":
            await self._support_list(ctx)
        elif action == "open" and user is not None:
            await self._support_open(ctx, user, message)
        elif action == "reply" and user is not None:
            await self._support_reply(ctx, user, message)
        elif action == "close" and user is not None:
            await self._support_close(ctx, user)
        else:
            await ctx.send_help(ctx.command)

    async def _support_reply(self, ctx: commands.Context, user: discord.User, message: str):
        """Reply to a user through their DM."""
        tickets = await self.config.tickets()
        ticket = tickets.get(str(user.id))
        if ticket is None:
            await ctx.send("No conversation exists for that user.")
            return

        try:
            await user.send(message)
        except discord.Forbidden:
            await ctx.send("I could not DM that user.")
            return

        await self._append_message(user.id, str(ctx.author), message, "staff")
        await ctx.send("Reply sent.", delete_after=5)

    async def _support_open(self, ctx: commands.Context, user: discord.User, message: str):
        """Open a staff thread and start a two-way DM with a user."""
        tickets = await self.config.tickets()
        ticket = tickets.get(str(user.id))
        if ticket and ticket.get("thread_id"):
            thread = ctx.guild.get_thread(ticket["thread_id"])
            if thread:
                await ctx.send(f"Conversation already open: {thread.mention}")
                return

        thread = await self._create_thread(ctx.guild, user)
        if thread is None:
            await ctx.send("The configured support channel is missing or is not a text channel.")
            return
        async with self.config.tickets() as all_tickets:
            all_tickets[str(user.id)] = {
                "status": "open",
                "thread_id": thread.id,
                "messages": [],
            }

        try:
            await user.send(message)
        except discord.Forbidden:
            await ctx.send("The thread was opened, but I could not DM that user.")
            return

        await self._append_message(user.id, str(ctx.author), message, "staff")
        await thread.send(f"Staff DM sent by **{ctx.author}**:\n{message}")
        await ctx.send(f"Conversation opened: {thread.mention}")

    async def _support_close(self, ctx: commands.Context, user: discord.User):
        """Close a support conversation and send its transcript."""
        async with self.config.tickets() as tickets:
            ticket = tickets.get(str(user.id))
            if ticket is None:
                await ctx.send("No conversation exists for that user.")
                return
            ticket["status"] = "closed"
            transcript = "\n".join(
                f"[{entry['timestamp']}] {entry['author']}: {entry['content']}"
                for entry in ticket["messages"]
            )

        await ctx.send(
            f"Conversation with {user.mention} closed.",
            file=discord.File(
                BytesIO(transcript.encode("utf-8")),
                filename=f"conversation-{user.id}.txt",
            ),
        )
        try:
            await user.send("This conversation has ended. Please contact staff again if you need further assistance.")
        except discord.Forbidden:
            pass

    async def _support_list(self, ctx: commands.Context):
        """List open support conversations."""
        tickets = await self.config.tickets()
        open_tickets = [user_id for user_id, ticket in tickets.items() if ticket.get("status") == "open"]
        await ctx.send("Open conversations: " + (", ".join(open_tickets) if open_tickets else "none"))

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if message.author.bot:
            return

        if message.guild is None:
            guild = await self._configured_guild()
            if guild is None:
                return

            ticket = await self._append_message(message.author.id, str(message.author), message.content, "user")
            await self._send_staff_message(guild, ticket, message)
            return

        tickets = await self.config.tickets()
        ticket = next(
            (candidate for candidate in tickets.values() if candidate.get("thread_id") == message.channel.id),
            None,
        )
        if ticket is None or not isinstance(message.channel, discord.Thread):
            return

        context = await self.bot.get_context(message)
        if context.valid:
            return

        user_id = next(
            (user_id for user_id, value in tickets.items() if value.get("thread_id") == message.channel.id),
            None,
        )
        if user_id is None:
            return

        content = message.content or "(attachment only)"
        if message.attachments:
            content += "\n" + "\n".join(attachment.url for attachment in message.attachments)

        try:
            user = await self.bot.fetch_user(int(user_id))
            await user.send(content)
        except (discord.Forbidden, discord.HTTPException, StopAsyncIteration):
            await message.channel.send("I could not deliver that reply to the user.")
            return

        await self._append_message(int(user_id), str(message.author), content, "staff")