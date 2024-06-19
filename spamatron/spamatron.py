from redbot.core import commands
import discord

class Spamatron(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.guild_only()
    @commands.command()
    @commands.has_permissions(administrator=True)
    async def spam(self, ctx, channel: discord.TextChannel, amount: int, *, message: str):
        """Spam a message in a channel a specified number of times."""
        if amount <= 0:
            return await ctx.send("Please provide a positive number for the amount.")

        confirmation = await ctx.send(
            f"Are you sure you want to send `{amount}` messages to {channel.mention}? Reply with `yes` to confirm."
        )

        try:
            reply = await self.bot.wait_for(
                "message",
                check=lambda m: m.author == ctx.author
                and m.channel == ctx.channel
                and m.content.lower() == "yes",
                timeout=30,
            )
        except TimeoutError:
            return await ctx.send("Confirmation timed out. Aborting.")

        for _ in range(amount):
            await channel.send(message)

        await ctx.send(f"Successfully sent `{amount}` messages to {channel.mention}.")

    @commands.guild_only()
    @commands.command()
    @commands.has_permissions(administrator=True)
    async def ghostping(self, ctx, users: commands.Greedy[discord.Member], *, reason: str = None):
        """Ghost ping one or multiple users with optional reason and customizable deletion delay."""
        deletion_delay = 10  # seconds
        await ctx.send("Ghost ping initiated...", delete_after=deletion_delay)
        for user in users:
            await ctx.send(f"{user.mention}", delete_after=0.1)
        if reason:
            await ctx.send(f"Ghost pinged {', '.join(u.mention for u in users)} for reason: {reason}", delete_after=deletion_delay)
        else:
            await ctx.send(f"Ghost pinged {', '.join(u.mention for u in users)}", delete_after=deletion_delay)


