import discord
from redbot.core import commands
from redbot.core import Config
import asyncio
import time

class TalkNotifier(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.config = Config.get_conf(self, identifier=492089091320446976)
        default_global = {"notification_message": "{author} said: {content}", "target_users": [], "cooldown": 10}
        self.config.register_global(**default_global)
        self.cooldowns = {}

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author == self.bot.user:
            return

        channel = message.channel
        notification_message = await self.config.notification_message()
        target_users = await self.config.target_users()
        cooldown = await self.config.cooldown()

        if message.author.id in target_users:
            if not await self.check_cooldown(message.author.id):
                msg_content = notification_message.format(author=message.author.display_name, content=message.content)
                await channel.send(msg_content)
                self.cooldowns[message.author.id] = time.time()
            else:
                await channel.send(f"Please wait for the cooldown period to end before sending another notification.")

    @commands.command()
    @commands.guild_only()
    @commands.admin_or_permissions(manage_guild=True)
    async def setnotificationmessage(self, ctx, *, message: str):
        """Set the notification message for the server."""
        await self.config.notification_message.set(message)
        await ctx.send("Notification message has been set successfully.")

    @commands.command()
    @commands.guild_only()
    @commands.admin_or_permissions(manage_guild=True)
    async def showcurrentnotificationmessage(self, ctx):
        """Display the current notification message."""
        notification_message = await self.config.notification_message()
        await ctx.send(f"Current notification message: {notification_message}")

    @commands.command()
    @commands.guild_only()
    @commands.admin_or_permissions(manage_guild=True)
    async def addtargetuser(self, ctx, user: discord.Member):
        """Add a user to the target list for notifications."""
        target_users = await self.config.target_users()
        if user.id not in target_users:
            target_users.append(user.id)
            await self.config.target_users.set(target_users)
            await ctx.send(f"{user.display_name} will now receive notifications.")
        else:
            await ctx.send(f"{user.display_name} is already set to receive notifications.")

    @commands.command()
    @commands.guild_only()
    @commands.admin_or_permissions(manage_guild=True)
    async def removetargetuser(self, ctx, user: discord.Member):
        """Remove a user from the target list for notifications."""
        target_users = await self.config.target_users()
        if user.id in target_users:
            target_users.remove(user.id)
            await self.config.target_users.set(target_users)
            await ctx.send(f"{user.display_name} will no longer receive notifications.")
        else:
            await ctx.send(f"{user.display_name} is not set to receive notifications.")

    @commands.command()
    @commands.guild_only()
    @commands.admin_or_permissions(manage_guild=True)
    async def cleartargetusers(self, ctx):
        """Clear all target users from the notification list."""
        await self.config.target_users.set([])
        await ctx.send("All target users have been cleared.")

    @commands.command()
    @commands.guild_only()
    @commands.admin_or_permissions(manage_guild=True)
    async def listtargetusers(self, ctx):
        """List all users who are set to receive notifications."""
        target_users = await self.config.target_users()
        if target_users:
            user_names = []
            for user_id in target_users:
                user = ctx.guild.get_member(user_id)
                if user:
                    user_names.append(user.display_name)
            if user_names:
                await ctx.send("Target users: " + ", ".join(user_names))
            else:
                await ctx.send("No target users found.")
        else:
            await ctx.send("There are currently no target users set.")

    @commands.command()
    @commands.guild_only()
    @commands.admin_or_permissions(manage_guild=True)
    async def setcooldown(self, ctx, cooldown: int):
        """Set the cooldown period for notifications."""
        if cooldown < 0:
            await ctx.send("Cooldown cannot be negative.")
        else:
            await self.config.cooldown.set(cooldown)
            await ctx.send(f"Cooldown set to {cooldown} seconds.")

    async def check_cooldown(self, user_id):
        cooldown = await self.config.cooldown()
        last_message_time = self.cooldowns.get(user_id, 0)
        if time.time() - last_message_time < cooldown:
            return True
        return False
