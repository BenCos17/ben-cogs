
import discord
from redbot.core import commands, Config, checks
import aiohttp
import asyncio

class SondeTracker(commands.Cog):
    """Track radiosondes using the SondeHub API."""

    def __init__(self, bot):
        self.bot = bot
        self.config = Config.get_conf(
            self, identifier=492089091320446976, force_registration=True
        )
        # Per guild configuration
        self.config.register_guild(
            tracked_sondes=[],
            update_channel=None,
            update_interval=300  # default 5 minutes
        )

        self.session = aiohttp.ClientSession()
        self.bg_task = self.bot.loop.create_task(self.update_sondes())

    def cog_unload(self):
        self.bg_task.cancel()
        asyncio.create_task(self.session.close())

    async def fetch_sondes(self):
        url = "https://api.sondehub.org/sondes/latest.json"
        async with self.session.get(url) as resp:
            if resp.status != 200:
                return []
            return await resp.json()

    async def update_sondes(self):
        await self.bot.wait_until_ready()
        while not self.bot.is_closed():
            for guild in self.bot.guilds:
                guild_config = await self.config.guild(guild).all()
                tracked = guild_config.get("tracked_sondes", [])
                channel_id = guild_config.get("update_channel")
                interval = guild_config.get("update_interval", 300)

                if tracked and channel_id:
                    sondes_data = await self.fetch_sondes()
                    channel = self.bot.get_channel(channel_id)
                    if not channel:
                        continue
                    for sonde_id in tracked:
                        for sonde in sondes_data:
                            if str(sonde.get("id")) == str(sonde_id):
                                msg = (
                                    f"**Sonde {sonde_id} Update**\n"
                                    f"Lat: {sonde.get('lat')}\n"
                                    f"Lon: {sonde.get('lon')}\n"
                                    f"Alt: {sonde.get('alt'):.1f} m\n"
                                    f"Speed: {sonde.get('vel'):.1f} m/s\n"
                                )
                                await channel.send(msg)
                await asyncio.sleep(1)  # small delay between guilds
            await asyncio.sleep(60)  # wait 1 minute before next batch

    @commands.group()
    async def sonde(self, ctx):
        """Manage sonde tracking."""
        pass

    @sonde.command()
    async def add(self, ctx, sonde_id: str):
        """Add a sonde to track."""
        tracked = await self.config.guild(ctx.guild).tracked_sondes()
        if sonde_id in tracked:
            await ctx.send(f"Sonde {sonde_id} is already tracked.")
            return
        tracked.append(sonde_id)
        await self.config.guild(ctx.guild).tracked_sondes.set(tracked)
        await ctx.send(f"Now tracking sonde {sonde_id}.")

    @sonde.command()
    async def remove(self, ctx, sonde_id: str):
        """Stop tracking a sonde."""
        tracked = await self.config.guild(ctx.guild).tracked_sondes()
        if sonde_id not in tracked:
            await ctx.send(f"Sonde {sonde_id} is not being tracked.")
            return
        tracked.remove(sonde_id)
        await self.config.guild(ctx.guild).tracked_sondes.set(tracked)
        await ctx.send(f"Stopped tracking sonde {sonde_id}.")

    @sonde.command()
    async def list(self, ctx):
        """List all tracked sondes."""
        tracked = await self.config.guild(ctx.guild).tracked_sondes()
        if not tracked:
            await ctx.send("No sondes are being tracked in this server.")
            return
        await ctx.send("Tracked sondes: " + ", ".join(tracked))

    @sonde.command()
    async def setchannel(self, ctx, channel: discord.TextChannel):
        """Set the channel for sonde updates."""
        await self.config.guild(ctx.guild).update_channel.set(channel.id)
        await ctx.send(f"Sonde updates will be sent to {channel.mention}.")

    @sonde.command()
    async def interval(self, ctx, seconds: int):
        """Set the update interval in seconds."""
        if seconds < 30:
            await ctx.send("Interval must be at least 30 seconds.")
            return
        await self.config.guild(ctx.guild).update_interval.set(seconds)
        await ctx.send(f"Update interval set to {seconds} seconds.")
