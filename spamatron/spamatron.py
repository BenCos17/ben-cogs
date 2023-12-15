from redbot.core import commands
import discord

class Spamatron(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.guild_only()
    @commands.command()
    @commands.has_permissions(administrator=True)
    async def spam(self, ctx, channel: discord.TextChannel, *, message: str, amount: int):
        """Spam a message in a channel a specified number of times."""
        if amount > 10:
            await ctx.send("Please limit the amount of spam to 10 or fewer for safety reasons.")
            return

        for _ in range(amount):
            await channel.send(message)

def setup(bot):
    bot.add_cog(Spam(bot))
