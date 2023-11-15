import discord
from redbot.core import commands
from redbot.core.bot import Red
from discord.ext import menus

class EmojiListMenu(menus.ListPageSource):
    def __init__(self, data):
        super().__init__(data, per_page=10)

    async def format_page(self, menu, entries):
        offset = menu.current_page * self.per_page
        embed = discord.Embed(
            title=f"Custom Emojis - Page {menu.current_page + 1}/{self.get_max_pages()}",
            description="\n".join(entries)
        )
        embed.set_footer(text=f"Total Emojis: {len(self.entries)} | Use reactions to navigate.")
        return embed

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
        try:
            # Check if the provided emoji is a custom emoji
            if not emoji.is_custom_emoji():
                raise commands.BadArgument("Please provide a custom Discord emoji.")

            # Construct the emoji link
            emoji_url = f"https://cdn.discordapp.com/emojis/{emoji.id}.{emoji.animated and 'gif' or 'png'}"
            
            # Send the emoji link
            await ctx.send(f"Emoji link: {emoji_url}")
        except commands.BadArgument as e:
            await ctx.send(str(e))

    @commands.command()
    async def listemojis(self, ctx: commands.Context):
        """
        List all custom emojis in the server along with their names and links.
        """
        emojis = [f"{emoji.name}: [Link]({emoji.url})" for emoji in ctx.guild.emojis]
        if emojis:
            emoji_menu = menus.MenuPages(source=EmojiListMenu(emojis), delete_message_after=True)
            await emoji_menu.start(ctx)
        else:
            await ctx.send("No custom emojis found in this server.")

    @commands.command()
    async def emojiinfo(self, ctx: commands.Context, emoji: discord.PartialEmoji):
        """
        Get information about a specific custom emoji, including its name, ID, and creation date.

        Parameters:
        - emoji: The Discord emoji.
        """
        try:
            if not emoji.is_custom_emoji():
                raise commands.BadArgument("Please provide a custom Discord emoji.")

            emoji_info = f"Name: {emoji.name}\nID: {emoji.id}\nCreation Date: {emoji.created_at}"
            await ctx.send(emoji_info)
        except commands.BadArgument as e:
            await ctx.send(str(e))

    @commands.command()
    async def randomemoji(self, ctx: commands.Context):
        """
        Get a link for a random custom emoji in the server.
        """
        emojis = ctx.guild.emojis
        if emojis:
            random_emoji = self.bot.utils().random.choice(emojis)
            emoji_url = f"https://cdn.discordapp.com/emojis/{random_emoji.id}.{random_emoji.animated and 'gif' or 'png'}"
            await ctx.send(f"Random Emoji link: {emoji_url}")
        else:
            await ctx.send("No custom emojis found in this server.")

    @commands.command()
    async def emojisearch(self, ctx: commands.Context, keyword: str):
        """
        Search for custom emojis based on their names or keywords.

        Parameters:
        - keyword: The search keyword.
        """
        matching_emojis = [f"{emoji.name}: [Link]({emoji.url})" for emoji in ctx.guild.emojis if keyword.lower() in emoji.name.lower()]
        if matching_emojis:
            await ctx.send("\n".join(matching_emojis))
        else:
            await ctx.send(f"No custom emojis found matching the keyword '{keyword}'.")

def setup(bot: Red):
    bot.add_cog(EmojiLink(bot))
