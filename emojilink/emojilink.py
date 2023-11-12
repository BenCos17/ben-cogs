import discord
from redbot.core import commands
from redbot.core.bot import Red

class EmojiLink(commands.Cog):
    def __init__(self, bot: Red):
        self.bot = bot

    @commands.command()
    async def getemojilink(self, ctx: commands.Context, emoji: discord.PartialEmoji):
        """
        Get the link for a Discord emoji.

        Parameters:
        - emoji: The Discord emoji.
        """
        # Check if the provided emoji is a custom emoji
        if not emoji.is_custom_emoji():
            return await ctx.send("Please provide a custom Discord emoji.")

        # Construct the emoji link
        emoji_url = f"https://cdn.discordapp.com/emojis/{emoji.id}.{emoji.animated and 'gif' or 'png'}"
        
        # Send the emoji link
        await ctx.send(f"Emoji link: {emoji_url}")

def setup(bot: Red):
    bot.add_cog(EmojiLink(bot))
