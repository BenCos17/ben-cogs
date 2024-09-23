from .clowndan import Clowndan

async def setup(bot):
    cog = Clowndan(bot)
    bot.add_cog(cog)
