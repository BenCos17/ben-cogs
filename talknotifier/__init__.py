from redbot.core.bot import Red

from .talknotifier import TalkNotifier

async def setup(bot: Red):
    await bot.add_cog(TalkNotifier(bot))