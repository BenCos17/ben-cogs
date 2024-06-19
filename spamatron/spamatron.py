from redbot.core import commands, Config
import discord
import asyncio

class Spamatron(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.config = Config.get_conf(self, identifier=492089091320446976)

        default_guild_settings = {
            "deletion_delay": 10,
        }

        self.config.register_guild(**default_guild_settings)
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
        except asyncio.TimeoutError:
            return await ctx.send("Confirmation timed out. Aborting.")

        for _ in range(amount):
            await channel.send(message)

        await ctx.send(f"Successfully sent `{amount}` messages to {channel.mention}.")

    @commands.guild_only()
    @commands.command()
    @commands.has_permissions(administrator=True)
    async def ghostping(self, ctx, channel: discord.TextChannel, users: commands.Greedy[discord.Member], *, reason: str = None):
        """Ghost ping one or multiple users with optional reason and customizable deletion delay."""
        deletion_delay = await self.config.guild(ctx.guild).deletion_delay()
        await ctx.send("Ghost ping initiated...", delete_after=deletion_delay)
        for user in users:
            await channel.send(f"{user.mention}", delete_after=0.1)
        if reason:
            await channel.send(f"Ghost pinged {', '.join(u.mention for u in users)} for reason: {reason}", delete_after=deletion_delay)
        else:
            await channel.send(f"Ghost pinged {', '.join(u.mention for u in users)}", delete_after=deletion_delay)

    @commands.guild_only()
    @commands.command()
    @commands.has_permissions(administrator=True)
    async def set_deletion_delay(self, ctx, delay: int):
        """Set the deletion delay for ghost pings."""
        await self.config.guild(ctx.guild).deletion_delay.set(delay)
        await ctx.send(f"Deletion delay set to {delay} seconds.")

    @commands.guild_only()
    @commands.command()
    @commands.has_permissions(administrator=True)
    async def random_ghostping(self, ctx, channel: discord.TextChannel, users: commands.Greedy[discord.Member], duration: int, interval: int, *, reason: str = None):
        """Randomly ghost ping one or multiple users over a specified duration with a specified interval."""
        await ctx.send("Random ghost ping initiated...", delete_after=await self.config.guild(ctx.guild).deletion_delay())

        task = self.bot.loop.create_task(self.random_ghostping_task(ctx, channel, users, duration, interval, reason))
        self.ghostping_tasks[ctx.guild.id] = task

    async def random_ghostping_task(self, ctx, channel, users, duration, interval, reason):
        end_time = ctx.message.created_at.timestamp() + duration
        deletion_delay = await self.config.guild(ctx.guild).deletion_delay()

        while True:
            for user in users:
                await channel.send(f"{user.mention}", delete_after=0.1)
            if reason:
                await channel.send(f"Ghost pinged {', '.join(u.mention for u in users)} for reason: {reason}", delete_after=deletion_delay)
            else:
                await channel.send(f"Ghost pinged {', '.join(u.mention for u in users)}", delete_after=deletion_delay)
            await asyncio.sleep(interval)
            if ctx.message.created_at.timestamp() >= end_time:
                break

    @commands.guild_only()
    @commands.command()
    @commands.has_permissions(administrator=True)
    async def stop_ghostping(self, ctx):
        """Stop the random ghost ping task."""
        task = self.ghostping_tasks.get(ctx.guild.id)
        if task:
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                pass
            del self.ghostping_tasks[ctx.guild.id]
            await ctx.send("Random ghost ping task stopped successfully.")
        else:
            await ctx.send("No random ghost ping task is running.")

def setup(bot):
    bot.add_cog(Spamatron(bot))
