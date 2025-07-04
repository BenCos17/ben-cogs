import discord
from redbot.core import commands
from redbot.core.bot import Red

class AutoChannel(commands.Cog):
    """Cog to automatically reply in specified channels."""
    def __init__(self, bot: Red):
        self.bot = bot
        self.reply_channels = {}

    @commands.group()
    async def autochannel(self, ctx: commands.Context):
        """Manage always reply settings for channels in this server."""
        if ctx.invoked_subcommand is None:
            await ctx.send_help(ctx.command)

    @autochannel.command()
    async def set(self, ctx: commands.Context, channel: discord.TextChannel):
        """Set a channel to always reply in automatically."""
        self.reply_channels[channel.id] = True
        await ctx.send(f"Always reply set for {channel.mention}")

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        """Invoke the bot's command context in channels set for auto-reply."""
        if message.channel.id in self.reply_channels:
            ctx = await self.bot.get_context(message, cls=commands.Context)
            if not ctx.prefix:
                ctx.prefix = ''
            await self.bot.invoke(ctx)





