import discord
from redbot.core import commands
from redbot.core import Config
import asyncio
import time
import typing as t
import wtforms
import logging

# Set up logging
logger = logging.getLogger("TalkNotifier")

def dashboard_page(*args, **kwargs):
    def decorator(func: t.Callable):
        func.__dashboard_decorator_params__ = (args, kwargs)
        return func
    return decorator

class DashboardIntegration:
    bot: commands.Bot

    @commands.Cog.listener()
    async def on_dashboard_cog_add(self, dashboard_cog: commands.Cog) -> None:
        dashboard_cog.rpc.third_parties_handler.add_third_party(self)

class TalkNotifier(DashboardIntegration, commands.Cog):
    def __init__(self, bot):
        super().__init__()
        self.bot = bot
        self.config = Config.get_conf(self, identifier=492089091320446976)
        default_guild = {"notification_message": "{author} said: {content}", "target_users": [], "cooldown": 10}
        self.config.register_guild(**default_guild)
        self.cooldowns = {}

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author == self.bot.user:
            return

        if message.guild is None:
            return  # Ignore DMs

        channel = message.channel
        guild_id = message.guild.id
        notification_message = await self.config.guild(message.guild).notification_message()
        target_users = await self.config.guild(message.guild).target_users()
        cooldown = await self.config.guild(message.guild).cooldown()

        if message.author.id in target_users:
            if not await self.check_cooldown(message.author.id, guild_id):
                msg_content = notification_message.format(author=message.author.display_name, content=message.content)
                await channel.send(msg_content)
                self.cooldowns.setdefault(guild_id, {})[message.author.id] = time.time()  # Update cooldown time

    async def check_cooldown(self, user_id, guild_id):
        cooldown = await self.config.guild(self.bot.get_guild(guild_id)).cooldown()
        last_message_time = self.cooldowns.get(guild_id, {}).get(user_id, 0)
        return time.time() - last_message_time < cooldown  # Return True if still in cooldown

    @dashboard_page(name="settings", description="View and modify notification settings.")
    async def settings_page(self, user: discord.User, guild: discord.Guild, **kwargs) -> t.Dict[str, t.Any]:
        notification_message = await self.config.guild(guild).notification_message()
        target_users = await self.config.guild(guild).target_users()
        cooldown = await self.config.guild(guild).cooldown()

        # Create a form for updating settings
        class SettingsForm(kwargs["Form"]):
            notification_message = wtforms.TextAreaField("Notification Message", default=notification_message)
            cooldown = wtforms.IntegerField("Cooldown (seconds)", default=cooldown)
            target_user = wtforms.IntegerField("User ID to Add/Remove")
            submit = wtforms.SubmitField("Update Settings")

        # Instantiate the form with current values
        form = SettingsForm()

        # Check if the form is submitted
        if form.validate_on_submit():
            try:
                # Update notification message
                await self.config.guild(guild).notification_message.set(form.notification_message.data)
                # Update cooldown
                await self.config.guild(guild).cooldown.set(form.cooldown.data)

                # Add or remove target user
                target_users = await self.config.guild(guild).target_users()
                user_id = form.target_user.data
                if user_id:
                    if user_id not in target_users:
                        target_users.append(user_id)
                    else:
                        target_users.remove(user_id)
                    await self.config.guild(guild).target_users.set(target_users)

                return {
                    "status": 0,
                    "notifications": [
                        {"message": "Settings updated successfully!", "category": "success"},
                        {"message": "Your changes have been saved.", "category": "info"}
                    ],
                    "web_content": {
                        "source": f"""
                        <h3>Notification Settings</h3>
                        <p>Current Notification Message: {form.notification_message.data}</p>
                        <p>Target Users: {', '.join([str(guild.get_member(user_id)) for user_id in target_users])}</p>
                        <p>Cooldown: {form.cooldown.data} seconds</p>
                        {form.notification_message.label} {form.notification_message()}
                        {form.cooldown.label} {form.cooldown()}
                        {form.target_user.label} {form.target_user()}
                        {form.submit()}
                        """,
                    },
                }
            except Exception as e:
                logger.error(f"Error updating settings: {e}")
                return {
                    "status": 1,
                    "error_title": "Update Failed",
                    "error_message": f"An error occurred while updating settings: {str(e)}",
                }

        # Render the form with current values
        return {
            "status": 0,
            "web_content": {
                "source": f"""
                <h3>Notification Settings</h3>
                <p>Current Notification Message: {notification_message}</p>
                <p>Target Users: {', '.join([str(guild.get_member(user_id)) for user_id in target_users])}</p>
                <p>Cooldown: {cooldown} seconds</p>
                {form.notification_message.label} {form.notification_message()}
                {form.cooldown.label} {form.cooldown()}
                {form.target_user.label} {form.target_user()}
                {form.submit()}
                """,
            },
        }