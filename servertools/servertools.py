import os
import discord
from redbot.core import commands, Config
import asyncio
import aiohttp
from io import BytesIO
from PIL import Image, ImageDraw, ImageFont

class Servertools(commands.Cog):
    """Cog providing various server management utilities, such as mod DMs, voice moves, and auto-reactions."""
    def __init__(self, bot):
        self.bot = bot
        self.config = Config.get_conf(self, identifier=492089091320446976)  # Initialize config with a unique identifier
        self.config.register_guild(auto_reactions=[])  # Initialize auto_reactions as an empty list
        self.config.register_user(online_notifications=[])  # Add this line to register online notifications

    @commands.command()
    @commands.has_permissions(manage_guild=True)
    async def moddm(self, ctx, user: discord.User, *, message):
        """Send a direct message to a user as a moderator, with confirmation prompt."""
        if ctx.guild:
            if ctx.guild.get_member(user.id):
                # Prompt for confirmation before sending dm
                confirm_embed = discord.Embed(title="Confirmation", description=f"Are you sure you want to send this message to {user.name}?", color=0x00ff00)
                await ctx.send(embed=confirm_embed)
                
                def check(m):
                    return m.author == ctx.author and m.channel == ctx.channel and m.content.lower() in ['yes', 'no', 'y', 'n']

                try:
                    response = await self.bot.wait_for('message', check=check, timeout=30.0)
                    if response.content.lower() in ['yes', 'y']:
                        try:
                            dm_embed = discord.Embed(title="Message from Server", description=message, color=0x00ff00)
                            dm_embed.set_footer(text=f"Sent from {ctx.guild.name}")
                            await user.send(embed=dm_embed)
                            embed = discord.Embed(title="Message Sent", description=f"Message sent to {user.name} from {ctx.guild.name}", color=0x00ff00)
                            await ctx.send(embed=embed)
                        except discord.Forbidden:
                            embed = discord.Embed(title="Error", description="I cannot send a message to this user.", color=0xff0000)
                            await ctx.send(embed=embed)
                    else:
                        await ctx.send("Message sending canceled.")
                except asyncio.TimeoutError:
                    await ctx.send("You took too long to reply with yes (y) or no (n). Message sending canceled.")
            else:
                embed = discord.Embed(title="Error", description="This user is not a member of this server.", color=0xff0000)
                await ctx.send(embed=embed)
        else:
            embed = discord.Embed(title="Error", description="This command can only be used in a server.", color=0xff0000)
            await ctx.send(embed=embed)


    @commands.command()
    @commands.has_permissions(move_members=True)
    async def voicemove(self, ctx, user: discord.Member, channel: discord.VoiceChannel):
        """Move a member to a specified voice channel."""
        if ctx.guild:
            if ctx.guild.get_member(user.id):
                try:
                    await user.move_to(channel)
                    await ctx.send(f"Moved {user.name} to {channel.name}.")
                except discord.Forbidden:
                    await ctx.send("I do not have permission to move members in voice channels.")
            else:
                await ctx.send("This user is not a member of this server.")
        else:
            await ctx.send("This command can only be used in a server.")



    @commands.command()
    @commands.has_permissions(manage_channels=True)
    async def ld(self, ctx, channel: discord.TextChannel, *, permissions: str):
        """Lock down a text channel for everyone by changing permissions."""
        if ctx.guild:
            try:
                await channel.set_permissions(ctx.guild.roles[0], send_messages=False)
                await ctx.send(f"Locked down {channel.name} for everyone.")
            except discord.Forbidden:
                await ctx.send("I do not have permission to change the permissions in this channel.")
        else:
            await ctx.send("This command can only be used in a server.")

    @commands.command()
    @commands.has_permissions(manage_messages=True)
    async def purge(self, ctx, amount: int):
        """Delete a specified number of messages in the current channel."""
        if ctx.channel:
            try:
                await ctx.channel.purge(limit=amount)
                await ctx.send(f"Deleted {amount} messages in this channel.")
            except discord.Forbidden:
                await ctx.send("I do not have permission to delete messages in this channel.")
        else:
            await ctx.send("This command can only be used in a channel.")



    @commands.command()
    @commands.has_permissions(view_audit_log=True)
    async def auditlog(self, ctx, amount: int):
        """Display the most recent audit log entries for the server."""
        if ctx.guild:
            try:
                async for log in ctx.guild.audit_logs(limit=amount):
                    action = log.action.name.replace("_", " ").title()
                    target_name = log.target.name if isinstance(log.target, discord.Member) else log.target.name if isinstance(log.target, discord.Role) else "an object"
                    user_name = log.user.name
                    timestamp = log.created_at.strftime("%Y-%m-%d %H:%M:%S")
                    await ctx.send(f"{target_name} was {action} by {user_name} at {timestamp}")
            except discord.Forbidden:
                await ctx.send("I do not have permission to view the audit log.")
        else:
            await ctx.send("This command can only be used in a server.")
            






    @commands.command(name='setservericon')
    @commands.guild_only()
    @commands.has_permissions(manage_guild=True)
    async def set_server_icon(self, ctx, url: str = None):
        """Set the server icon using a provided image URL or attachment."""
        if url is None and len(ctx.message.attachments) == 0:
            await ctx.send('Error: You must provide either an image URL or upload an image.')
            return

        if url is not None:
            async with aiohttp.ClientSession() as session:
                try:
                    async with session.get(url) as resp:
                        image_bytes = await resp.read()
                        content_type = resp.headers.get('content-type')
                        if content_type in ['image/png', 'image/webp']:
                            await ctx.guild.edit(icon=image_bytes)
                            await ctx.send('Server icon has been updated!')
                        else:
                            await ctx.send('Error: Unsupported image type given.')
                except Exception as e:
                    await ctx.send(f'Error: {str(e)}')

        if len(ctx.message.attachments) > 0:
            attachment = ctx.message.attachments[0]
            image_bytes = await attachment.read()
            image_name = attachment.filename
            if image_name.endswith('.png') or image_name.endswith('.webp'):
                await ctx.guild.edit(icon=image_bytes)
                await ctx.send('Server icon has been updated!')
            else:
                await ctx.send('Error: Unsupported image type given.')

    @commands.command(name='fakeping')
    @commands.guild_only()
    async def fake_ping(self, ctx):
        """Send a fake ping image resembling a Discord notification badge."""
        icon_url = ctx.guild.icon.url if ctx.guild.icon else None
        if icon_url is None:
            await ctx.send("Server icon is not set.")
            return
        async with aiohttp.ClientSession() as session:
            async with session.get(str(icon_url)) as resp:
                image_bytes = await resp.read()
                image = Image.open(BytesIO(image_bytes))
                image.thumbnail((64, 64))
                image = image.convert('RGBA')

                # Badge parameters
                badge_radius = 14
                badge_center = (image.width - badge_radius, image.height - badge_radius)
                badge_diameter = badge_radius * 2

                # Draw badge
                draw = ImageDraw.Draw(image)

                # Draw white border
                draw.ellipse([
                    badge_center[0] - badge_radius - 2, badge_center[1] - badge_radius - 2,
                    badge_center[0] + badge_radius + 2, badge_center[1] + badge_radius + 2
                ], fill=(255, 255, 255, 255))
                # Draw red circle
                draw.ellipse([
                    badge_center[0] - badge_radius, badge_center[1] - badge_radius,
                    badge_center[0] + badge_radius, badge_center[1] + badge_radius
                ], fill=(237, 66, 69, 255))

                # Draw the number '1' in the center of the badge
                try:
                    font = ImageFont.truetype("arial.ttf", 20)
                except Exception:
                    font = ImageFont.load_default()
                text = "1"
                text_width, text_height = draw.textsize(text, font=font)
                text_x = badge_center[0] - text_width // 2
                text_y = badge_center[1] - text_height // 2
                draw.text((text_x, text_y), text, font=font, fill=(255, 255, 255, 255))

                buffer = BytesIO()
                image.save(buffer, format='PNG')
                buffer.seek(0)
                file = discord.File(buffer, filename='fake_ping.png')
                await ctx.send(file=file)

    @commands.group()
    async def autoreact(self, ctx):
        """Manage automatic reactions for users and channels."""
        if ctx.invoked_subcommand is None:
            await ctx.send("Use subcommands: add, remove, list")

    @autoreact.command(name="add")
    async def add_autoreact(self, ctx, user: discord.Member, channel: discord.TextChannel, emoji: str):
        """Add an auto-reaction for a user in a specific channel"""
        async with self.config.guild(ctx.guild).auto_reactions() as reactions:
            reactions[f"{channel.id}-{user.id}"] = emoji
        await ctx.send(f"Added auto-reaction with {emoji} for {user.display_name} in {channel.mention}")

    @autoreact.command(name="remove")
    async def remove_autoreact(self, ctx, user: discord.Member, channel: discord.TextChannel):
        """Remove an auto-reaction"""
        async with self.config.guild(ctx.guild).auto_reactions() as reactions:
            key = f"{channel.id}-{user.id}"
            if key in reactions:
                del reactions[key]
                await ctx.send("Auto-reaction removed.")
            else:
                await ctx.send("No auto-reaction found for that user in that channel.")

    @autoreact.command(name="list")
    async def list_autoreacts(self, ctx):
        """List all auto-reactions"""
        reactions = await self.config.guild(ctx.guild).auto_reactions()
        if not reactions:
            await ctx.send("No auto-reactions set.")
            return

        msg = "\n".join([f"<#{key.split('-')[0]}> - <@{key.split('-')[1]}>: {emoji}" for key, emoji in reactions.items()])
        await ctx.send(f"Auto-reactions:\n{msg}")

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot:
            return

        guild = message.guild
        if not guild:
            return

        reactions = await self.config.guild(guild).auto_reactions()
        if reactions is None:  # Check if reactions is None
            reactions = {}  # Initialize as an empty dictionary
        key = f"{message.channel.id}-{message.author.id}"
        if key in reactions:
            await message.add_reaction(reactions[key])

    @commands.group()
    async def notify(self, ctx):
        """Manage online status notifications"""
        if ctx.invoked_subcommand is None:
            await ctx.send("Use subcommands: add, remove, list")

    @notify.command(name="add")
    async def add_notification(self, ctx, user: discord.Member):
        """Get notified when a specific user comes online"""
        if user.bot:
            await ctx.send("You cannot track bot accounts!")
            return

        async with self.config.user(ctx.author).online_notifications() as notifications:
            if user.id in notifications:
                await ctx.send(f"You're already tracking {user.display_name}'s online status!")
                return
            
            notifications.append(user.id)
            await ctx.send(f"You will be notified when {user.display_name} comes online!")

    @notify.command(name="remove")
    async def remove_notification(self, ctx, user: discord.Member):
        """Stop getting notifications for a specific user"""
        async with self.config.user(ctx.author).online_notifications() as notifications:
            if user.id in notifications:
                notifications.remove(user.id)
                await ctx.send(f"Stopped tracking {user.display_name}'s online status.")
            else:
                await ctx.send(f"You weren't tracking {user.display_name}'s online status.")

    @notify.command(name="list")
    async def list_notifications(self, ctx):
        """List all users you're tracking"""
        notifications = await self.config.user(ctx.author).online_notifications()
        if not notifications:
            await ctx.send("You're not tracking anyone's online status.")
            return

        users = []
        for user_id in notifications:
            user = self.bot.get_user(user_id)
            if user:
                users.append(f"- {user.name}#{user.discriminator}")
            
        await ctx.send("You're tracking these users:\n" + "\n".join(users))

    @commands.Cog.listener()
    async def on_member_update(self, before, after):
        if before.status != after.status:
            if after.status == discord.Status.online and before.status in [discord.Status.offline, discord.Status.invisible]:
                async for user_data in self.config.all_users():
                    user_id = int(user_data)
                    notifications = await self.config.user_from_id(user_id).online_notifications()
                    
                    if after.id in notifications:
                        user = self.bot.get_user(user_id)
                        if user:
                            try:
                                await user.send(f"🟢 {user.mention}, **{after.name}#{after.discriminator}** is now online!")
                            except discord.Forbidden:
                                pass  # Can't send DM to this user









