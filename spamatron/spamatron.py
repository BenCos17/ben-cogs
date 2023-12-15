from redbot.core import commands
import discord

class SpamPing(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def spamping(self, ctx, user: discord.User, times: int = 5):
        """Spam pings a user a specified number of times."""
        if times > 10:
            await ctx.send("Please limit the number of pings to 10 or fewer for spamming.")
            return

        for i in range(times):
            await ctx.send(f"{user.mention}")

def setup(bot):
    bot.add_cog(SpamPing(bot))
