
import discord
from redbot.core import commands, Config, checks
import aiohttp
import asyncio

class Radiosonde(commands.Cog):
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
        """Fetch latest sonde data. Returns (data_dict, error_message). 
        data_dict is a dictionary keyed by serial number. error_message is None on success."""
        url = "https://api.v2.sondehub.org/sondes"
        try:
            async with self.session.get(url, timeout=aiohttp.ClientTimeout(total=15)) as resp:
                if resp.status != 200:
                    return {}, f"API returned HTTP {resp.status}"
                data = await resp.json()
                # API returns dict keyed by serial number
                return data if isinstance(data, dict) else {}, None
        except asyncio.TimeoutError:
            return {}, "Request timed out after 15 seconds"
        except aiohttp.ClientConnectorError as e:
            return {}, f"Connection failed: {e.os_error.strerror if e.os_error else str(e)}"
        except aiohttp.ClientError as e:
            return {}, f"Request error: {type(e).__name__}: {e}"
        except OSError as e:
            return {}, f"Network/OS error: {type(e).__name__}: {e}"

    async def fetch_sites(self):
        """Fetch launch sites data. Returns (data_dict, error_message).
        data_dict is keyed by station ID. error_message is None on success."""
        url = "https://api.v2.sondehub.org/sites"
        try:
            async with self.session.get(url, timeout=aiohttp.ClientTimeout(total=15)) as resp:
                if resp.status != 200:
                    return {}, f"API returned HTTP {resp.status}"
                data = await resp.json()
                return data if isinstance(data, dict) else {}, None
        except asyncio.TimeoutError:
            return {}, "Request timed out after 15 seconds"
        except aiohttp.ClientConnectorError as e:
            return {}, f"Connection failed: {e.os_error.strerror if e.os_error else str(e)}"
        except aiohttp.ClientError as e:
            return {}, f"Request error: {type(e).__name__}: {e}"
        except OSError as e:
            return {}, f"Network/OS error: {type(e).__name__}: {e}"

    async def update_sondes(self):
        await self.bot.wait_until_ready()
        while not self.bot.is_closed():
            for guild in self.bot.guilds:
                guild_config = await self.config.guild(guild).all()
                tracked = guild_config.get("tracked_sondes", [])
                channel_id = guild_config.get("update_channel")
                interval = guild_config.get("update_interval", 300)

                if tracked and channel_id:
                    sondes_data, _ = await self.fetch_sondes()
                    channel = self.bot.get_channel(channel_id)
                    if not channel:
                        continue
                    for sonde_id in tracked:
                        sonde = sondes_data.get(sonde_id)
                        if sonde:
                            vel_h = sonde.get("vel_h")
                            vel_v = sonde.get("vel_v")
                            # Calculate speed from horizontal and vertical velocity
                            if vel_h is not None and vel_v is not None:
                                speed = (vel_h**2 + vel_v**2)**0.5
                            elif vel_h is not None:
                                speed = vel_h
                            else:
                                speed = None
                            speed_str = f"{speed:.1f} m/s" if speed is not None else "—"
                            msg = (
                                f"**Sonde {sonde_id} Update**\n"
                                f"Lat: {sonde.get('lat')}\n"
                                f"Lon: {sonde.get('lon')}\n"
                                f"Alt: {sonde.get('alt'):.1f} m\n"
                                f"Speed: {speed_str}\n"
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
    async def status(self, ctx):
        """List current status of all tracked sondes (lat, lon, alt, speed)."""
        tracked = await self.config.guild(ctx.guild).tracked_sondes()
        if not tracked:
            await ctx.send("No sondes are being tracked in this server.")
            return
        async with ctx.typing():
            sondes_data, error = await self.fetch_sondes()
        if error or not sondes_data:
            detail = f" {error}" if error else ""
            await ctx.send(
                f"Could not fetch sonde data from the API.{detail} Try again later."
            )
            return
        lines = []
        for sonde_id in tracked:
            s = sondes_data.get(sonde_id)
            if s is None:
                lines.append(f"**{sonde_id}** — No current data (not in latest API)")
                continue
            lat = s.get("lat", "—")
            lon = s.get("lon", "—")
            alt = s.get("alt")
            vel_h = s.get("vel_h")
            vel_v = s.get("vel_v")
            # Calculate speed from horizontal and vertical velocity
            if vel_h is not None and vel_v is not None:
                speed = (vel_h**2 + vel_v**2)**0.5
            elif vel_h is not None:
                speed = vel_h
            else:
                speed = None
            alt_str = f"{alt:.1f} m" if alt is not None else "—"
            vel_str = f"{speed:.1f} m/s" if speed is not None else "—"
            lines.append(
                f"**{sonde_id}** — Lat: {lat} | Lon: {lon} | Alt: {alt_str} | Speed: {vel_str}"
            )
        await ctx.send("**Tracked sondes status**\n" + "\n".join(lines))

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

    def _format_site_message(self, site_id: str, site: dict) -> str:
        """Build the display message for a single site."""
        name = site.get("station_name", "—")
        pos = site.get("position")
        if isinstance(pos, (list, tuple)) and len(pos) >= 2:
            lon, lat = pos[0], pos[1]
            pos_str = f"Lat: {lat}, Lon: {lon}"
        else:
            pos_str = "—"
        alt = site.get("alt")
        alt_str = f"{alt} m" if alt is not None else "—"
        rs = site.get("rs_types", [])
        rs_str = ", ".join(str(r) for r in rs[:10]) if rs else "—"
        if rs and len(rs) > 10:
            rs_str += f" (+{len(rs) - 10} more)"
        times = site.get("times", [])
        times_str = ", ".join(str(t) for t in times[:6]) if times else "—"
        if times and len(times) > 6:
            times_str += f" (+{len(times) - 6} more)"
        notes = site.get("notes", "").strip()
        msg = (
            f"**{name}** (station `{site_id}`)\n"
            f"Position: {pos_str}\n"
            f"Altitude: {alt_str}\n"
            f"Radiosonde types: {rs_str}\n"
            f"Launch times (UTC): {times_str}"
        )
        if notes:
            msg += f"\n*{notes[:200]}{'…' if len(notes) > 200 else ''}*"
        return msg

    @sonde.command()
    async def site(self, ctx, query: str):
        """Look up a radiosonde launch site by station ID or by name (e.g. 10238, Bergen-Hohne)."""
        async with ctx.typing():
            sites_data, error = await self.fetch_sites()
        if error or not sites_data:
            detail = f" {error}" if error else ""
            await ctx.send(
                f"Could not fetch sites from the API.{detail} Try again later."
            )
            return
        # Try exact match by station ID first
        site = sites_data.get(query)
        if site is not None:
            await ctx.send(self._format_site_message(query, site))
            return
        # Search by station name (case-insensitive, substring)
        query_lower = query.lower()
        matches = [
            (sid, s)
            for sid, s in sites_data.items()
            if query_lower in (s.get("station_name") or "").lower()
        ]
        if not matches:
            await ctx.send(f"No site found for `{query}` (try station ID or part of the site name).")
            return
        if len(matches) == 1:
            sid, s = matches[0]
            await ctx.send(self._format_site_message(sid, s))
            return
        # Multiple matches: list them (up to 15)
        lines = [f"**Multiple sites matching \"{query}\"** — use station ID for one:\n"]
        for sid, s in sorted(matches, key=lambda x: (x[1].get("station_name") or ""))[:15]:
            name = s.get("station_name", "—")
            lines.append(f"• `{sid}` — {name}")
        if len(matches) > 15:
            lines.append(f"*… and {len(matches) - 15} more. Narrow your search.*")
        await ctx.send("\n".join(lines))
