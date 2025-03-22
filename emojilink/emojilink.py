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

    @emojilink.command(name="list", aliases=["all"])
    async def list_emojis(self, ctx: commands.Context):
        """List all custom emojis in the server along with their names and links."""
        if not ctx.guild.emojis:
            await ctx.send("No custom emojis found in this server.")
            return

        # Create embed pages with 5 emojis per page (reduced from 10 to show larger images)
        emojis = ctx.guild.emojis
        pages = []
        for i in range(0, len(emojis), 5):
            embed = discord.Embed(title="Server Emojis", color=discord.Color.blue())
            chunk = emojis[i:i + 5]
            for emoji in chunk:
                emoji_url = f"https://cdn.discordapp.com/emojis/{emoji.id}.{emoji.animated and 'gif' or 'png'}"
                embed.add_field(
                    name=f":{emoji.name}:",
                    value=f"{emoji} [Download]({emoji_url})",
                    inline=False
                )
                # Add the emoji as a thumbnail in the embed
                if len(chunk) == 1:  # If only one emoji, use a large thumbnail
                    embed.set_thumbnail(url=emoji_url)
                else:  # If multiple emojis, add the image directly
                    embed.add_field(name="‎", value=f"[⠀]({emoji_url})", inline=False)  # Zero-width space for name

            embed.set_footer(text=f"Page {i//5 + 1}/{-(-len(emojis)//5)} • Total emojis: {len(emojis)}")
            pages.append(embed)

        if not pages:
            return await ctx.send("No emojis to display.")

        # Create custom view with buttons
        class PaginationView(discord.ui.View):
            def __init__(self):
                super().__init__(timeout=60)
                self.current_page = 0

            @discord.ui.button(label="◀️ Previous", style=discord.ButtonStyle.secondary, disabled=True)
            async def previous_button(self, interaction: discord.Interaction, button: discord.ui.Button):
                if interaction.user != ctx.author:
                    return await interaction.response.send_message("You cannot use these buttons.", ephemeral=True)
                
                self.current_page -= 1
                # Update button states
                button.disabled = self.current_page == 0
                self.children[1].disabled = self.current_page == len(pages) - 1  # Next button
                
                await interaction.response.edit_message(embed=pages[self.current_page], view=self)

            @discord.ui.button(label="Next ▶️", style=discord.ButtonStyle.secondary)
            async def next_button(self, interaction: discord.Interaction, button: discord.ui.Button):
                if interaction.user != ctx.author:
                    return await interaction.response.send_message("You cannot use these buttons.", ephemeral=True)
                
                self.current_page += 1
                # Update button states
                self.children[0].disabled = self.current_page == 0  # Previous button
                button.disabled = self.current_page == len(pages) - 1
                
                await interaction.response.edit_message(embed=pages[self.current_page], view=self)

            async def on_timeout(self):
                # Disable all buttons when the view times out
                for item in self.children:
                    item.disabled = True
                # Try to update the message with disabled buttons
                try:
                    await self.message.edit(view=self)
                except:
                    pass

        # Send the initial message with the view
        view = PaginationView()
        view.message = await ctx.send(embed=pages[0], view=view)

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
        matching_emojis = [
            f"{emoji}: [Link]({emoji_url})" 
            for emoji, emoji_url in self.get_all_emojis(ctx.guild.emojis) 
            if keyword.lower() in emoji.name.lower()  # Compare against emoji name
        ]
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

    @emojilink.command(name="add", aliases=["create"])
    @commands.has_permissions(manage_emojis=True)
    async def add_emoji(self, ctx: commands.Context, name: str, url: str = None):
        """Add a custom emoji to the server from a URL or attachment."""
        # Validate emoji name
        if not name.isalnum() and not '_' in name:
            return await ctx.send("Emoji name must contain only letters, numbers, and underscores.")
        
        if len(name) < 2 or len(name) > 32:
            return await ctx.send("Emoji name must be between 2 and 32 characters long.")

        # Check for attachment if no URL is provided
        if not url and not ctx.message.attachments:
            return await ctx.send("Please provide either a URL or attach an image file.")
        
        try:
            async with ctx.typing():
                async with aiohttp.ClientSession() as session:
                    # Use attachment URL if no URL is provided
                    if not url and ctx.message.attachments:
                        url = ctx.message.attachments[0].url
                    
                    async with session.get(url) as response:
                        if response.status != 200:
                            return await ctx.send("Failed to fetch image.")
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

    @emojilink.command(name="delete", require_var_positional=True)
    @commands.has_permissions(manage_emojis=True)
    async def delete_emoji(self, ctx: commands.Context, emoji: discord.PartialEmoji):
        """
        Delete a custom emoji from the server.

        Parameters:
        - emoji: The custom emoji to delete.
        """
        try:
            # Find the emoji in the guild's emoji list
            guild_emoji = discord.utils.get(ctx.guild.emojis, id=emoji.id)
            if guild_emoji is None:
                return await ctx.send("This emoji doesn't exist in this server.")
            
            # Create confirmation view
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
            
            # Send confirmation message
            await ctx.send(
                f"Are you sure you want to delete the emoji {emoji}?",
                view=view
            )
            
        except Exception as e:
            await ctx.send(f"An unexpected error occurred: {e}")

    @emojilink.command(name="rename", aliases=["edit"])
    @commands.has_permissions(manage_emojis=True)
    async def rename_emoji(self, ctx: commands.Context, emoji: discord.PartialEmoji, new_name: str):
        """Rename a custom emoji in the server."""
        # Validate new name
        if not new_name.isalnum() and not '_' in new_name:
            return await ctx.send("Emoji name must contain only letters, numbers, and underscores.")
        
        if len(new_name) < 2 or len(new_name) > 32:
            return await ctx.send("Emoji name must be between 2 and 32 characters long.")

        # Find the emoji in the guild's emoji list
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