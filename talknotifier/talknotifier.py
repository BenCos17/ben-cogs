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

    async def parse_channel_mention(self, ctx, channel_mention):
        if not channel_mention.startswith("<#") or not channel_mention.endswith(">"):
            return None

        channel_id = int(channel_mention[2:-1])
        return ctx.guild.get_channel(channel_id)

    @commands.guild_only()
    @commands.command()
    @commands.has_permissions(administrator=True)
    async def spam(self, ctx, channel_mention: str, amount: int, *, message: str):
        """Spam a message in a channel a specified number of times."""
        target_channel = await self.parse_channel_mention(ctx, channel_mention)
        if not target_channel:
            return await ctx.send("Invalid channel mention.")

        if amount <= 0:
            return await ctx.send("Please provide a positive number for the amount.")

        confirmation = await ctx.send(
            f"Are you sure you want to send `{amount}` messages to {target_channel.mention}? Reply with `yes` to confirm."
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
            await target_channel.send(message)

        await ctx.send(f"Successfully sent `{amount}` messages to {target_channel.mention}.")
