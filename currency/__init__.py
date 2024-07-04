from .currency import Currency

async def setup(bot):
    await bot.add_cog(Currency(bot))
