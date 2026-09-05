import discord


class ContactDashboard:
    """Dashboard helpers for the contact cog."""

    async def dashboard_embed(self, guild: discord.Guild) -> discord.Embed:
        tickets = await self.config.tickets()
        open_tickets = [ticket for ticket in tickets.values() if ticket.get("status") == "open"]
        configured = await self.config.guild(guild).staff_channel()

        embed = discord.Embed(title="Contact Dashboard", color=discord.Color.blurple())
        embed.add_field(name="Open conversations", value=str(len(open_tickets)))
        embed.add_field(name="Configured channel", value="yes" if configured else "no")
        return embed