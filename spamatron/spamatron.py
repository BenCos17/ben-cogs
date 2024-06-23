from redbot.core import commands
import discord
import asyncio

class Spamatron(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.ghostping_tasks = {}

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
    async def ghostping(self, ctx, member: discord.Member, amount: int = 1, interval: int = 1):
        """Ghostping a member."""
        if amount <= 0:
            return await ctx.send("Please provide a positive number for the amount.")
        if interval <= 0:
            return await ctx.send("Please provide a positive number for the interval.")

        if ctx.author.id in self.ghostping_tasks:
            return await ctx.send("You already have a ghostping task running.")

        async def ghostping_task(member, amount, interval):
            for _ in range(amount):
                msg = await ctx.send(f"{member.mention} has been ghostpinged.")
                await msg.delete()
                await asyncio.sleep(interval)
            self.ghostping_tasks.pop(ctx.author.id, None)  # Remove the task from the dictionary after completion

        self.ghostping_tasks[ctx.author.id] = self.bot.loop.create_task(ghostping_task(member, amount, interval))
        await ctx.send(f"Ghostping task started for {member.mention} with {amount} pings at an interval of {interval} seconds.")

    @commands.guild_only()
    @commands.command()
    @commands.has_permissions(administrator=True)
    async def stopghostping(self, ctx):
        """Stop the ghostping task."""
        if ctx.author.id not in self.ghostping_tasks:
            return await ctx.send("You don't have a ghostping task running.")

        task = self.ghostping_tasks.pop(ctx.author.id)
        task.cancel()
        await ctx.send("Ghostping task stopped.")

