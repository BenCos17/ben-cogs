from redbot.core.bot import Red

from .contact import Contact

__red_end_user_data_statement__ = (
    "This cog stores Discord user IDs and conversation messages for support conversations."
)


async def setup(bot: Red):
    await bot.add_cog(Contact(bot))