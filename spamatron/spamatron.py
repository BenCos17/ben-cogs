from redbot.core import commands, Config
import discord
import asyncio
import random
from .dashboard_integration import DashboardIntegration

class Spamatron(commands.Cog, DashboardIntegration):
    """Cog for typo watching and ghostping features.
    
    Provides commands to watch for common typos and respond, as well as ghostping utilities for server admins.
    """
    def __init__(self, bot):
        self.bot = bot
        self.ghostping_tasks = {}
        self.ghostping_progress = {}  # Track progress: {user_id: {"current": X, "total": Y, "member": member, "channel": channel}}
        self.config = Config.get_conf(self, identifier=844628346534)
        
        # Default settings for servers - no default words
        default_guild = {
            "typo_watch": {
                "enabled": False,
                "words": {}  # Empty dictionary, no defaults
            }
        }
        
        self.config.register_guild(**default_guild)
        
        # Initialize dashboard integration
        DashboardIntegration.__init__(self)
        self._spamatron_cog = self

    @commands.guild_only()
    @commands.group()
    @commands.admin_or_permissions(administrator=True)
    async def typowatch(self, ctx):
        """Configure typo watch settings for this server.
        
        Use subcommands to add, remove, or list watched words and their responses.
        """
        if ctx.invoked_subcommand is None:
            settings = await self.config.guild(ctx.guild).typo_watch()
            enabled = "enabled" if settings["enabled"] else "disabled"
            word_list = "\n".join(
                f"• '{word_data['typo']}' → '{correct_word}' ({len(word_data['responses'])} responses)"
                for correct_word, word_data in settings["words"].items()
            )
            await ctx.send(
                f"Current typo watch settings:\n"
                f"Status: {enabled}\n"
                f"Watched words:\n{word_list}"
            )

    @typowatch.command(name="toggle")
    async def typowatch_toggle(self, ctx):
        """Toggle typo watching on or off for this server."""
        async with self.config.guild(ctx.guild).typo_watch() as settings:
            settings["enabled"] = not settings["enabled"]
            state = "enabled" if settings["enabled"] else "disabled"
        await ctx.send(f"Typo watching is now {state}")

    @typowatch.command(name="add")
    async def typowatch_add(self, ctx, correct_word: str, typo_word: str, *, first_response: str):
        """Add a new word to watch for with its first response.
        
        Example:
            [p]typowatch add available availablew Did you mean 'available'?
        """
        async with self.config.guild(ctx.guild).typo_watch() as settings:
            settings["words"][correct_word] = {
                "typo": typo_word,
                "responses": [first_response]  # Start with just the provided response
            }
        await ctx.send(f"Now watching for '{typo_word}' to suggest '{correct_word}' with 1 response")

    @typowatch.command(name="remove")
    async def typowatch_remove(self, ctx, correct_word: str):
        """Remove a word from the typo watch list for this server.
        
        Example:
            [p]typowatch remove available
        """
        async with self.config.guild(ctx.guild).typo_watch() as settings:
            if correct_word in settings["words"]:
                del settings["words"][correct_word]
                await ctx.send(f"Removed '{correct_word}' from the watch list")
            else:
                await ctx.send(f"'{correct_word}' was not in the watch list")

    @typowatch.command(name="responses")
    async def typowatch_responses(self, ctx, correct_word: str, *, responses: str):
        """Set custom responses for a watched word. Separate responses with '|'.
        
        Example:
            [p]typowatch responses available Did you mean 'available'? | That's not how you spell it! | *available
        """
        async with self.config.guild(ctx.guild).typo_watch() as settings:
            if correct_word not in settings["words"]:
                return await ctx.send(f"'{correct_word}' is not in the watch list. Add it first!")
            
            new_responses = [r.strip() for r in responses.split("|")]
            if not new_responses:
                return await ctx.send("Please provide at least one response!")
                
            settings["words"][correct_word]["responses"] = new_responses
            await ctx.send(f"Updated responses for '{correct_word}'")

    @commands.Cog.listener()
    async def on_message(self, message):
        """Listen for messages containing configured typos and respond if found."""
        if message.author.bot or not message.guild:
            return

        settings = await self.config.guild(message.guild).typo_watch()
        if not settings["enabled"]:
            return
            
        content_lower = message.content.lower()
        for correct_word, word_data in settings["words"].items():
            if word_data["typo"].lower() in content_lower:
                await message.channel.send(random.choice(word_data["responses"]))
                break  # Only respond once even if multiple typos are found

    @commands.guild_only()
    @commands.command()
    @commands.has_permissions(administrator=True)
    async def spam(self, ctx, channel: discord.TextChannel, amount: int, *, message: str):
        """Spam a message in a channel a specified number of times after confirmation."""
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
        """Ghostping a member in a specified channel a given number of times at a set interval."""
        if amount <= 0:
            return await ctx.send("Please provide a positive number for the amount.")
        if interval <= 0:
            return await ctx.send("Please provide a positive number for the interval.")

        if ctx.author.id in self.ghostping_tasks:
            return await ctx.send("You already have a ghostping task running.")

        async def ghostping_task(member, channel, amount, interval):
            # Initialize progress tracking
            self.ghostping_progress[ctx.author.id] = {
                "current": 0,
                "total": amount,
                "member": member,
                "channel": channel
            }
            
            for i in range(amount):
                msg = await channel.send(f"{member.mention} has been ghostpinged.")
                await msg.delete()
                # Update progress
                self.ghostping_progress[ctx.author.id]["current"] = i + 1
                await asyncio.sleep(interval)
            
            # Clean up after completion
            self.ghostping_tasks.pop(ctx.author.id, None)
            self.ghostping_progress.pop(ctx.author.id, None)

        self.ghostping_tasks[ctx.author.id] = self.bot.loop.create_task(ghostping_task(member, channel, amount, interval))
        await ctx.send(f"Ghostping task started for {member.mention} in {channel.mention} with {amount} pings at an interval of {interval} seconds.")

    async def start_ghostping_task(self, user_id, member: discord.Member, channel: discord.TextChannel, amount: int, interval: int):
        """Start a ghostping task from dashboard or other sources."""
        if user_id in self.ghostping_tasks:
            return False, "User already has a ghostping task running."

        async def ghostping_task(member, channel, amount, interval):
            # Initialize progress tracking
            self.ghostping_progress[user_id] = {
                "current": 0,
                "total": amount,
                "member": member,
                "channel": channel
            }
            
            for i in range(amount):
                try:
                    msg = await channel.send(f"{member.mention} has been ghostpinged.")
                    await msg.delete()
                    # Update progress
                    self.ghostping_progress[user_id]["current"] = i + 1
                    await asyncio.sleep(interval)
                except Exception as e:
                    # If there's an error, clean up and break
                    self.ghostping_tasks.pop(user_id, None)
                    self.ghostping_progress.pop(user_id, None)
                    break
            
            # Clean up after completion
            self.ghostping_tasks.pop(user_id, None)
            self.ghostping_progress.pop(user_id, None)

        self.ghostping_tasks[user_id] = self.bot.loop.create_task(ghostping_task(member, channel, amount, interval))
        return True, f"Ghostping task started for {member.display_name} in {channel.name} ({amount} pings, {interval}s interval)"

    @commands.guild_only()
    @commands.command()
    @commands.has_permissions(administrator=True)
    async def stopghostping(self, ctx):
        """Stop the currently running ghostping task for the command author."""
        if ctx.author.id not in self.ghostping_tasks:
            return await ctx.send("You don't have a ghostping task running.")

        task = self.ghostping_tasks.pop(ctx.author.id)
        task.cancel()
        # Clean up progress tracking
        self.ghostping_progress.pop(ctx.author.id, None)
        await ctx.send("Ghostping task stopped.")

    @commands.guild_only()
    @commands.command()
    @commands.has_permissions(administrator=True)
    async def ghostpingtasks(self, ctx):
        """Show all currently running ghostping tasks."""
        if not self.ghostping_tasks:
            return await ctx.send("No ghostping tasks are currently running.")
        
        embed = discord.Embed(title="Active Ghostping Tasks", color=discord.Color.blue())
        
        for user_id, task in self.ghostping_tasks.items():
            user = ctx.guild.get_member(user_id)
            user_name = user.display_name if user else f"User {user_id}"
            task_status = "Running" if not task.done() else "Completed"
            status_emoji = "🟢" if not task.done() else "🔴"
            
            # Get progress information
            progress_info = ""
            if user_id in self.ghostping_progress:
                progress = self.ghostping_progress[user_id]
                target_member = progress["member"]
                target_channel = progress["channel"]
                current = progress["current"]
                total = progress["total"]
                progress_info = f"\nTarget: {target_member.display_name}\nChannel: {target_channel.name}\nProgress: {current}/{total} pings"
            
            embed.add_field(
                name=f"{status_emoji} {user_name}",
                value=f"User ID: {user_id}\nTask ID: {id(task)}\nStatus: {task_status}{progress_info}",
                inline=False
            )
        
        await ctx.send(embed=embed)

    @typowatch.command(name="list")
    async def typowatch_list(self, ctx, word: str = None):
        """List all watched words or details about a specific word.
        
        Example:
            [p]typowatch list
            [p]typowatch list available
        """
        settings = await self.config.guild(ctx.guild).typo_watch()
        
        if word:
            if word not in settings["words"]:
                return await ctx.send(f"'{word}' is not in the watch list")
            
            word_data = settings["words"][word]
            responses = "\n".join(f"{i+1}. {r}" for i, r in enumerate(word_data["responses"]))
            await ctx.send(
                f"Details for '{word}':\n"
                f"Typo: {word_data['typo']}\n"
                f"Responses:\n{responses}"
            )
        else:
            if not settings["words"]:
                return await ctx.send("No words are being watched")
            
            word_list = "\n".join(
                f"• '{word}' → '{data['typo']}' ({len(data['responses'])} responses)"
                for word, data in settings["words"].items()
            )
            await ctx.send(f"Watched words:\n{word_list}")

    @typowatch.command(name="edit")
    async def typowatch_edit(self, ctx, word: str, new_typo: str):
        """Edit the typo for a watched word."""
        async with self.config.guild(ctx.guild).typo_watch() as settings:
            if word not in settings["words"]:
                return await ctx.send(f"'{word}' is not in the watch list")
            
            settings["words"][word]["typo"] = new_typo
            await ctx.send(f"Updated typo for '{word}' to '{new_typo}'")

    @typowatch.command(name="addresponse")
    async def typowatch_addresponse(self, ctx, word: str, *, response: str):
        """Add a new response for a word
        
        Example:
        [p]typowatch addresponse available I think you meant 'available'!"""
        async with self.config.guild(ctx.guild).typo_watch() as settings:
            if word not in settings["words"]:
                return await ctx.send(f"'{word}' is not in the watch list")
            
            settings["words"][word]["responses"].append(response)
            await ctx.send(f"Added new response for '{word}'")

    @typowatch.command(name="delresponse")
    async def typowatch_delresponse(self, ctx, word: str, index: int):
        """Delete a response for a word by its number (use list command to see numbers)
        
        Example:
        [p]typowatch delresponse available 2"""
        async with self.config.guild(ctx.guild).typo_watch() as settings:
            if word not in settings["words"]:
                return await ctx.send(f"'{word}' is not in the watch list")
            
            responses = settings["words"][word]["responses"]
            if index < 1 or index > len(responses):
                return await ctx.send(f"Invalid response number. Use numbers 1-{len(responses)}")
            
            removed = responses.pop(index - 1)
            await ctx.send(f"Removed response: {removed}")

    @typowatch.command(name="editresponse")
    async def typowatch_editresponse(self, ctx, word: str, index: int, *, new_response: str):
        """Edit a specific response for a word by its number
        
        Example:
        [p]typowatch editresponse available 1 Did you mean to type 'available'?"""
        async with self.config.guild(ctx.guild).typo_watch() as settings:
            if word not in settings["words"]:
                return await ctx.send(f"'{word}' is not in the watch list")
            
            responses = settings["words"][word]["responses"]
            if index < 1 or index > len(responses):
                return await ctx.send(f"Invalid response number. Use numbers 1-{len(responses)}")
            
            old_response = responses[index - 1]
            responses[index - 1] = new_response
            await ctx.send(f"Updated response:\nOld: {old_response}\nNew: {new_response}")


def setup(bot):
    """Add the cog to the bot."""
    bot.add_cog(Spamatron(bot))

