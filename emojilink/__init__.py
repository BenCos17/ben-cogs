

from redbot.core.bot import Red

from .emojilink import EmojiLink

async def setup(bot: Red):
    await bot.add_cog(EmojiLink(bot))