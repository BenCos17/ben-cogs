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
    async def ghostping(self, ctx, channel: discord.TextChannel, users: commands.Greedy[discord.Member], *, reason: str = None):
        """Ghost ping one or multiple users with optional reason and customizable deletion delay."""
        deletion_delay = 10  # seconds
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
    async def random_ghostping(self, ctx, channel: discord.TextChannel, users: commands.Greedy[discord.Member], duration: int, interval: int, *, reason: str = None):
        """Randomly ghost ping one or multiple users over a specified duration with a specified interval."""
        await ctx.send("Random ghost ping initiated...", delete_after=10)
        self.bot.loop.create_task(self.random_ghostping_task(ctx, channel, users, duration, interval, reason))

    async def random_ghostping_task(self, ctx, channel, users, duration, interval, reason):
        end_time = ctx.message.created_at.timestamp() + duration
        while True:
            for user in users:
                await channel.send(f"{user.mention}", delete_after=0.1)
            if reason:
                await channel.send(f"Ghost pinged {', '.join(u.mention for u in users)} for reason: {reason}", delete_after=10)
            else:
                await channel.send(f"Ghost pinged {', '.join(u.mention for u in users)}", delete_after=10)
            await asyncio.sleep(interval)
            if ctx.message.created_at.timestamp() >= end_time:
                break
    @commands.guild_only()
    @commands.command()
    @commands.has_permissions(administrator=True)
    async def stop_ghostping(self, ctx):
        """Stop the random ghost ping task."""
        await self.stop_ghostping_task(ctx)
        await ctx.send("Random ghost ping task stopped successfully.")

    async def stop_ghostping_task(self, ctx):
        tasks = [task for task in asyncio.all_tasks() if task.get_name() == 'random_ghostping_task']
        for task in tasks:
            try:
                task.cancel()
            except Exception as e:
                print(f"Error canceling task: {e}")
            else:
                task.exception()

