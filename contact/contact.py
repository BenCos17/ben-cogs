from __future__ import annotations

import asyncio
from datetime import datetime, timezone
from io import BytesIO
from typing import Optional

import discord
from redbot.core import Config, commands
from redbot.core.bot import Red

from .dashboard import ContactDashboard


class Contact(commands.Cog, ContactDashboard):
    """A small DM-based support inbox for staff."""

    def __init__(self, bot: Red):
        self.bot = bot
        self._ticket_id_lock = asyncio.Lock()
        self.config = Config.get_conf(self, identifier=9182736450)
        self.config.register_guild(
            staff_channel=None, tickets={}, next_ticket_id=1, pending_ticket_choices={}
        )

    @staticmethod
    def _timestamp() -> str:
        return datetime.now(timezone.utc).isoformat(timespec="seconds")

    @staticmethod
    def _conversation_embed(title: str, content: str, color: discord.Color) -> discord.Embed:
        return discord.Embed(title=title, description=content or "(attachment only)", color=color)

    async def _configured_guild(self) -> Optional[discord.Guild]:
        for guild in self.bot.guilds:
            if await self.config.guild(guild).staff_channel():
                return guild
        return None

    async def _migrate_tickets(self, guild: discord.Guild) -> dict:
        """Convert the original user-keyed storage to ticket-keyed storage."""
        async with self.config.guild(guild).tickets() as tickets:
            next_id = await self.config.guild(guild).next_ticket_id()
            changed = False
            for key, ticket in list(tickets.items()):
                if "ticket_id" in ticket:
                    continue
                ticket_id = f"{guild.id}-{next_id:04d}"
                next_id += 1
                ticket["ticket_id"] = ticket_id
                ticket["user_id"] = int(key) if str(key).isdigit() else ticket.get("user_id")
                tickets[ticket_id] = ticket
                del tickets[key]
                changed = True
        if changed:
            await self.config.guild(guild).next_ticket_id.set(next_id)
        return await self.config.guild(guild).tickets()

    async def _new_ticket(self, guild: discord.Guild, user_id: int) -> dict:
        async with self._ticket_id_lock:
            next_id = await self.config.guild(guild).next_ticket_id()
            ticket_id = f"{guild.id}-{next_id:04d}"
            await self.config.guild(guild).next_ticket_id.set(next_id + 1)
        ticket = {"ticket_id": ticket_id, "user_id": user_id, "status": "open", "messages": []}
        async with self.config.guild(guild).tickets() as tickets:
            tickets[ticket_id] = ticket
        return ticket

    @staticmethod
    def _find_ticket(tickets: dict, ticket_id: str) -> Optional[dict]:
        ticket = tickets.get(ticket_id)
        return ticket if ticket and ticket.get("ticket_id") == ticket_id else None

    @staticmethod
    def _find_open_ticket(tickets: dict, user_id: int) -> tuple[Optional[str], Optional[dict]]:
        for ticket_id, ticket in reversed(list(tickets.items())):
            if ticket.get("user_id") == user_id and ticket.get("status") == "open":
                return ticket_id, ticket
        return None, None

    async def _ticket_guild(self, user_id: int) -> Optional[discord.Guild]:
        for guild in self.bot.guilds:
            tickets = await self._migrate_tickets(guild)
            if any(ticket.get("user_id") == user_id and ticket.get("status") == "open" for ticket in tickets.values()):
                return guild
        return None

    async def _find_user_ticket(self, user_id: int, ticket_id: str) -> tuple[Optional[discord.Guild], Optional[dict]]:
        for guild in self.bot.guilds:
            tickets = await self._migrate_tickets(guild)
            ticket = self._find_ticket(tickets, ticket_id)
            if ticket is not None and ticket.get("user_id") == user_id:
                return guild, ticket
        return None, None

    async def _create_thread(
        self, guild: discord.Guild, user: discord.abc.User, ticket_id: str
    ) -> Optional[discord.Thread]:
        channel_id = await self.config.guild(guild).staff_channel()
        channel = guild.get_channel(channel_id) if channel_id else None
        if not isinstance(channel, discord.TextChannel):
            return None

        return await channel.create_thread(
            name=f"ticket-{ticket_id}-{user.name}"[:100],
            type=discord.ChannelType.public_thread,
            auto_archive_duration=1440,
            reason="New DM support conversation",
        )

    async def _send_staff_message(self, guild: discord.Guild, ticket: dict, message: discord.Message):
        thread_id = ticket.get("thread_id")
        thread = guild.get_thread(thread_id) if isinstance(thread_id, int) else None
        if thread is None:
            thread = await self._create_thread(guild, message.author, ticket["ticket_id"])
            if thread is None:
                return
            async with self.config.guild(guild).tickets() as tickets:
                tickets[ticket["ticket_id"]]["thread_id"] = thread.id

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

    async def _append_message(
        self, guild: discord.Guild, ticket_id: str, author: str, content: str, direction: str
    ):
        async with self.config.guild(guild).tickets() as tickets:
            ticket = tickets.get(ticket_id)
            if ticket is None:
                return None
            ticket["messages"].append(
                {
                    "author": author,
                    "content": content,
                    "direction": direction,
                    "timestamp": self._timestamp(),
                }
            )
            return dict(ticket)

    async def _open_tickets_for_user(self, guild: discord.Guild, user_id: int) -> dict:
        tickets = await self._migrate_tickets(guild)
        return {
            ticket_id: ticket
            for ticket_id, ticket in tickets.items()
            if ticket.get("user_id") == user_id and ticket.get("status") == "open"
        }

    async def _ask_for_ticket(self, guild: discord.Guild, user: discord.abc.User, ticket_ids: list[str]):
        choices = ", ".join(ticket_ids)
        await user.send(
            embed=self._conversation_embed(
                "Which ticket should receive this message?",
                f"You have multiple open tickets: {choices}\nReply with one ticket ID.",
                discord.Color.orange(),
            )
        )

    async def _reply_to_ticket(self, guild: discord.Guild, ticket_id: str, author: str, message: str) -> bool:
        tickets = await self._migrate_tickets(guild)
        ticket = self._find_ticket(tickets, ticket_id)
        if ticket is None or ticket.get("status") != "open":
            return False
        user = await self.bot.fetch_user(int(ticket["user_id"]))
        await user.send(embed=self._conversation_embed("Message from staff", message, discord.Color.blurple()))
        await self._append_message(guild, ticket_id, author, message, "staff")
        thread_id = ticket.get("thread_id")
        thread = guild.get_thread(thread_id) if isinstance(thread_id, int) else None
        if thread is not None:
            thread_message = await thread.send(
                embed=self._conversation_embed(
                    f"Message from {author}", message, discord.Color.blurple()
                )
            )
            try:
                await thread_message.add_reaction("✅")
            except (discord.Forbidden, discord.HTTPException):
                pass
        return True

    async def _close_ticket(self, guild: discord.Guild, ticket_id: str) -> Optional[dict]:
        async with self.config.guild(guild).tickets() as tickets:
            ticket = tickets.get(ticket_id)
            if ticket is None:
                return None
            ticket["status"] = "closed"
            closed_ticket = dict(ticket)
        async with self.config.guild(guild).pending_ticket_choices() as choices:
            if choices.get(str(closed_ticket.get("user_id"))) == ticket_id:
                choices.pop(str(closed_ticket.get("user_id")), None)
        return closed_ticket

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
    async def contactpanel(self, ctx: commands.Context, channel: discord.TextChannel):
        """Post a user-facing support panel in a channel."""
        bot_user = self.bot.user
        if bot_user is None:
            await ctx.send("I cannot create the panel until the bot is ready.")
            return
        embed = discord.Embed(
            title="Contact Support",
            description=(
                "Need help? Click **Message Support** to start a private support ticket.\n\n"
                "You will receive a ticket ID. Keep it if you have more than one open ticket."
            ),
            color=discord.Color.blurple(),
        )
        embed.set_footer(text="You can close your ticket with contactclose <ticket-id>.")
        view = discord.ui.View()
        view.add_item(
            discord.ui.Button(
                label="Open a Support Ticket",
                style=discord.ButtonStyle.link,
                url=f"https://discord.com/users/{bot_user.id}",
            )
        )
        await channel.send(embed=embed, view=view)
        await ctx.send(f"Support panel posted in {channel.mention}.", delete_after=5)

    @commands.command()
    async def contactclose(self, ctx: commands.Context, ticket_id: str):
        """Let a ticket owner close their own ticket from Discord or DM."""
        guild, ticket = await self._find_user_ticket(ctx.author.id, ticket_id)
        if guild is None or ticket is None:
            await ctx.send("That ticket was not found, or it does not belong to you.")
            return
        if ticket.get("status") != "open":
            await ctx.send("That ticket is already closed.")
            return
        await self._close_ticket(guild, ticket_id)
        await ctx.send(f"Ticket {ticket_id} is now closed. You can start a new ticket any time.")

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
        target: Optional[str] = None,
        *,
        message: str = "Hello, how can we help you?",
    ):
        """Open, reply to, close, or list support conversations by user or ticket ID."""
        action = action.lower()
        if action == "list":
            await self._support_list(ctx)
        elif action == "open" and target is not None:
            try:
                user = await commands.UserConverter().convert(ctx, target)
            except commands.BadArgument:
                await ctx.send("I could not find that user.")
                return
            await self._support_open(ctx, user, message)
        elif action in {"reply", "close"} and target is not None:
            tickets = await self._migrate_tickets(ctx.guild)
            ticket = self._find_ticket(tickets, target)
            if ticket is not None:
                if action == "reply":
                    await self._support_ticket_reply(ctx, target, message)
                else:
                    await self._support_ticket_close(ctx, target)
                return
            try:
                user = await commands.UserConverter().convert(ctx, target)
            except commands.BadArgument:
                await ctx.send("I could not find that user or ticket ID.")
                return
            if action == "reply":
                await self._support_reply(ctx, user, message)
            else:
                await self._support_close(ctx, user)
        else:
            await ctx.send_help(ctx.command)

    async def _support_ticket_reply(self, ctx: commands.Context, ticket_id: str, message: str):
        try:
            if await self._reply_to_ticket(ctx.guild, ticket_id, str(ctx.author), message):
                await ctx.send("Reply sent.", delete_after=5)
            else:
                await ctx.send("That ticket is not open.")
        except discord.Forbidden:
            await ctx.send("I could not DM that user.")

    async def _support_ticket_close(self, ctx: commands.Context, ticket_id: str):
        ticket = await self._close_ticket(ctx.guild, ticket_id)
        if ticket is None:
            await ctx.send("Ticket not found.")
            return
        await ctx.send(f"Ticket {ticket_id} closed.", delete_after=5)

    async def _support_reply(self, ctx: commands.Context, user: discord.User, message: str):
        """Reply to a user through their DM."""
        tickets = await self._migrate_tickets(ctx.guild)
        ticket_id, ticket = self._find_open_ticket(tickets, user.id)
        if ticket is None or ticket_id is None:
            await ctx.send("No conversation exists for that user.")
            return

        try:
            await self._reply_to_ticket(ctx.guild, ticket_id, str(ctx.author), message)
        except discord.Forbidden:
            await ctx.send("I could not DM that user.")
            return

        await ctx.send("Reply sent.", delete_after=5)

    async def _support_open(self, ctx: commands.Context, user: discord.User, message: str):
        """Open a staff thread and start a two-way DM with a user."""
        ticket = await self._new_ticket(ctx.guild, user.id)
        ticket_id = ticket["ticket_id"]
        thread = await self._create_thread(ctx.guild, user, ticket_id)
        if thread is None:
            await self._close_ticket(ctx.guild, ticket_id)
            await ctx.send("The configured support channel is missing or is not a text channel.")
            return
        async with self.config.guild(ctx.guild).tickets() as all_tickets:
            all_tickets[ticket_id]["thread_id"] = thread.id

        try:
            await user.send(
                embed=self._conversation_embed(
                    f"Support ticket {ticket_id} opened",
                    f"Your ticket ID is `{ticket_id}`. Use `contactclose {ticket_id}` when you are finished.\n\n{message}",
                    discord.Color.green(),
                )
            )
        except discord.Forbidden:
            await ctx.send("The thread was opened, but I could not DM that user.")
            return

        await self._append_message(ctx.guild, ticket_id, str(ctx.author), message, "staff")
        await thread.send(
            embed=self._conversation_embed(
                f"Message from {ctx.author}", message, discord.Color.green()
            )
        )
        await ctx.send(f"Conversation opened: {thread.mention}")

    async def _support_close(self, ctx: commands.Context, user: discord.User):
        """Close a support conversation and send its transcript."""
        tickets = await self._migrate_tickets(ctx.guild)
        ticket_id, ticket = self._find_open_ticket(tickets, user.id)
        if ticket is None or ticket_id is None:
            await ctx.send("No conversation exists for that user.")
            return
        closed_ticket = await self._close_ticket(ctx.guild, ticket_id)
        if closed_ticket is None:
            await ctx.send("No conversation exists for that user.")
            return
        transcript = "\n".join(
            f"[{entry['timestamp']}] {entry['author']}: {entry['content']}"
            for entry in closed_ticket["messages"]
        )

        await ctx.send(
            f"Conversation with {user.mention} closed.",
            file=discord.File(
                BytesIO(transcript.encode("utf-8")),
                filename=f"conversation-{ticket_id}.txt",
            ),
        )
        try:
            await user.send(
                embed=self._conversation_embed(
                    "Conversation ended",
                    "This conversation has ended. Please contact staff again if you need further assistance.",
                    discord.Color.red(),
                )
            )
        except discord.Forbidden:
            pass

    async def _support_list(self, ctx: commands.Context):
        """List open support conversations."""
        tickets = await self._migrate_tickets(ctx.guild)
        open_tickets = [ticket_id for ticket_id, ticket in tickets.items() if ticket.get("status") == "open"]
        await ctx.send("Open tickets: " + (", ".join(open_tickets) if open_tickets else "none"))

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if message.author.bot:
            return

        if message.guild is None:
            guild = await self._ticket_guild(message.author.id)
            if guild is None:
                guild = await self._configured_guild()
            if guild is None:
                return

            open_tickets = await self._open_tickets_for_user(guild, message.author.id)
            pending_choices = await self.config.guild(guild).pending_ticket_choices()
            pending_ticket_id = pending_choices.get(str(message.author.id))
            content = message.content.strip()

            if pending_ticket_id not in open_tickets:
                pending_ticket_id = None
                async with self.config.guild(guild).pending_ticket_choices() as choices:
                    choices.pop(str(message.author.id), None)

            if len(open_tickets) > 1 and content in open_tickets:
                async with self.config.guild(guild).pending_ticket_choices() as choices:
                    choices[str(message.author.id)] = content
                await message.author.send(
                    f"Ticket {content} selected. Your next message will be sent to that ticket."
                )
                return
            if len(open_tickets) > 1 and pending_ticket_id is None:
                await self._ask_for_ticket(guild, message.author, list(open_tickets))
                return

            ticket_id = pending_ticket_id or next(iter(open_tickets), None)
            if ticket_id is None:
                ticket = await self._new_ticket(guild, message.author.id)
                ticket_id = ticket["ticket_id"]
                await message.author.send(
                    embed=self._conversation_embed(
                        f"Support ticket {ticket_id} created",
                        f"Your ticket ID is `{ticket_id}`. Keep it to select this ticket when you have multiple open tickets.\n\nTo close it, use `contactclose {ticket_id}`.",
                        discord.Color.green(),
                    )
                )
            else:
                ticket = open_tickets[ticket_id]

            ticket = await self._append_message(
                guild, ticket_id, str(message.author), message.content, "user"
            )
            if ticket is None:
                return
            await self._send_staff_message(guild, ticket, message)
            return

        tickets = await self._migrate_tickets(message.guild)
        ticket = next(
            (
                candidate
                for candidate in tickets.values()
                if candidate.get("thread_id") == message.channel.id and candidate.get("status") == "open"
            ),
            None,
        )
        if ticket is None or not isinstance(message.channel, discord.Thread):
            return

        context = await self.bot.get_context(message)
        if context.valid:
            return

        ticket_id = next(
            (ticket_id for ticket_id, value in tickets.items() if value.get("thread_id") == message.channel.id),
            None,
        )
        if ticket_id is None:
            return
        user_id = tickets[ticket_id].get("user_id")

        content = message.content or "(attachment only)"
        if message.attachments:
            content += "\n" + "\n".join(attachment.url for attachment in message.attachments)

        try:
            user = await self.bot.fetch_user(int(user_id))
            await user.send(
                embed=self._conversation_embed(
                    f"Message from {message.author}", content, discord.Color.blurple()
                )
            )
        except (discord.Forbidden, discord.HTTPException, StopAsyncIteration):
            await message.channel.send("I could not deliver that reply to the user.")
            return

        await self._append_message(message.guild, ticket_id, str(message.author), content, "staff")
        try:
            await message.add_reaction("✅")
        except (discord.Forbidden, discord.HTTPException):
            pass