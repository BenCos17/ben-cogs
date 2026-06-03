from .airframes import Airframes


async def setup(bot):
    """Async package entrypoint for the Airframes cog."""
    await bot.add_cog(Airframes(bot))
