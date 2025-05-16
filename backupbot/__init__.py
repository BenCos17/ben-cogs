from redbot.core.bot import Red
from .backupbot import BackupBot

async def setup(bot: Red):
    await bot.add_cog(BackupBot(bot))
