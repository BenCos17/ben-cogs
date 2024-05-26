from .amazon import Amazon

async def setup(bot):
    bot.add_cog(Amazon(bot))
