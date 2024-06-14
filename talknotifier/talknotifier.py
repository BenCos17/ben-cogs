import discord
from redbot.core import commands
from redbot.core import Config
import asyncio

class TalkNotifier(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.config = Config.get_conf(self, identifier=492089091320446976, force_registration=True)
        default_global = {"notification_message": "{author} said: {content}", "target_users": {}, "cooldown": 10}
        self.config.register_global(**default_global)
        self.cooldowns = {}

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author == self.bot.user:
            return

        channel = message.channel
        guild_config = self.config.guild(message.guild)
        notification_message = await guild_config.notification_message()
        target_users = await guild_config.target_users()
        cooldown = await guild_config.cooldown()

        if message.author.id in target_users:
            if not await self.check_cooldown(message.author.id, cooldown):
                msg_content = notification_message.format(author=message.author.display_name, content=message.content)
                await channel.send(msg_content)
                self.cooldowns[message.author.id] = time.time()

    @commands.guild_only()
    @commands.group(name='talk', help='Notification related commands.', invoke_without_command=True, aliases=["talknotifier"])
    async def talk_group(self, ctx):
        """Notification related commands."""
        if ctx.invoked_subcommand is None:
            pass

    @talk_group.command()
    @commands.admin_or_permissions(manage_guild=True)
    async def setmessage(self, ctx, *, message: str):
        """Set the notification message for the server."""
        guild_config = self.config.guild(ctx.guild)
        await guild_config.set_raw("notification_message", value=message)
        await ctx.send("Notification message has been set successfully.")

    @talk_group.command()
    @commands.admin_or_permissions(manage_guild=True)
    async def showmessage(self, ctx):
        """Display the current notification message."""
        guild_config = self.config.guild(ctx.guild)
        notification_message = await guild_config.notification_message()
        await ctx.send(f"Current notification message: {notification_message}")

    @talk_group.command()
    @commands.admin_or_permissions(manage_guild=True)
    async def adduser(self, ctx, user: discord.Member):
        """Add a user to the target list for notifications."""
        guild_config = self.config.guild(ctx.guild)
        target_users = await guild_config.target_users()
        if user.id not in target_users:
            target_users.append(user.id)
            await guild_config.set_raw("target_users", value=target_users)
            await ctx.send(f"{user.display_name} will now receive notifications.")
        else:
            await ctx.send(f"{user.display_name} is already set to receive notifications.")

    @talk_group.command()
    @commands.admin_or_permissions(manage_guild=True)
    async def removeuser(self, ctx, user: discord.Member):
        """Remove a user from the target list for notifications."""
        guild_config = self.config.guild(ctx.guild)
        target_users = await guild_config.target_users()
        if user.id in target_users:
            target_users.remove(user.id)
            await guild_config.set_raw("target_users", value=target_users)
            await ctx.send(f"{user.display_name} will no longer receive notifications.")
        else:
            await ctx.send(f"{user.display_name} is not set to receive notifications.")

    @talk_group.command()
    @commands.admin_or_permissions(manage_guild=True)
    async def clearusers(self, ctx):
        """Clear all target users from the notification list."""
        guild_config = self.config.guild(ctx.guild)
        await guild_config.set_raw("target_users", value={})
        await ctx.send("All target users have been cleared.")

    @talk_group.command()
    @commands.admin_or_permissions(manage_guild=True)
    async def listusers(self, ctx):
        """List all users who are set to receive notifications."""
        guild_config = self.config.guild(ctx.guild)
        target_users = await guild_config.target_users()
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

    @talk_group.command()
    @commands.admin_or_permissions(manage_guild=True)
    async def setcooldown(self, ctx, cooldown: int):
        """Set the cooldown period for notifications."""
        guild_config = self.config.guild(ctx.guild)
        if cooldown < 0:
            await ctx.send("Cooldown cannot be negative.")
        else:
            await guild_config.set_raw("cooldown", value=cooldown)
            await ctx.send(f"Cooldown set to {cooldown} seconds.")

    @talk_group.command()
    @commands.admin_or_permissions(manage_guild=True)
    async def getdocs(self, ctx):
        """Get the documentation for TalkNotifier."""
        await ctx.send("You can find the documentation for TalkNotifier [here](https://github.com/BenCos17/ben-cogs/blob/main/talknotifier/docs.md).")

    async def check_cooldown(self, user_id, cooldown):
        last_message_time = self.cooldowns.get(user_id, 0)
        if time.time() - last_message_time < cooldown:
            return True
        return False


