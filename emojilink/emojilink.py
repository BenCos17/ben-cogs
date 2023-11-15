import discord
from redbot.core import commands
from redbot.core.bot import Red
import random
import typing

class EmojiLink(commands.Cog):
    def __init__(self, bot: Red):
        self.bot = bot

    @commands.command()
    async def getemojilink(self, ctx: commands.Context, emoji: typing.Union[discord.PartialEmoji, str]):
        """
        Get the link for a Discord emoji.

        Parameters:
        - emoji: The Discord emoji (custom emoji or Unicode emoji).
        """
        # Determine if the provided emoji is a custom emoji or a Unicode emoji
        if isinstance(emoji, discord.PartialEmoji):
            emoji_str = str(emoji)
            emoji_url = f"https://cdn.discordapp.com/emojis/{emoji.id}.{emoji.animated and 'gif' or 'png'}"
        elif isinstance(emoji, str):
            emoji_str = emoji
            emoji_url = f"https://cdn.discordapp.com/emojis/{emoji}.png"
        else:
            raise commands.BadArgument("Invalid emoji provided.")

        # Send the emoji and the emoji link
        await ctx.send(f"Emoji: {emoji_str}\nEmoji link: {emoji_url}")

    @commands.command()
    async def listemojis(self, ctx: commands.Context):
        """
        List all custom emojis in the server along with their names and links.
        """
        emojis = [f"{emoji}: [Link]({emoji_url})" for emoji, emoji_url in self.get_all_emojis(ctx.guild.emojis)]
        if emojis:
            await ctx.send("\n".join(emojis))
        else:
            await ctx.send("No custom emojis found in this server.")

    @commands.command()
    async def emojiinfo(self, ctx: commands.Context, emoji: typing.Union[discord.PartialEmoji, str]):
        """
        Get information about a specific custom emoji, including its name, ID, and creation date.

        Parameters:
        - emoji: The Discord emoji (custom emoji or Unicode emoji).
        """
        # Determine if the provided emoji is a custom emoji or a Unicode emoji
        if isinstance(emoji, discord.PartialEmoji):
            emoji_str = str(emoji)
            emoji_url = f"https://cdn.discordapp.com/emojis/{emoji.id}.{emoji.animated and 'gif' or 'png'}"
            emoji_name = emoji.name
            emoji_id = emoji.id
            emoji_created_at = emoji.created_at
        elif isinstance(emoji, str):
            emoji_str = emoji
            emoji_url = f"https://cdn.discordapp.com/emojis/{emoji}.png"
            emoji_name = None  # Unicode emojis don't have a name
            emoji_id = None  # Unicode emojis don't have an ID
            emoji_created_at = None  # Unicode emojis don't have a creation date
        else:
            raise commands.BadArgument("Invalid emoji provided.")

        if emoji_name is not None:
            emoji_info = f"Emoji: {emoji_str}\nName: {emoji_name}\nID: {emoji_id}\nCreation Date: {emoji_created_at}\nEmoji link: {emoji_url}"
        else:
            emoji_info = f"Emoji: {emoji_str}\nEmoji link: {emoji_url}"

        await ctx.send(emoji_info)

    @commands.command()
    async def randomemoji(self, ctx: commands.Context):
        """
        Get a link for a random custom emoji in the server.
        """
        emojis = ctx.guild.emojis
        if emojis:
            random_emoji = random.choice(emojis)
            emoji_url = f"https://cdn.discordapp.com/emojis/{random_emoji.id}.{random_emoji.animated and 'gif' or 'png'}"
            # Send the emoji and the emoji link
            await ctx.send(f"Random Emoji: {random_emoji}\nEmoji link: {emoji_url}")
        else:
            await ctx.send("No custom emojis found in this server.")

    @commands.command()
    async def emojisearch(self, ctx: commands.Context, keyword: str):
        """
        Search for custom emojis based on their names or keywords.

        Parameters:
        - keyword: The search keyword.
        """
        matching_emojis = [f"{emoji}: [Link]({emoji_url})" for emoji, emoji_url in self.get_all_emojis(ctx.guild.emojis) if keyword.lower() in emoji.lower()]
        if matching_emojis:
            await ctx.send("\n".join(matching_emojis))
        else:
            await ctx.send(f"No custom emojis found matching the keyword '{keyword}'.")

    def get_all_emojis(self, emojis):
        """
        Helper function to extract all emojis and their URLs from a list of emojis.
        """
        all_emojis = []
        for emoji in emojis:
            if isinstance(emoji, discord.PartialEmoji):
                emoji_url = f"https://cdn.discordapp.com/emojis/{emoji.id}.{emoji.animated and 'gif' or 'png'}"
            elif isinstance(emoji, str):
                emoji_url = f"https://cdn.discordapp.com/emojis/{emoji}.png"
            else:
                continue
            all_emojis.append((str(emoji), emoji_url))
        return all_emojis

def setup(bot: Red):
    bot.add_cog(EmojiLink(bot))
