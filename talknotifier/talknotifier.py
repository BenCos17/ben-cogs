import discord
from redbot.core import commands
from redbot.core import Config

class TalkNotifier(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.config = Config.get_conf(self, identifier=1234567890)
        default_global = {"default_notification_message": "Someone spoke!"}
        self.config.register_global(**default_global)

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author == self.bot.user:
            return

        channel = message.channel
        user_id = str(message.author.id)

        # Retrieve the custom notification message for the user
        notification_message = await self.config.member_from_id(message.author.id).get_raw("notification_message", default=None)

        if notification_message is not None:
            msg_content = notification_message.format(author=message.author.display_name, content=message.content)
            await channel.send(msg_content)
        else:
            default_message = await self.config.default_notification_message()
            msg_content = default_message.format(author=message.author.display_name, content=message.content)
            await channel.send(msg_content)

    @commands.command()
    @commands.guild_only()
    @commands.admin_or_permissions(manage_guild=True)
    async def setnotificationmessage(self, ctx, user: discord.Member, *, message: str):
        # Set custom notification message for the user
        await self.config.member(user).notification_message.set(message)
        await ctx.send(f"Notification message for {user.display_name} has been set successfully.")

    @commands.command()
    @commands.guild_only()
    @commands.admin_or_permissions(manage_guild=True)
    async def resetnotificationmessage(self, ctx, user: discord.Member):
        # Reset custom notification message for the user
        await self.config.member(user).notification_message.clear()
        await ctx.send(f"Notification message for {user.display_name} has been reset.")

    @commands.command()
    @commands.guild_only()
    @commands.admin_or_permissions(manage_guild=True)
    async def setdefaultnotificationmessage(self, ctx, *, message: str):
        # Set default notification message
        await self.config.default_notification_message.set(message)
        await ctx.send("Default notification message has been set successfully.")
    
    @commands.command()
    @commands.guild_only()
    @commands.admin_or_permissions(manage_guild=True)
    async def setusernotificationmessage(self, ctx, user: discord.Member, *, message: str):
        # Set notification message for a specific user
        await self.config.member(user).notification_message.set(message)
        await ctx.send(f"Notification message for {user.display_name} has been set successfully.")

def setup(bot):
    bot.add_cog(TalkNotifier(bot))
