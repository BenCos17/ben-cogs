from redbot.core import commands
import discord

class Spamatron(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    async def parse_channel_mention(self, ctx, channel_mention):
        if not channel_mention.startswith("<#") or not channel_mention.endswith(">"):
            return None

        channel_id = int(channel_mention[2:-1])
        return ctx.guild.get_channel(channel_id)

    @commands.guild_only()
    @commands.command()
    @commands.has_permissions(administrator=True)
    async def spam(self, ctx, channel_mention: str, *, args: str):
        """Spam a message in a channel a specified number of times."""
        try:
            amount, message = args.split(maxsplit=1)
            amount = int(amount)
        except ValueError:
            await ctx.send("Please provide the command in the format: `spam #channel message amount`")
            return

        target_channel = await self.parse_channel_mention(ctx, channel_mention)
        if not target_channel:
            await ctx.send("Invalid channel mention.")
            return

        if amount > 10:
            await ctx.send("Please limit the amount of spam to 10 or fewer for safety reasons.")
            return

        for _ in range(amount):
            await target_channel.send(message)

def setup(bot):
    bot.add_cog(Spamatron(bot))
