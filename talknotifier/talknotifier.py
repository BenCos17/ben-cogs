import discord
from redbot.core import commands
from redbot.core import Config
import asyncio

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

        if message.author.id in target_users:
            msg_content = notification_message.format(author=message.author.display_name, content=message.content)
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
    async def addtargetuser(self, ctx, user: discord.Member):
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
    async def setcooldown(self, ctx, cooldown: int):
        await self.config.cooldown.set(cooldown)
        await ctx.send(f"Cooldown set to {cooldown} seconds.")

    async def check_cooldown(self, user_id):
        cooldown = await self.config.cooldown()
        if user_id in self.cooldowns:
            if self.cooldowns[user_id] + cooldown > time():
                return True
        return False

def setup(bot):
    bot.add_cog(TalkNotifier(bot))
