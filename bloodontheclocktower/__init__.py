from .bloodontheclocktower import BloodOnTheClocktower


async def setup(bot):
    await bot.add_cog(BloodOnTheClocktower(bot))
