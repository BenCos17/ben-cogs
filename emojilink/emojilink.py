import discord
from redbot.core import commands
from redbot.core.bot import Red
import random
import typing
import aiohttp

class EmojiLink(commands.Cog):
    def __init__(self, bot: Red):
        self.bot = bot

    @commands.group(name="emojilink", invoke_without_command=True)
    async def emojilink(self, ctx: commands.Context):
        """Emoji related commands."""
        await ctx.send_help(str(ctx.command))

    @emojilink.command(name="getlink")
    async def get_emoji_link(self, ctx: commands.Context, emoji: typing.Union[discord.PartialEmoji, str]):
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

    @emojilink.command(name="list")
    async def list_emojis(self, ctx: commands.Context):
        """
        List all custom emojis in the server along with their names and links.
        """
        if not ctx.guild.emojis:
            await ctx.send("No custom emojis found in this server.")
            return

        emojis = [f"{emoji}: [Link](https://cdn.discordapp.com/emojis/{emoji.id}.{emoji.animated and 'gif' or 'png'})" for emoji in ctx.guild.emojis]
        # Check if the message length exceeds Discord's limit and split the message if necessary
        if len("\n".join(emojis)) > 2000:
            for chunk in [emojis[i:i+10] for i in range(0, len(emojis), 10)]:  # Splitting the list into chunks
                await ctx.send("\n".join(chunk))
        else:
            await ctx.send("\n".join(emojis))

    @emojilink.command(name="info")
    async def emoji_info(self, ctx: commands.Context, emoji: typing.Union[discord.PartialEmoji, str]):
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

    @emojilink.command(name="random")
    async def random_emoji(self, ctx: commands.Context):
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

    @emojilink.command(name="search")
    async def emoji_search(self, ctx: commands.Context, keyword: str):
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

    @emojilink.command(name="add", require_var_positional=True)
    @commands.has_permissions(manage_emojis=True)
    async def add_emoji(self, ctx: commands.Context, name: str, url: str):
        """
        Add a custom emoji to the server from a given URL.

        Parameters:
        - name: The name for the new emoji.
        - url: The URL of the image to use for the emoji.
        """
        try:
            async with ctx.typing():
                async with aiohttp.ClientSession() as session:
                    async with session.get(url) as response:
                        if response.status != 200:
                            return await ctx.send("Failed to fetch image from URL.")
                        image_data = await response.read()
                        await ctx.guild.create_custom_emoji(name=name, image=image_data)
                        await ctx.send(f"Emoji '{name}' added successfully.")
        except discord.HTTPException as e:
            await ctx.send(f"Failed to add emoji: {e.text}")
        except discord.Forbidden:
            await ctx.send("I do not have permissions to add emojis.")
        except Exception as e:
            await ctx.send(f"An unexpected error occurred: {e}")

    @emojilink.command(name="copy", require_var_positional=True)
    @commands.has_permissions(manage_emojis=True)
    async def copy_emoji(self, ctx: commands.Context, emoji: discord.PartialEmoji):
        """
        Copy a custom emoji from one server to another.

        Parameters:
        - emoji: The custom emoji to copy.
        """
        # Check if the user has permission to manage emojis
        if not ctx.author.guild_permissions.manage_emojis:
            return await ctx.send("You do not have permission to manage emojis.")

        if not ctx.guild.me.guild_permissions.manage_emojis:
            return await ctx.send("I do not have permissions to manage emojis in this server.")

        try:
            async with ctx.typing():
                emoji_url = f"https://cdn.discordapp.com/emojis/{emoji.id}.{emoji.animated and 'gif' or 'png'}"
                async with aiohttp.ClientSession() as session:
                    async with session.get(emoji_url) as response:
                        if response.status != 200:
                            return await ctx.send("Failed to fetch emoji image.")
                        image_data = await response.read()
                        await ctx.guild.create_custom_emoji(name=emoji.name, image=image_data)
                        await ctx.send(f"Emoji '{emoji.name}' copied successfully.")
        except discord.HTTPException as e:
            await ctx.send(f"Failed to copy emoji: {e.text}")
        except discord.Forbidden:
            await ctx.send("I do not have permissions to add emojis.")
        except Exception as e:
            await ctx.send(f"An unexpected error occurred: {e}")