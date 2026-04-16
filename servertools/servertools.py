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

    # --- REGEX PATTERNS ---
    SPOTIFY_URL_RE = re.compile(r'https?://open\.spotify\.com/[^\s<>"]+', re.IGNORECASE)
    INVITE_RE = re.compile(r"(discord\.gg\/|discord\.com\/invite\/)([a-zA-Z0-9\-]+)", re.IGNORECASE)

    def __init__(self, bot):
        self.bot = bot
        self.config = Config.get_conf(self, identifier=492089091320446976)
        
        default_guild = {
            "auto_reactions": [], 
            "spotify_autoclean": False,
            "invite_filter_enabled": False,
            "min_members": 0,
            "invite_rules": [], # Format: {"text": "keyword", "action": "delete/warn/ban"}
            "invite_warn_message": None,  # Custom DM sent on warn (can use {guild} and {offending_server})
        }
        default_user = {
            "online_notifications": [],
            "spotify_dm_autoclean": False,
        }
        
        self.config.register_guild(**default_guild)
        self.config.register_user(**default_user)

    # --- UI COMPONENTS ---

    class InviteRuleModal(discord.ui.Modal, title="Add Invite Rule"):
        """Pop-up modal to add specific server name triggers."""
        trigger_text = discord.ui.TextInput(label="Keyword in Server Name", placeholder="e.g. Free Nitro", required=True)
        action_type = discord.ui.TextInput(label="Action (delete / warn / ban)", placeholder="delete", min_length=3, max_length=6, required=True)

        def __init__(self, cog, guild):
            super().__init__()
            self.cog = cog
            self.guild = guild

        async def on_submit(self, interaction: discord.Interaction):
            action = self.action_type.value.lower()
            if action not in ["delete", "warn", "ban"]:
                return await interaction.response.send_message("❌ Invalid action! Use delete, warn, or ban.", ephemeral=True)
            
            async with self.cog.config.guild(self.guild).invite_rules() as rules:
                rules.append({"text": self.trigger_text.value.lower(), "action": action})
            await interaction.response.send_message(f"✅ Rule added: Servers containing **{self.trigger_text.value}** will trigger a **{action}**.", ephemeral=True)

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

        @discord.ui.button(label="Add Rule", style=discord.ButtonStyle.success)
        async def add_rule(self, interaction: discord.Interaction, button: discord.ui.Button):
            await interaction.response.send_modal(Servertools.InviteRuleModal(self.cog, self.guild))

        @discord.ui.button(label="Wipe Rules/Reactions", style=discord.ButtonStyle.danger)
        async def clear_all(self, interaction: discord.Interaction, button: discord.ui.Button):
            await self.cog.config.guild(self.guild).invite_rules.set([])
            await self.cog.config.guild(self.guild).auto_reactions.set([])
            await interaction.response.send_message("🚨 Rules and reactions have been reset.", ephemeral=True)

        @discord.ui.button(label="View Settings", style=discord.ButtonStyle.secondary)
        async def view_settings(self, interaction: discord.Interaction, button: discord.ui.Button):
            """Show current guild configuration in an ephemeral embed."""
            spotify = await self.cog.config.guild(self.guild).spotify_autoclean()
            invites = await self.cog.config.guild(self.guild).invite_filter_enabled()
            rules = await self.cog.config.guild(self.guild).invite_rules()
            min_members = await self.cog.config.guild(self.guild).min_members()
            reactions = await self.cog.config.guild(self.guild).auto_reactions()
            warn_msg = await self.cog.config.guild(self.guild).invite_warn_message()

            embed = discord.Embed(title=f"Settings for {self.guild.name}", color=0x00aaff)
            embed.add_field(name="Spotify Auto-clean", value="✅ ON" if spotify else "❌ OFF", inline=True)
            embed.add_field(name="Invite Filter", value="✅ ON" if invites else "❌ OFF", inline=True)
            embed.add_field(name="Minimum Invite Members", value=str(min_members), inline=True)
            embed.add_field(name="Invite Warn DM", value=warn_msg if warn_msg else "<Default/Not set>", inline=False)
            rule_list = "\n".join([f"`{r['text']}` ➔ **{r['action']}**" for r in rules]) if rules else "No custom rules."
            embed.add_field(name="Invite Rules", value=rule_list, inline=False)
            react_list = "\n".join(reactions) if reactions else "No auto-reactions configured."
            embed.add_field(name="Auto Reactions", value=react_list, inline=False)

            await interaction.response.send_message(embed=embed, ephemeral=True)

    # --- CONFIG COMMANDS ---

    @commands.command()
    @commands.guild_only()
    @commands.has_permissions(manage_guild=True)
    async def servertools(self, ctx):
        """Open the interactive management panel for settings."""
        spotify = await self.config.guild(ctx.guild).spotify_autoclean()
        invites = await self.config.guild(ctx.guild).invite_filter_enabled()
        rules = await self.config.guild(ctx.guild).invite_rules()
        min_members = await self.config.guild(ctx.guild).min_members()
        reactions = await self.config.guild(ctx.guild).auto_reactions()
        warn_msg = await self.config.guild(ctx.guild).invite_warn_message()

        embed = discord.Embed(title="🛠️ ServerTools Dashboard", color=await ctx.embed_color())
        embed.add_field(name="Spotify Clean", value="✅ ON" if spotify else "❌ OFF", inline=True)
        embed.add_field(name="Invite Filter", value="✅ ON" if invites else "❌ OFF", inline=True)
        embed.add_field(name="Minimum Invite Members", value=str(min_members), inline=True)

        rule_list = "\n".join([f"`{r['text']}` ➔ **{r['action']}**" for r in rules]) if rules else "No custom rules."
        embed.add_field(name="Invite Rules", value=rule_list, inline=False)

        embed.add_field(name="Invite Warn DM", value=warn_msg if warn_msg else "<Default/Not set>", inline=False)
        react_list = "\n".join(reactions) if reactions else "No auto-reactions configured."
        embed.add_field(name="Auto Reactions", value=react_list, inline=False)

        await ctx.send(embed=embed, view=self.ControlPanel(self, ctx.guild))

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

    @invitefilter.command(name="warnmsg")
    @commands.has_permissions(manage_guild=True)
    async def warnmsg(self, ctx, *, message: str = None):
        """Set, clear, or view the DM sent when users are warned for invites.

        Usage:
        - [p]invitefilter warnmsg <message>  -> sets custom DM (use {guild} and {offending_server} placeholders)
        - [p]invitefilter warnmsg clear      -> clears custom DM
        - [p]invitefilter warnmsg            -> shows current message
        """
        if not ctx.guild:
            return
        if message is None:
            current = await self.config.guild(ctx.guild).invite_warn_message()
            if current:
                await ctx.send(f"Current warn DM:\n{current}")
            else:
                await ctx.send("No custom warn DM set. Using default.")
            return

        if message.lower().strip() == "clear":
            await self.config.guild(ctx.guild).invite_warn_message.set(None)
            await ctx.send("Custom warn DM cleared.")
            return

        await self.config.guild(ctx.guild).invite_warn_message.set(message)
        await ctx.send("Custom warn DM updated. You can use {guild} and {offending_server} in the message.")

    # --- UTILITY COMMANDS ---

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
                except discord.Forbidden: await ctx.send("❌ Cannot DM this user.")
            else: await ctx.send("Canceled.")
        except asyncio.TimeoutError: await ctx.send("Timed out.")

    @commands.command()
    @commands.has_permissions(move_members=True)
    async def voicemove(self, ctx, user: discord.Member, channel: discord.VoiceChannel):
        """Move a member to a specified voice channel."""
        try:
            await user.move_to(channel)
            await ctx.send(f"Moved {user.name} to {channel.name}.")
        except discord.Forbidden: await ctx.send("Permission denied.")

    @commands.command()
    @commands.has_permissions(manage_channels=True)
    async def ld(self, ctx, channel: discord.TextChannel):
        """Lock down a text channel."""
        try:
            await channel.set_permissions(ctx.guild.default_role, send_messages=False)
            await ctx.send(f"Locked down {channel.mention}.")
        except discord.Forbidden: await ctx.send("Permission denied.")

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

    # --- EVENT LISTENERS ---

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot or not message.guild: return

        # 1. Invite Filtering & Rules
        if await self.config.guild(message.guild).invite_filter_enabled():
            match = self.INVITE_RE.search(message.content)
            if match:
                try:
                    invite = await self.bot.fetch_invite(match.group(2), with_counts=True)
                    server_name = invite.guild.name.lower() if invite.guild else ""
                    rules = await self.config.guild(message.guild).invite_rules()
                    min_req = await self.config.guild(message.guild).min_members()

                    # Check rules
                    for rule in rules:
                        if rule["text"] in server_name:
                            # remove the offending message first
                            try:
                                await message.delete()
                            except Exception:
                                pass

                            action = (rule.get("action") or "delete").lower()

                            # BAN: attempt to ban the member from the current guild with clear error handling
                            if action == "ban":
                                # Ensure the bot has guild-level ban permission
                                bot_member = message.guild.me
                                if bot_member is None:
                                    try:
                                        bot_member = await message.guild.fetch_member(self.bot.user.id)
                                    except Exception:
                                        bot_member = None

                                if bot_member is None or not bot_member.guild_permissions.ban_members:
                                    await message.channel.send("❌ I don't have the **Ban Members** permission. Please grant it and ensure my role is high enough.", delete_after=10)
                                    return

                                # Resolve the guild Member object for the target
                                member = message.guild.get_member(message.author.id)
                                if member is None:
                                    try:
                                        member = await message.guild.fetch_member(message.author.id)
                                    except Exception:
                                        member = None

                                if member is None:
                                    await message.channel.send(f"❌ Could not locate member {message.author}.", delete_after=5)
                                    return

                                # Prevent banning the bot itself or the guild owner
                                if member.id == bot_member.id:
                                    await message.channel.send("❌ I won't ban myself.", delete_after=5)
                                    return
                                if member == message.guild.owner:
                                    await message.channel.send("❌ Cannot ban the server owner.", delete_after=5)
                                    return

                                # Check role hierarchy / bannable flag
                                if hasattr(member, "bannable") and not member.bannable:
                                    await message.channel.send("❌ I cannot ban that member — check role hierarchy and my permissions.", delete_after=10)
                                    return

                                try:
                                    await member.ban(reason=f"Blacklisted Invite: {server_name}")
                                    await message.channel.send(f"🚫 {member.mention} has been banned for posting a blacklisted invite.", delete_after=5)
                                except discord.Forbidden as e:
                                    await message.channel.send(f"❌ Could not ban {member.mention}. Missing permissions.", delete_after=10)
                                except Exception as e:
                                    # Provide minimal diagnostic info for debugging (short repr)
                                    await message.channel.send(f"❌ Failed to ban {member.mention}. Error: {e!r}", delete_after=10)
                                return

                            # WARN: try to DM the user and notify the channel
                            if action == "warn":
                                dm_sent = False
                                # use custom warn DM if set, allow placeholders {guild} and {offending_server}
                                warn_msg = await self.config.guild(message.guild).invite_warn_message()
                                if warn_msg:
                                    try:
                                        formatted = warn_msg.format(guild=message.guild.name, offending_server=server_name, author=message.author.name)
                                    except Exception:
                                        formatted = warn_msg
                                else:
                                    formatted = f"You were warned in **{message.guild.name}** for posting an invite to **{server_name}**, which is disallowed."

                                try:
                                    await message.author.send(formatted)
                                    dm_sent = True
                                except discord.Forbidden:
                                    dm_sent = False
                                except Exception:
                                    dm_sent = False

                                await message.channel.send(f"⚠️ {message.author.mention} has been warned. {'(DM sent)' if dm_sent else '(Could not DM)'}", delete_after=5)
                                return

                            # Default / delete: just delete and notify
                            await message.channel.send(f"🚫 {message.author.mention}, that invite is not allowed.", delete_after=5)
                            return

                    # Check member count
                    if (invite.approximate_member_count or 0) < min_req:
                        await message.delete()
                        return await message.channel.send(f"⚠️ {message.author.mention}, invites must have {min_req}+ members.", delete_after=5)
                except: pass

        # 2. Spotify Cleaning
        if await self.config.guild(message.guild).spotify_autoclean():
            cleaned = self._extract_clean_spotify_urls(message.content)
            if cleaned: await message.channel.send("\n".join(cleaned))

        # 3. Auto-Reactions (Placeholder for logic)
        reactions = await self.config.guild(message.guild).auto_reactions()

    # --- SPOTIFY HELPERS ---

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

    @commands.command(name="bancheck")
    @commands.has_permissions(manage_guild=True)
    async def bancheck(self, ctx, member: discord.Member):
        """Check whether the bot can ban the provided member and why."""
        guild = ctx.guild
        bot_member = guild.me or await guild.fetch_member(self.bot.user.id)

        lines = []
        # Permission check
        can_ban_perm = bot_member.guild_permissions.ban_members if bot_member else False
        lines.append(f"Bot has Ban Members permission: {'✅' if can_ban_perm else '❌'}")

        # Member resolution
        if member is None:
            lines.append("Could not resolve the target member.")
            return await ctx.send("\n".join(lines))

        # Owner and self checks
        lines.append(f"Target is server owner: {'✅' if member == guild.owner else '❌'}")
        lines.append(f"Target is the bot itself: {'✅' if member.id == bot_member.id else '❌'}")

        # Role hierarchy
        try:
            bot_top = bot_member.top_role.position
            member_top = member.top_role.position
            lines.append(f"Bot top role position: {bot_top}")
            lines.append(f"Member top role position: {member_top}")
            lines.append(f"Bot higher than member: {'✅' if bot_top > member_top else '❌'}")
        except Exception:
            pass

        # bannable attribute
        bannable = getattr(member, 'bannable', None)
        if bannable is None:
            lines.append(f"Member.bannable unknown (object may be a User proxy). Try running the command with a mention.)")
        else:
            lines.append(f"Member.bannable: {'✅' if bannable else '❌'}")

        await ctx.send("\n".join(lines))
