import html
import typing

import discord
from redbot.core import commands


def dashboard_page(*args, **kwargs):
    """Mark a method as a page for the Red Dashboard cog."""
    def decorator(func):
        func.__dashboard_decorator_params__ = (args, kwargs)
        return func

    return decorator


class ContactDashboard:
    """Red Dashboard integration for the contact cog."""

    @commands.Cog.listener()
    async def on_dashboard_cog_add(self, dashboard_cog: commands.Cog) -> None:
        dashboard_cog.rpc.third_parties_handler.add_third_party(self)

    @dashboard_page(
        name=None,
        description="Contact Support Dashboard",
        methods=("GET",),
        context_ids=["guild_id"],
    )
    async def dashboard_support(self, guild: discord.Guild, **kwargs) -> typing.Dict[str, typing.Any]:
        tickets = await self.config.tickets()
        open_tickets = [ticket for ticket in tickets.values() if ticket.get("status") == "open"]
        configured_channel = await self.config.guild(guild).staff_channel()
        channel = guild.get_channel(configured_channel) if configured_channel else None
        channel_name = channel.mention if channel else "Not configured"

        rows = []
        for user_id, ticket in tickets.items():
            if ticket.get("status") != "open":
                continue
            messages = ticket.get("messages", [])
            last_message = messages[-1].get("content", "") if messages else "No messages yet"
            rows.append(
                "<li><strong>User "
                + html.escape(str(user_id))
                + "</strong>: "
                + html.escape(last_message[:200])
                + "</li>"
            )

        conversation_list = "".join(rows) or "<li>No open conversations.</li>"
        page = f"""
        <div style="padding: 24px; color: #e6e6e6; background: #1e1f22; border-radius: 8px;">
            <h2 style="color: #ffffff;">Contact Support</h2>
            <p>Live support conversation overview for <strong>{html.escape(guild.name)}</strong>.</p>
            <p><strong>Staff channel:</strong> {html.escape(str(channel_name))}</p>
            <p><strong>Open conversations:</strong> {len(open_tickets)}</p>
            <h3 style="color: #ffffff;">Conversations</h3>
            <ul>{conversation_list}</ul>
        </div>
        """
        return {"status": 0, "web_content": {"source": page}}

    async def dashboard_embed(self, guild: discord.Guild) -> discord.Embed:
        tickets = await self.config.tickets()
        open_tickets = [ticket for ticket in tickets.values() if ticket.get("status") == "open"]
        configured = await self.config.guild(guild).staff_channel()

        embed = discord.Embed(title="Contact Dashboard", color=discord.Color.blurple())
        embed.add_field(name="Open conversations", value=str(len(open_tickets)))
        embed.add_field(name="Configured channel", value="yes" if configured else "no")
        return embed