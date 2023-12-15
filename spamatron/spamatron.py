from redbot.core import commands
import discord

class Spamatron(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.guild_only()
    @commands.command()
    @commands.has_permissions(administrator=True)
    async def spam(self, ctx, channel: discord.TextChannel, *, args):
        """Spam a message in a channel a specified number of times."""
        try:
            channel_mention, message, amount = args.split(maxsplit=2)
            amount = int(amount)
        except ValueError:
            await ctx.send("Please provide the command in the format: `spam #channel message amount`")
            return

        target_channel = discord.utils.get(ctx.guild.channels, mention=channel_mention)
        if not target_channel:
            await ctx.send("Invalid channel mention.")
            return

        if amount > 10:
            await ctx.send("Please limit the amount of spam to 10 or fewer for safety reasons.")
            return

        for _ in range(amount):
            await target_channel.send(message)

def setup(bot):
    bot.add_cog(Spam(bot))
