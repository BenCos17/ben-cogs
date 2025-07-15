from .loan import BankLoan

async def setup(bot):
    await bot.add_cog(BankLoan(bot))


