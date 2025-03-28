from redbot.core import commands, Config
import discord
import asyncio
import random

class Spamatron(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.ghostping_tasks = {}
        self.config = Config.get_conf(self, identifier=844628346534)
        
        # Default settings for servers
        default_guild = {
            "typo_watch": {
                "enabled": False,
                "watch_word": "available",
                "replace_word": "availablew"
            }
        }
        
        self.config.register_guild(**default_guild)

    @commands.guild_only()
    @commands.group()
    @commands.admin_or_permissions(administrator=True)
    async def typowatch(self, ctx):
        """Configure the typo watch settings"""
        if ctx.invoked_subcommand is None:
            settings = await self.config.guild(ctx.guild).typo_watch()
            enabled = "enabled" if settings["enabled"] else "disabled"
            await ctx.send(
                f"Current typo watch settings:\n"
                f"Status: {enabled}\n"
                f"Watching for: '{settings['replace_word']}' (should be '{settings['watch_word']}')"
            )

    @typowatch.command(name="toggle")
    async def typowatch_toggle(self, ctx):
        """Toggle typo watching on/off"""
        async with self.config.guild(ctx.guild).typo_watch() as settings:
            settings["enabled"] = not settings["enabled"]
            state = "enabled" if settings["enabled"] else "disabled"
        await ctx.send(f"Typo watching is now {state}")

    @typowatch.command(name="set")
    async def typowatch_set(self, ctx, correct_word: str, typo_word: str):
        """Set the words to watch for
        
        Example:
        [p]typowatch set available availablew
        """
        async with self.config.guild(ctx.guild).typo_watch() as settings:
            settings["watch_word"] = correct_word
            settings["replace_word"] = typo_word
        await ctx.send(f"Now watching for '{typo_word}' to suggest '{correct_word}'")

    @commands.Cog.listener()
    async def on_message(self, message):
        """Listen for messages containing the configured typo"""
        if message.author.bot or not message.guild:
            return

        settings = await self.config.guild(message.guild).typo_watch()
        if not settings["enabled"]:
            return
            
        if settings["replace_word"].lower() in message.content.lower():
            responses = [
                f"Did you mean '{settings['watch_word']}'? 🤔",
                f"I see that typo sneaking in there... 👀",
                f"*{settings['watch_word']} (I'm just your friendly typo detector)",
                f"Ah yes, the classic {settings['replace_word']}™",
                "Someone's fingers are getting creative with spelling!"
            ]
            await message.channel.send(random.choice(responses))

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
    async def ghostping(self, ctx, member: discord.Member, channel: discord.TextChannel, amount: int = 1, interval: int = 1):
        """Ghostping a member in a specified channel."""
        if amount <= 0:
            return await ctx.send("Please provide a positive number for the amount.")
        if interval <= 0:
            return await ctx.send("Please provide a positive number for the interval.")

        if ctx.author.id in self.ghostping_tasks:
            return await ctx.send("You already have a ghostping task running.")

        async def ghostping_task(member, channel, amount, interval):
            for _ in range(amount):
                msg = await channel.send(f"{member.mention} has been ghostpinged.")
                await msg.delete()
                await asyncio.sleep(interval)
            self.ghostping_tasks.pop(ctx.author.id, None)  # Remove the task from the dictionary after completion

        self.ghostping_tasks[ctx.author.id] = self.bot.loop.create_task(ghostping_task(member, channel, amount, interval))
        await ctx.send(f"Ghostping task started for {member.mention} in {channel.mention} with {amount} pings at an interval of {interval} seconds.")

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

