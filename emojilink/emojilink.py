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
            # Generate a link using Emojipedia (replace '+' with the Unicode emoji)
            emoji_url = f"https://emojipedia.org/{'+'.join(emoji.encode('unicode-escape').decode('utf-8').split())}/"
        else:
            raise commands.BadArgument("Invalid emoji provided.")

        # Send the emoji and the emoji link
        await ctx.send(f"Emoji: {emoji_str}")
        await ctx.send(f"Emoji link: {emoji_url}")

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
            emoji_url = None  # Unicode emojis don't have a direct image link
            emoji_name = None  # Unicode emojis don't have a name
            emoji_id = None  # Unicode emojis don't have an ID
            emoji_created_at = None  # Unicode emojis don't have a creation date
        else:
            raise commands.BadArgument("Invalid emoji provided.")

        if emoji_name is not None:
            await ctx.send(f"Emoji: {emoji_str}\nName: {emoji_name}\nID: {emoji_id}\nCreation Date: {emoji_created_at}")
        else:
            await ctx.send(f"Emoji: {emoji_str}")

        if emoji_url:
            await ctx.send(f"Emoji link: {emoji_url}")

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
            await ctx.send(f"Random Emoji: {random_emoji}")
            await ctx.send(f"Emoji link: {emoji_url}")
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
                all_emojis.append((str(emoji), emoji_url))
            elif isinstance(emoji, str):
                # Unicode emojis don't have a direct image link
                all_emojis.append((emoji, None))
        return all_emojis

        @commands.command()
        @commands.has_permissions(manage_emojis=True)
        async def addemoji(self, ctx: commands.Context, name: str, url: str):
            """
            Adds a custom emoji to the server from a specified URL.

            Parameters:
            - name: The desired name for the new emoji.
            - url: The direct URL of the image to be used as the emoji.
            """
            try:
                async with ctx.typing():
                    async with aiohttp.ClientSession() as session:
                        async with session.get(url) as response:
                            if response.status == 200:
                                image_bytes = await response.read()
                                created_emoji = await ctx.guild.create_custom_emoji(name=name, image=image_bytes)
                                await ctx.send(f"Emoji '{name}' added successfully. {created_emoji}")
                            else:
                                await ctx.send("Could not retrieve the image from the provided URL.")
            except discord.HTTPException as e:
                await ctx.send(f"An error occurred while adding the emoji: {e}")
            except aiohttp.ClientError as e:
                await ctx.send(f"An error occurred while fetching the image: {e}")
