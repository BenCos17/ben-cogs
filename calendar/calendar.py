from redbot.core import commands

class Calendar(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def show_calendar(self, ctx):
        await ctx.send("Here is the calendar for you!")

def setup(bot):
    bot.add_cog(Calendar(bot))


