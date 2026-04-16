import os
import discord
from redbot.core import commands, Config
import asyncio
import aiohttp
import re
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit
from io import BytesIO
from PIL import Image, ImageDraw, ImageFont

class Servertools(commands.Cog):
    """Advanced server management utilities with interactive UI controls."""

    SPOTIFY_URL_RE = re.compile(r'https?://open\.spotify\.com/[^\s<>"]+', re.IGNORECASE)
    INVITE_RE = re.compile(r"(discord\.gg\/|discord\.com\/invite\/)([a-zA-Z0-9\-]+)", re.IGNORECASE)

    def __init__(self, bot):
        self.bot = bot
        self.config = Config.get_conf(self, identifier=492089091320446976, force_registration=True)
        
        default_guild = {
            "auto_reactions": {},
            "spotify_autoclean": False,
            "invite_filter_enabled": False,
            "min_members": 0,
        }
        default_user = {
            "online_notifications": [],
            "spotify_dm_autoclean": False,
        }
        
        #  register these individually to prevent the 'Group vs Value' conflict from blocking the entire registration block.
        for key, value in default_guild.items():
            self.config.register_guild(**{key: value})
            
        self.config.register_user(**default_user)

    # UI 

    class ControlPanel(discord.ui.View):
        """Interactive UI for Cog settings."""
        def __init__(self, cog, guild):
            super().__init__(timeout=60)
            self.cog = cog
            self.guild = guild

        @discord.ui.button(label="Spotify Clean", style=discord.ButtonStyle.primary)
        async def toggle_spotify(self, interaction: discord.Interaction, button: discord.ui.Button):
            current = await self.cog.config.guild(self.guild).spotify_autoclean()
            await self.cog.config.guild(self.guild).spotify_autoclean.set(not current)
            status = "Enabled" if not current else "Disabled"
            await interaction.response.send_message(f"✅ Spotify Auto-clean is now **{status}**.", ephemeral=True)

        @discord.ui.button(label="Invite Filter", style=discord.ButtonStyle.secondary)
        async def toggle_invite(self, interaction: discord.Interaction, button: discord.ui.Button):
            current = await self.cog.config.guild(self.guild).invite_filter_enabled()
            await self.cog.config.guild(self.guild).invite_filter_enabled.set(not current)
            status = "Enabled" if not current else "Disabled"
            await interaction.response.send_message(f"✅ Invite filtering is now **{status}**.", ephemeral=True)

        @discord.ui.button(label="Wipe Auto-Reactions", style=discord.ButtonStyle.danger)
        async def clear_reactions(self, interaction: discord.Interaction, button: discord.ui.Button):
            await self.cog.config.guild(self.guild).auto_reactions.set({})
            await interaction.response.send_message("🚨 All auto-reactions for this server have been cleared.", ephemeral=True)

#config stuff
    @commands.command()
    @commands.guild_only()
    @commands.has_permissions(manage_guild=True)
    async def servertools(self, ctx):
        """Open the interactive management panel for settings."""
        embed = discord.Embed(
            title="🛠️ ServerTools Control Panel",
            description="Toggle guild utilities using the buttons below.",
            color=await ctx.embed_color()
        )
        # Fetch current statuses for the embed
        spotify = await self.config.guild(ctx.guild).spotify_autoclean()
        invites = await self.config.guild(ctx.guild).invite_filter_enabled()
        min_m = await self.config.guild(ctx.guild).min_members()

        embed.add_field(name="Spotify Clean", value="✅ ON" if spotify else "❌ OFF")
        embed.add_field(name="Invite Filter", value="✅ ON" if invites else "❌ OFF")
        embed.add_field(name="Min Invite Members", value=str(min_m))
        
        view = self.ControlPanel(self, ctx.guild)
        await ctx.send(embed=embed, view=view)

    @commands.group()
    @commands.has_permissions(manage_guild=True)
    async def invitefilter(self, ctx):
        """Manage invite content filtering settings."""
        if ctx.invoked_subcommand is None:
            await ctx.send_help(ctx.command)

    @invitefilter.command(name="minmembers")
    async def set_min_members(self, ctx, count: int):
        """Set minimum member count required for an invite link to stay."""
        await self.config.guild(ctx.guild).min_members.set(count)
        await ctx.send(f"Invites must now have at least **{count}** members to be allowed.")


    @commands.command()
    @commands.has_permissions(manage_guild=True)
    async def moddm(self, ctx, user: discord.User, *, message):
        """Send a direct message to a user as a moderator."""
        if not ctx.guild: return
        confirm_embed = discord.Embed(title="Confirmation", description=f"Send this to {user.name}?", color=0x00ff00)
        await ctx.send(embed=confirm_embed)
        
        def check(m): return m.author == ctx.author and m.channel == ctx.channel and m.content.lower() in ['yes', 'y', 'no', 'n']
        try:
            resp = await self.bot.wait_for('message', check=check, timeout=30.0)
            if resp.content.lower() in ['yes', 'y']:
                try:
                    dm = discord.Embed(title="Message from Server", description=message, color=0x00ff00)
                    dm.set_footer(text=f"Sent from {ctx.guild.name}")
                    await user.send(embed=dm)
                    await ctx.send("✅ Message sent.")
                except discord.Forbidden:
                    await ctx.send("❌ Cannot DM this user.")
            else:
                await ctx.send("Canceled.")
        except asyncio.TimeoutError:
            await ctx.send("Timed out.")

    @commands.command()
    @commands.has_permissions(move_members=True)
    async def voicemove(self, ctx, user: discord.Member, channel: discord.VoiceChannel):
        """Move a member to a specified voice channel."""
        try:
            await user.move_to(channel)
            await ctx.send(f"Moved {user.name} to {channel.name}.")
        except discord.Forbidden:
            await ctx.send("Permission denied.")

    @commands.command()
    @commands.has_permissions(manage_channels=True)
    async def ld(self, ctx, channel: discord.TextChannel):
        """Lock down a text channel."""
        try:
            await channel.set_permissions(ctx.guild.default_role, send_messages=False)
            await ctx.send(f"Locked down {channel.mention}.")
        except discord.Forbidden:
            await ctx.send("Permission denied.")

    @commands.command()
    @commands.has_permissions(manage_messages=True)
    async def purge(self, ctx, amount: int):
        """Delete messages in current channel."""
        await ctx.channel.purge(limit=amount + 1)

    @commands.command()
    @commands.has_permissions(view_audit_log=True)
    async def auditlog(self, ctx, amount: int = 5):
        """Display recent audit log entries."""
        async for log in ctx.guild.audit_logs(limit=amount):
            action = log.action.name.replace("_", " ").title()
            await ctx.send(f"**{log.user}** performed **{action}** on **{log.target}**")

    @commands.command(name='fakeping')
    @commands.guild_only()
    async def fake_ping(self, ctx):
        """Send a fake ping image badge."""
        icon_url = ctx.guild.icon.url if ctx.guild.icon else None
        if not icon_url: return await ctx.send("No server icon.")
        async with aiohttp.ClientSession() as session:
            async with session.get(str(icon_url)) as resp:
                image_bytes = await resp.read()
                image = Image.open(BytesIO(image_bytes)).convert('RGBA')
                image.thumbnail((64, 64))
                draw = ImageDraw.Draw(image)
                badge_radius = 14
                badge_center = (image.width - badge_radius, image.height - badge_radius)
                draw.ellipse([badge_center[0]-16, badge_center[1]-16, badge_center[0]+16, badge_center[1]+16], fill=(255, 255, 255))
                draw.ellipse([badge_center[0]-14, badge_center[1]-14, badge_center[0]+14, badge_center[1]+14], fill=(237, 66, 69))
                try: font = ImageFont.truetype("arial.ttf", 20)
                except: font = ImageFont.load_default()
                draw.text((badge_center[0]-5, badge_center[1]-10), "1", font=font, fill=(255, 255, 255))
                buffer = BytesIO()
                image.save(buffer, format='PNG')
                buffer.seek(0)
                await ctx.send(file=discord.File(buffer, filename='ping.png'))


    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot: return

        #  Invite Filters
        if message.guild and await self.config.guild(message.guild).invite_filter_enabled():
            match = self.INVITE_RE.search(message.content)
            if match:
                try:
                    invite = await self.bot.fetch_invite(match.group(2), with_counts=True)
                    min_req = await self.config.guild(message.guild).min_members()
                    if (invite.approximate_member_count or 0) < min_req:
                        await message.delete()
                        await message.channel.send(f"⚠️ {message.author.mention}, invites must be to servers with {min_req}+ members.", delete_after=5)
                        return
                except discord.NotFound: pass

        # Spotify Cleaning
        if message.guild:
            if await self.config.guild(message.guild).spotify_autoclean():
                cleaned = self._extract_clean_spotify_urls(message.content)
                if cleaned: await message.channel.send("\n".join(cleaned))
        else: # DMs
            if await self.config.user(message.author).spotify_dm_autoclean():
                cleaned = self._extract_clean_spotify_urls(message.content)
                if cleaned: await message.channel.send("\n".join(cleaned))

        # 3. Auto-Reactions
        if message.guild:
            reactions = await self.config.guild(message.guild).auto_reactions()
            # Safety check: Ensure reactions is a dict before trying to access it
            if isinstance(reactions, dict):
                key = f"{message.channel.id}-{message.author.id}"
                if key in reactions:
                    try: await message.add_reaction(reactions[key])
                    except: pass

    # SPOTIFY HELPERS

    def _clean_spotify_url(self, url: str):
        try:
            parts = urlsplit(url)
            params = parse_qsl(parts.query, keep_blank_values=True)
            filtered = [(k, v) for k, v in params if k.lower() != "si"]
            new_query = urlencode(filtered, doseq=True)
            cleaned = urlunsplit((parts.scheme, parts.netloc, parts.path, new_query, parts.fragment))
            return cleaned if cleaned != url else None
        except: return None

    def _extract_clean_spotify_urls(self, content: str):
        cleaned_links = []
        for match in self.SPOTIFY_URL_RE.findall(content):
            cleaned = self._clean_spotify_url(match)
            if cleaned and cleaned not in cleaned_links: cleaned_links.append(cleaned)
        return cleaned_links
