import discord
from redbot.core import commands
from redbot.core import Config

class TalkNotifier(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.config = Config.get_conf(self, identifier=1234567890)
        default_global = {"notification_message": "Someone spoke!", "target_user": None}
        self.config.register_global(**default_global)

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author == self.bot.user:
            return

        channel = message.channel
        notification_message = await self.config.notification_message()
        target_user_id = await self.config.target_user()

        if target_user_id == message.author.id:
            # Customize the message content as needed
            msg_content = notification_message.format(author=message.author.display_name, content=message.content)

            # Sending the message to the same channel where the event occurred
            await channel.send(msg_content)

    @commands.command()
    @commands.guild_only()
    @commands.admin_or_permissions(manage_guild=True)
    async def setnotificationmessage(self, ctx, *, message: str):
        await self.config.notification_message.set(message)
        await ctx.send("Notification message has been set successfully.")

    @commands.command()
    @commands.guild_only()
    @commands.admin_or_permissions(manage_guild=True)
    async def settargetuser(self, ctx, user: discord.Member):
        await self.config.target_user.set(user.id)
        await ctx.send(f"Notifications will now be sent whenever {user.display_name} speaks.")

def setup(bot):
    bot.add_cog(TalkNotifier(bot))
