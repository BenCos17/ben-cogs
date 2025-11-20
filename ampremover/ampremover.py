from redbot.core import commands, Config
import requests
import re
from discord import Embed
import aiohttp
import asyncio
from .dashboard_integration import DashboardIntegration
import time

class AmputatorBot(DashboardIntegration, commands.Cog):
    """Cog to convert AMP URLs to canonical forms using the AmputatorBot API.
    
    Supports opt-in/out for servers and users, and automatic conversion in messages.
    """
    
    def __init__(self, bot):
        self.bot = bot
        self.config = Config.get_conf(self, identifier=492089091320446976)  
        # Register a guild-specific variable for opted-in status and basic stats
        self.config.register_guild(
            opted_in=False,
            stats={
                "total_conversions": 0,
                "total_urls_detected": 0,
                "total_canonical_returned": 0,
                "last_conversion_ts": 0,
            },
        )
        self.opted_in_users = set()

    async def initialize_config(self, guild):
        """Initialize the configuration for the server and return opted-in status."""
        return await self.config.guild(guild).opted_in()

    @commands.group(name='amputator', invoke_without_command=True)
    async def amputator(self, ctx):
        """Base command for AmputatorBot operations. Use subcommands to opt-in, opt-out, convert, or view settings."""
        await ctx.send("Use `[p]amputator optin`, `[p]amputator optout`, or `[p]amputator convert`.")

    @amputator.command(name='optin')
    async def opt_in(self, ctx):
        """Opt-in to use the AmputatorBot service for this server."""
        if ctx.guild:
            await self.config.guild(ctx.guild).opted_in.set(True)
            await ctx.send("Successfully opted in to use the AmputatorBot service.")
        else:
            await ctx.send("This command cannot be used in DMs.")

    @amputator.command(name='optout')
    async def opt_out(self, ctx):
        """Opt-out from using the AmputatorBot service for this server."""
        if ctx.guild:
            await self.config.guild(ctx.guild).opted_in.set(False)
            await ctx.send("Successfully opted out from using the AmputatorBot service.")
        else:
            await ctx.send("This command cannot be used in DMs.")

    @amputator.command(name='convert')
    async def convert_amp(self, ctx, *, message: str):
        """Convert AMP URLs in a message to canonical URLs using AmputatorBot API."""
        urls = self.extract_urls(message)
        if not urls:
            await ctx.send("No URLs found in the message.")
            return

        canonical_links = await self.fetch_canonical_links(urls)
        # Update stats if invoked in a guild context
        if ctx.guild is not None:
            await self._update_guild_stats(ctx.guild, urls_detected=len(urls), canonical_returned=len(canonical_links))
        if canonical_links:
            if ctx.guild:  # If in a server, respond in the channel
                await ctx.send(f"Canonical URL(s): {'; '.join(canonical_links)}")
            else:  # If in DMs, respond in DMs
                await ctx.author.send(f"Canonical URL(s): {'; '.join(canonical_links)}")
        else:
            await ctx.send("No canonical URLs found.")

    def extract_urls(self, message: str):
        """Extract URLs from a given message using regex."""
        return re.findall(r'(https?://\S+)', message)

    async def fetch_canonical_links(self, urls):
        """Fetch canonical links for a list of URLs using the AmputatorBot API."""
        canonical_links = []
        async with aiohttp.ClientSession() as session:
            for url in urls:
                api_url = f"https://www.amputatorbot.com/api/v1/convert?gac=true&md=3&q={url}"
                try:
                    async with session.get(api_url, timeout=10) as response:
                        if response.status == 200:
                            data = await response.json()
                            if not 'error' in data:
                                links = [link['canonical']['url'] for link in data if link['canonical']]
                                canonical_links.extend(links)
                except (aiohttp.ClientError, asyncio.TimeoutError):
                    continue
        return canonical_links

    @commands.Cog.listener()
    async def on_message(self, message):
        """Detect and convert AMP links in messages if the server or user is opted in."""
        if message.guild:  # Check if the message is in a guild
            if await self.config.guild(message.guild).opted_in():  # Check if the server is opted in
                urls = self.extract_urls(message.content)
                if urls:
                    canonical_links = await self.fetch_canonical_links(urls)
                    # Update stats for guild automatic conversion checks
                    await self._update_guild_stats(message.guild, urls_detected=len(urls), canonical_returned=len(canonical_links))
                    if canonical_links:
                        await message.channel.send(f"Canonical URL(s): {'; '.join(canonical_links)}")
        else:  # DM context
            if message.author.id in self.opted_in_users:  # Check if the user is opted in
                urls = self.extract_urls(message.content)
                if urls:
                    canonical_links = await self.fetch_canonical_links(urls)
                    if canonical_links:
                        await message.author.send(f"Canonical URL(s): {'; '.join(canonical_links)}")

    async def _update_guild_stats(self, guild, *, urls_detected: int, canonical_returned: int) -> None:
        """Update guild-level stats used by the dashboard.

        Increments total conversion events, accumulates counts, and records the last conversion timestamp.
        """
        async with self.config.guild(guild).stats() as stats:
            stats["total_conversions"] = int(stats.get("total_conversions", 0)) + 1
            stats["total_urls_detected"] = int(stats.get("total_urls_detected", 0)) + int(urls_detected)
            stats["total_canonical_returned"] = int(stats.get("total_canonical_returned", 0)) + int(canonical_returned)
            stats["last_conversion_ts"] = int(time.time())

    @amputator.command(name='settings')
    async def show_settings(self, ctx):
        """Display the current configuration settings for the AmputatorBot in this guild."""
        if ctx.guild:  # Check if the command is invoked in a guild
            opted_in = await self.config.guild(ctx.guild).opted_in()  # Get opted-in status
            status_color = "✅" if opted_in else "❌"  # Use checkmark for Yes and cross for No
            status_text = "Opted In: " + (f"{status_color} Yes" if opted_in else f"{status_color} No")  # Create status text
            
            embed = Embed(title=f"Settings for {ctx.guild.name}", color=0x00ff00 if opted_in else 0xff0000)  # Green for Yes, Red for No
            embed.add_field(name="Status", value=status_text, inline=False)  # Add status field
            embed.set_footer(text="Use [p]amputator for more commands.")  # Add a footer for additional context
            
            await ctx.send(embed=embed)  # Send the embed message
        else:  # DM context
            await ctx.send("This command cannot be used in DMs.")