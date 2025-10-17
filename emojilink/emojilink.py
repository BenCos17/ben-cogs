import discord
from redbot.core import commands
from redbot.core.bot import Red
import random
import typing
import aiohttp
from PIL import Image
import io

class EmojiLink(commands.Cog):
    """Emoji management commands with automatic background removal."""

    def __init__(self, bot: Red):
        self.bot = bot

    @commands.group(name="emojilink", invoke_without_command=True)
    async def emojilink(self, ctx: commands.Context):
        """Emoji related commands."""
        await ctx.send_help(str(ctx.command))

    # -----------------------------
    # Subcommands
    # -----------------------------

    @commands.command(name="getlink")
    async def get_emoji_link(self, ctx: commands.Context, emoji: typing.Union[discord.PartialEmoji, str]):
        """Get the link for a Discord emoji."""
        if isinstance(emoji, discord.PartialEmoji):
            emoji_str = str(emoji)
            emoji_url = f"https://cdn.discordapp.com/emojis/{emoji.id}.{ 'gif' if emoji.animated else 'png'}"
        elif isinstance(emoji, str):
            emoji_str = emoji
            emoji_url = f"https://emojipedia.org/{'+'.join(emoji.encode('unicode-escape').decode('utf-8').split())}/"
        else:
            raise commands.BadArgument("Invalid emoji provided.")
        await ctx.send(f"Emoji: {emoji_str}")
        await ctx.send(f"Emoji link: {emoji_url}")
    emojilink.add_command(get_emoji_link)

    @commands.command(name="list", aliases=["all"])
    async def list_emojis(self, ctx: commands.Context):
        """List all custom emojis in the server with names and links."""
        if not ctx.guild.emojis:
            await ctx.send("No custom emojis found in this server.")
            return

        emojis = ctx.guild.emojis
        pages = []
        for i in range(0, len(emojis), 3):
            embed = discord.Embed(title="Server Emojis", color=discord.Color.blue())
            chunk = emojis[i:i + 3]
            for emoji in chunk:
                emoji_url = f"https://cdn.discordapp.com/emojis/{emoji.id}.{ 'gif' if emoji.animated else 'png'}"
                embed.add_field(
                    name=f":{emoji.name}:",
                    value=f"[⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀]({emoji_url})\n{emoji} • [Download]({emoji_url})",
                    inline=True
                )
            remaining = 3 - len(chunk)
            for _ in range(remaining):
                embed.add_field(name="⠀", value="⠀", inline=True)
            embed.set_footer(text=f"Page {i//3 + 1}/{-(-len(emojis)//3)} • Total emojis: {len(emojis)}")
            pages.append(embed)

        if not pages:
            return await ctx.send("No emojis to display.")

        class PaginationView(discord.ui.View):
            def __init__(self):
                super().__init__(timeout=60)
                self.current_page = 0

            @discord.ui.button(label="◀️ Previous", style=discord.ButtonStyle.secondary, disabled=True)
            async def previous_button(self, interaction: discord.Interaction, button: discord.ui.Button):
                if interaction.user != ctx.author:
                    return await interaction.response.send_message("You cannot use these buttons.", ephemeral=True)
                self.current_page -= 1
                button.disabled = self.current_page == 0
                self.children[1].disabled = self.current_page == len(pages) - 1
                await interaction.response.edit_message(embed=pages[self.current_page], view=self)

            @discord.ui.button(label="Next ▶️", style=discord.ButtonStyle.secondary)
            async def next_button(self, interaction: discord.Interaction, button: discord.ui.Button):
                if interaction.user != ctx.author:
                    return await interaction.response.send_message("You cannot use these buttons.", ephemeral=True)
                self.current_page += 1
                self.children[0].disabled = self.current_page == 0
                button.disabled = self.current_page == len(pages) - 1
                await interaction.response.edit_message(embed=pages[self.current_page], view=self)

            async def on_timeout(self):
                for item in self.children:
                    item.disabled = True
                try:
                    await self.message.edit(view=self)
                except:
                    pass

        view = PaginationView()
        view.message = await ctx.send(embed=pages[0], view=view)
    emojilink.add_command(list_emojis)

    @commands.command(name="info")
    async def emoji_info(self, ctx: commands.Context, emoji: typing.Union[discord.PartialEmoji, str]):
        """Get information about a specific emoji."""
        if isinstance(emoji, discord.PartialEmoji):
            emoji_str = str(emoji)
            emoji_url = f"https://cdn.discordapp.com/emojis/{emoji.id}.{ 'gif' if emoji.animated else 'png'}"
            emoji_name = emoji.name
            emoji_id = emoji.id
            emoji_created_at = emoji.created_at
        elif isinstance(emoji, str):
            emoji_str = emoji
            emoji_url = None
            emoji_name = None
            emoji_id = None
            emoji_created_at = None
        else:
            raise commands.BadArgument("Invalid emoji provided.")

        if emoji_name:
            await ctx.send(f"Emoji: {emoji_str}\nName: {emoji_name}\nID: {emoji_id}\nCreation Date: {emoji_created_at}")
        else:
            await ctx.send(f"Emoji: {emoji_str}")

        if emoji_url:
            await ctx.send(f"Emoji link: {emoji_url}")
    emojilink.add_command(emoji_info)

    @commands.command(name="random")
    async def random_emoji(self, ctx: commands.Context):
        """Get a random custom emoji."""
        emojis = ctx.guild.emojis
        if emojis:
            random_emoji = random.choice(emojis)
            emoji_url = f"https://cdn.discordapp.com/emojis/{random_emoji.id}.{ 'gif' if random_emoji.animated else 'png'}"
            await ctx.send(f"Random Emoji: {random_emoji}")
            await ctx.send(f"Emoji link: {emoji_url}")
        else:
            await ctx.send("No custom emojis found in this server.")
    emojilink.add_command(random_emoji)

    @commands.command(name="search")
    async def emoji_search(self, ctx: commands.Context, keyword: str):
        """Search custom emojis by name."""
        matching_emojis = [
            f"{emoji}: [Link]({emoji_url})"
            for emoji, emoji_url in self.get_all_emojis(ctx.guild.emojis)
            if hasattr(emoji, "name") and keyword.lower() in emoji.name.lower()
        ]
        if matching_emojis:
            await ctx.send("\n".join(matching_emojis))
        else:
            await ctx.send(f"No custom emojis found matching '{keyword}'.")
    emojilink.add_command(emoji_search)

    # -----------------------------
    # Helpers
    # -----------------------------

    def get_all_emojis(self, emojis):
        all_emojis = []
        for emoji in emojis:
            if isinstance(emoji, discord.PartialEmoji):
                emoji_url = f"https://cdn.discordapp.com/emojis/{emoji.id}.{ 'gif' if emoji.animated else 'png'}"
                all_emojis.append((emoji, emoji_url))
            elif isinstance(emoji, str):
                all_emojis.append((emoji, None))
        return all_emojis

    # -----------------------------
    # Add / Copy / Delete / Rename
    # -----------------------------

    @commands.command(name="add", aliases=["create"])
    @commands.has_permissions(manage_emojis=True)
    async def add_emoji(self, ctx: commands.Context, name: str, source: typing.Union[discord.PartialEmoji, str] = None):
        """Add a custom emoji with automatic background removal."""
        if not name.isalnum() and "_" not in name:
            return await ctx.send("Emoji name must contain only letters, numbers, and underscores.")
        if len(name) < 2 or len(name) > 32:
            return await ctx.send("Emoji name must be between 2 and 32 characters long.")
        if not source and not ctx.message.attachments:
            return await ctx.send("Provide an existing emoji, URL, or attach an image file.")

        try:
            async with ctx.typing():
                async with aiohttp.ClientSession() as session:
                    if isinstance(source, discord.PartialEmoji):
                        url = f"https://cdn.discordapp.com/emojis/{source.id}.{ 'gif' if source.animated else 'png'}"
                    elif isinstance(source, str) and source.startswith(('http://', 'https://')):
                        url = source
                    elif ctx.message.attachments:
                        url = ctx.message.attachments[0].url
                    else:
                        return await ctx.send("Invalid source.")

                    async with session.get(url) as response:
                        if response.status != 200:
                            return await ctx.send("Failed to fetch image.")
                        image_data = await response.read()

                    # === Background removal ===
                    image = Image.open(io.BytesIO(image_data)).convert("RGBA")
                    datas = image.getdata()
                    new_data = []
                    for item in datas:
                        if item[0] > 240 and item[1] > 240 and item[2] > 240:
                            new_data.append((255, 255, 255, 0))
                        else:
                            new_data.append(item)
                    image.putdata(new_data)
                    buffered = io.BytesIO()
                    image.save(buffered, format="PNG")
                    buffered.seek(0)
                    image_data = buffered.read()
                    # === End background removal ===

                    await ctx.guild.create_custom_emoji(name=name, image=image_data)
                    await ctx.send(f"Emoji '{name}' added successfully.")
        except discord.HTTPException as e:
            await ctx.send(f"Failed to add emoji: {e.text}")
        except discord.Forbidden:
            await ctx.send("I do not have permissions to add emojis.")
        except Exception as e:
            await ctx.send(f"An unexpected error occurred: {e}")
    emojilink.add_command(add_emoji)

    @commands.command(name="copy")
    @commands.has_permissions(manage_emojis=True)
    async def copy_emoji(self, ctx: commands.Context, emoji: discord.PartialEmoji):
        """Copy a custom emoji with automatic background removal."""
        if not ctx.author.guild_permissions.manage_emojis:
            return await ctx.send("You do not have permission to manage emojis.")
        if not ctx.guild.me.guild_permissions.manage_emojis:
            return await ctx.send("I do not have permissions to manage emojis in this server.")

        try:
            async with ctx.typing():
                emoji_url = f"https://cdn.discordapp.com/emojis/{emoji.id}.{ 'gif' if emoji.animated else 'png'}"
                async with aiohttp.ClientSession() as session:
                    async with session.get(emoji_url) as response:
                        if response.status != 200:
                            return await ctx.send("Failed to fetch emoji image.")
                        image_data = await response.read()

                # === Background removal ===
                image = Image.open(io.BytesIO(image_data)).convert("RGBA")
                datas = image.getdata()
                new_data = []
                for item in datas:
                    if item[0] > 240 and item[1] > 240 and item[2] > 240:
                        new_data.append((255, 255, 255, 0))
                    else:
                        new_data.append(item)
                image.putdata(new_data)
                buffered = io.BytesIO()
                image.save(buffered, format="PNG")
                buffered.seek(0)
                image_data = buffered.read()
                # === End background removal ===

                await ctx.guild.create_custom_emoji(name=emoji.name, image=image_data)
                await ctx.send(f"Emoji '{emoji.name}' copied successfully.")
        except discord.HTTPException as e:
            await ctx.send(f"Failed to copy emoji: {e.text}")
        except discord.Forbidden:
            await ctx.send("I do not have permissions to add emojis.")
        except Exception as e:
            await ctx.send(f"An unexpected error occurred: {e}")
    emojilink.add_command(copy_emoji)

    @commands.command(name="delete")
    @commands.has_permissions(manage_emojis=True)
    async def delete_emoji(self, ctx: commands.Context, emoji: discord.PartialEmoji):
        """Delete a custom emoji from the server."""
        try:
            guild_emoji = discord.utils.get(ctx.guild.emojis, id=emoji.id)
            if guild_emoji is None:
                return await ctx.send("This emoji doesn't exist in this server.")

            view = discord.ui.View(timeout=30)
            confirm_button = discord.ui.Button(label="Confirm", style=discord.ButtonStyle.danger)
            cancel_button = discord.ui.Button(label="Cancel", style=discord.ButtonStyle.secondary)

            async def confirm_callback(interaction: discord.Interaction):
                if interaction.user != ctx.author:
                    return await interaction.response.send_message("You cannot use this button.", ephemeral=True)
                try:
                    await guild_emoji.delete()
                    await interaction.response.edit_message(content=f"Emoji '{emoji.name}' deleted successfully.", view=None)
                except Exception as e:
                    await interaction.response.edit_message(content=f"Failed to delete emoji: {e}", view=None)

            async def cancel_callback(interaction: discord.Interaction):
                if interaction.user != ctx.author:
                    return await interaction.response.send_message("You cannot use this button.", ephemeral=True)
                await interaction.response.edit_message(content="Emoji deletion cancelled.", view=None)

            confirm_button.callback = confirm_callback
            cancel_button.callback = cancel_callback

            view.add_item(confirm_button)
            view.add_item(cancel_button)

            await ctx.send(f"Are you sure you want to delete the emoji {emoji}?", view=view)
        except Exception as e:
            await ctx.send(f"An unexpected error occurred: {e}")
    emojilink.add_command(delete_emoji)

    @commands.command(name="rename", aliases=["edit"])
    @commands.has_permissions(manage_emojis=True)
    async def rename_emoji(self, ctx: commands.Context, emoji: discord.PartialEmoji, new_name: str):
        """Rename a custom emoji in the server."""
        if not new_name.isalnum() and "_" not in new_name:
            return await ctx.send("Emoji name must contain only letters, numbers, and underscores.")
        if len(new_name) < 2 or len(new_name) > 32:
            return await ctx.send("Emoji name must be between 2 and 32 characters long.")

        guild_emoji = discord.utils.get(ctx.guild.emojis, id=emoji.id)
        if guild_emoji is None:
            return await ctx.send("This emoji doesn't exist in this server.")

        try:
            await guild_emoji.edit(name=new_name)
            await ctx.send(f"Emoji successfully renamed from `:{emoji.name}:` to `:{new_name}:`")
        except discord.HTTPException as e:
            await ctx.send(f"Failed to rename emoji: {e.text}")
        except discord.Forbidden:
            await ctx.send("I do not have permissions to rename emojis.")
        except Exception as e:
            await ctx.send(f"An unexpected error occurred: {e}")
    emojilink.add_command(rename_emoji)
