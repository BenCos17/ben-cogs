
import discord
from redbot.core import commands, Config, checks
import aiohttp
import asyncio
from .dashboard import DashboardIntegration

__version__ = "1.0.1"

class Radiosonde(DashboardIntegration, commands.Cog):
    """Track radiosondes using the SondeHub API."""

    def __init__(self, bot):
        self.bot = bot
        self._radiosonde_cog = self  # For dashboard integration
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
        # track last update times per guild to respect configured intervals
        self._last_updates = {}

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

    async def fetch_telemetry(self, serial: str):
        """Fetch telemetry history for a given sonde serial. Returns (data, error)."""
        # Individual sonde telemetry is served at /sonde/{serial} (singular)
        url = f"https://api.v2.sondehub.org/sonde/{serial}"
        try:
            async with self.session.get(url, timeout=aiohttp.ClientTimeout(total=15)) as resp:
                if resp.status != 200:
                    if resp.status == 404:
                        return None, f"Not found (HTTP 404): no telemetry for {serial}"
                    return None, f"API returned HTTP {resp.status}"
                data = await resp.json()
                return data, None
        except asyncio.TimeoutError:
            return None, "Request timed out after 15 seconds"
        except aiohttp.ClientConnectorError as e:
            return None, f"Connection failed: {e.os_error.strerror if e.os_error else str(e)}"
        except aiohttp.ClientError as e:
            return None, f"Request error: {type(e).__name__}: {e}"
        except OSError as e:
            return None, f"Network/OS error: {type(e).__name__}: {e}"

    async def fetch_sondes_near(self, lat: float, lon: float, distance: float = 100.0):
        """Query sondes by location. `distance` is passed directly to API (units used by API).
        Returns (data_dict, error)."""
        url = f"https://api.v2.sondehub.org/sondes?lat={lat}&lon={lon}&distance={distance}"
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

    async def fetch_realtime_endpoint(self):
        """Return the MQTT-over-WebSocket endpoint from /sondes/websocket."""
        url = "https://api.v2.sondehub.org/sondes/websocket"
        try:
            async with self.session.get(url, timeout=aiohttp.ClientTimeout(total=10)) as resp:
                if resp.status != 200:
                    return None, f"API returned HTTP {resp.status}"
                data = await resp.json()
                return data, None
        except Exception as e:
            return None, str(e)

    async def fetch_listeners_stats(self):
        """Fetch aggregated listener/uploader statistics from /listeners/stats."""
        url = "https://api.v2.sondehub.org/listeners/stats"
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
            now = self.bot.loop.time()
            for guild in self.bot.guilds:
                guild_config = await self.config.guild(guild).all()
                tracked = guild_config.get("tracked_sondes", [])
                channel_id = guild_config.get("update_channel")
                interval = guild_config.get("update_interval", 300)

                if not tracked or not channel_id:
                    continue

                last = self._last_updates.get(guild.id, 0)
                if now - last < interval:
                    continue

                sondes_data, error = await self.fetch_sondes()
                channel = self.bot.get_channel(channel_id)
                if error:
                    # Inform channel of failures optionally (only once)
                    try:
                        if channel:
                            await channel.send(f"Could not fetch sondes for updates: {error}")
                    except Exception:
                        pass
                    continue
                if not channel:
                    continue

                for sonde_id in tracked:
                    sonde = sondes_data.get(sonde_id)
                    if not sonde:
                        e = discord.Embed(title=f"{sonde_id}", description="No current data (not in latest API)", colour=0xDD5555)
                        await channel.send(embed=e)
                        continue
                    embed = self._sonde_to_embed(sonde_id, sonde)
                    await channel.send(embed=embed)

                self._last_updates[guild.id] = now
                await asyncio.sleep(1)  # small delay between guilds
            await asyncio.sleep(5)  # short polling delay

    def _format_sonde_message(self, sonde_id: str, sonde: dict) -> str:
        """Create a safe, readable message for a single sonde dict."""
        def fmt_num(v, prec=5):
            return f"{v:.{prec}f}" if isinstance(v, (int, float)) else (str(v) if v is not None else "—")

        lat = fmt_num(sonde.get("lat"), 5)
        lon = fmt_num(sonde.get("lon"), 5)
        alt = sonde.get("alt")
        alt_str = f"{alt:.1f} m" if isinstance(alt, (int, float)) else (str(alt) if alt is not None else "—")

        vel_h = sonde.get("vel_h")
        vel_v = sonde.get("vel_v")
        if isinstance(vel_h, (int, float)) and isinstance(vel_v, (int, float)):
            speed = (vel_h ** 2 + vel_v ** 2) ** 0.5
        elif isinstance(vel_h, (int, float)):
            speed = vel_h
        else:
            speed = None
        speed_str = f"{speed:.1f} m/s" if speed is not None else "—"

        heading = sonde.get("heading")
        sats = sonde.get("sats")
        temp = sonde.get("temp")
        batt = sonde.get("batt")

        lines = [f"**Sonde {sonde_id} Update**"]
        lines.append(f"Lat: {lat} | Lon: {lon} | Alt: {alt_str}")
        lines.append(f"Speed: {speed_str} | Heading: {heading if heading is not None else '—'}")
        lines.append(f"Sats: {sats if sats is not None else '—'} | Temp: {temp if temp is not None else '—'}°C | Batt: {batt if batt is not None else '—'} V")
        uploader = sonde.get("uploader_callsign") or sonde.get("uploader")
        if uploader:
            lines.append(f"Uploader: {uploader}")
        return "\n".join(lines)

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
        embeds = []
        for sonde_id in tracked:
            s = sondes_data.get(sonde_id)
            if s is None:
                e = discord.Embed(title=f"{sonde_id}", description="No current data (not in latest API)", colour=0xDD5555)
                embeds.append(e)
                continue
            embeds.append(self._sonde_to_embed(sonde_id, s))

        # Send embeds in small groups to avoid hitting limits
        batch = []
        for e in embeds:
            batch.append(e)
            if len(batch) >= 5:
                # Discord API supports multiple embeds; send this batch
                await ctx.send(embeds=batch)
                batch = []
        if batch:
            await ctx.send(embeds=batch)

    def _sonde_to_embed(self, sonde_id: str, sonde: dict) -> discord.Embed:
        """Build a Discord embed summarizing a sonde's current data."""
        def fmt_num(v, prec=5):
            return f"{v:.{prec}f}" if isinstance(v, (int, float)) else (str(v) if v is not None else "—")

        lat = fmt_num(sonde.get("lat"), 5)
        lon = fmt_num(sonde.get("lon"), 5)
        alt = sonde.get("alt")
        alt_str = f"{alt:.1f} m" if isinstance(alt, (int, float)) else (str(alt) if alt is not None else "—")

        vel_h = sonde.get("vel_h")
        vel_v = sonde.get("vel_v")
        if isinstance(vel_h, (int, float)) and isinstance(vel_v, (int, float)):
            speed = (vel_h ** 2 + vel_v ** 2) ** 0.5
        elif isinstance(vel_h, (int, float)):
            speed = vel_h
        else:
            speed = None
        speed_str = f"{speed:.1f} m/s" if speed is not None else "—"

        heading = sonde.get("heading")
        sats = sonde.get("sats")
        temp = sonde.get("temp")
        batt = sonde.get("batt")
        uploader = sonde.get("uploader_callsign") or sonde.get("uploader")

        title = f"Sonde {sonde_id}"
        desc = f"Lat: {lat} | Lon: {lon}\nAlt: {alt_str} | Speed: {speed_str}"
        e = discord.Embed(title=title, description=desc, colour=0x55AAFF)
        e.add_field(name="Heading", value=str(heading) if heading is not None else "—", inline=True)
        e.add_field(name="Sats", value=str(sats) if sats is not None else "—", inline=True)
        e.add_field(name="Temp (°C)", value=str(temp) if temp is not None else "—", inline=True)
        e.add_field(name="Battery (V)", value=str(batt) if batt is not None else "—", inline=True)
        if uploader:
            e.set_footer(text=f"Uploader: {uploader}")
        last = sonde.get("last_seen") or sonde.get("datetime") or sonde.get("time")
        if last:
            e.add_field(name="Last seen", value=str(last), inline=False)
        return e

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
            await ctx.send(embed=self._site_to_embed(query, site))
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
            await ctx.send(embed=self._site_to_embed(sid, s))
            return
        # Multiple matches: list them (up to 15)
        desc_lines = [f"Multiple sites matching \"{query}\" — use station ID for one:"]
        for sid, s in sorted(matches, key=lambda x: (x[1].get("station_name") or ""))[:15]:
            name = s.get("station_name", "—")
            desc_lines.append(f"`{sid}` — {name}")
        if len(matches) > 15:
            desc_lines.append(f"… and {len(matches) - 15} more. Narrow your search.")
        e = discord.Embed(title=f"Sites matching '{query}'", description="\n".join(desc_lines), colour=0x55AAFF)
        await ctx.send(embed=e)

    @sonde.command()
    async def history(self, ctx, serial: str, limit: int = 25):
        """Show recent telemetry history for a radiosonde serial."""
        async with ctx.typing():
            data, error = await self.fetch_telemetry(serial)
        if error:
            await ctx.send(
                f"Could not fetch telemetry for `{serial}`: {error}. Check the serial number or try again later."
            )
            return
        if not data:
            await ctx.send(f"No telemetry found for `{serial}`. It may be expired or never uploaded.")
            return
        # Try to find telemetry list in response
        telemetry = None
        if isinstance(data, dict):
            telemetry = data.get("telemetry") or data.get("history") or data.get("data")
        if telemetry is None and isinstance(data, list):
            telemetry = data
        if not telemetry:
            await ctx.send(f"No telemetry history found for `{serial}`.")
            return
        # Take last `limit` points
        points = telemetry[-limit:]
        desc_lines = []
        for p in reversed(points):
            t = p.get("time") or p.get("timestamp") or p.get("ts") or "—"
            lat = p.get("lat") if p.get("lat") is not None else "—"
            lon = p.get("lon") if p.get("lon") is not None else "—"
            alt = p.get("alt")
            alt_str = f"{alt:.1f} m" if isinstance(alt, (int, float)) else (str(alt) if alt is not None else "—")
            desc_lines.append(f"{t} — Lat: {lat} | Lon: {lon} | Alt: {alt_str}")
        desc = "\n".join(desc_lines)
        if len(desc) > 3500:
            desc = desc[:3490] + "\n…output truncated…"
        e = discord.Embed(title=f"Telemetry for {serial} (last {len(points)})", description=desc, colour=0x55AAFF)
        await ctx.send(embed=e)

    @sonde.command()
    async def nearby(self, ctx, lat: float, lon: float, distance: float = 100.0):
        """List sondes near a given lat/lon within `distance` (API units)."""
        async with ctx.typing():
            data, error = await self.fetch_sondes_near(lat, lon, distance)
        if error:
            await ctx.send(f"Could not query sondes near location: {error}. Check parameters or try again later.")
            return
        # data expected as dict keyed by serial
        if not isinstance(data, dict) or not data:
            await ctx.send("No sondes found near that location.")
            return
        desc_lines = [f"Sondes within {distance} of {lat},{lon}"]
        for sid, s in sorted(data.items(), key=lambda x: x[0])[:25]:
            la = s.get("lat", "—")
            lo = s.get("lon", "—")
            alt = s.get("alt")
            alt_str = f"{alt:.1f} m" if isinstance(alt, (int, float)) else (str(alt) if alt is not None else "—")
            desc_lines.append(f"`{sid}` — Lat: {la} | Lon: {lo} | Alt: {alt_str}")
        if len(data) > 25:
            desc_lines.append(f"… and {len(data) - 25} more.")
        e = discord.Embed(title="Nearby sondes", description="\n".join(desc_lines), colour=0x55AAFF)
        await ctx.send(embed=e)

    @sonde.command()
    async def realtime(self, ctx):
        """Show the MQTT-over-WebSocket endpoint used for realtime sonde streaming."""
        async with ctx.typing():
            data, error = await self.fetch_realtime_endpoint()
        if error:
            await ctx.send(f"Could not fetch realtime endpoint: {error}. Try again later or check API status.")
            return
        if not data:
            await ctx.send("Realtime endpoint returned unexpected data; try again later.")
            return
        # Present the returned JSON or common `url` key
        url = None
        if isinstance(data, dict):
            url = data.get("url") or data.get("endpoint") or data.get("ws")
        if not url:
            await ctx.send(embed=discord.Embed(title="Realtime endpoint", description=str(data), colour=0xDD5555))
            return
        e = discord.Embed(title="Realtime MQTT-over-WebSocket endpoint", description=url, colour=0x55AAFF)
        await ctx.send(embed=e)

    @sonde.command()
    async def listeners(self, ctx):
        """Show aggregated listener/uploader statistics from SondeHub."""
        async with ctx.typing():
            data, error = await self.fetch_listeners_stats()
        if error:
            await ctx.send(f"Could not fetch listener stats: {error}. Try again later.")
            return
        if not data:
            await ctx.send("No listener statistics available at the moment.")
            return
        # Present a brief summary of top-level keys
        e = discord.Embed(title="Listener statistics (summary)", colour=0x55AAFF)
        if isinstance(data, dict):
            if "uploaders" in data:
                e.add_field(name="Uploaders", value=str(len(data.get("uploaders") or [])), inline=True)
            if "stations" in data:
                e.add_field(name="Stations", value=str(len(data.get("stations") or [])), inline=True)
            if "listeners" in data:
                e.add_field(name="Listeners", value=str(len(data.get("listeners") or [])), inline=True)
            # show some other top-level values
            for k, v in list(data.items())[:8]:
                if k in ("uploaders", "stations", "listeners"):
                    continue
                if isinstance(v, (int, float, str)):
                    e.add_field(name=k, value=str(v), inline=True)
        else:
            e.description = str(data)
        await ctx.send(embed=e)

    def _site_to_embed(self, site_id: str, site: dict) -> discord.Embed:
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
        e = discord.Embed(title=f"{name} ({site_id})", colour=0x55AAFF)
        e.add_field(name="Position", value=pos_str, inline=False)
        e.add_field(name="Altitude", value=alt_str, inline=True)
        e.add_field(name="Radiosonde types", value=rs_str, inline=True)
        e.add_field(name="Launch times (UTC)", value=times_str, inline=False)
        if notes:
            e.add_field(name="Notes", value=notes[:300] + ("…" if len(notes) > 300 else ""), inline=False)
        return e
    @sonde.command()
    async def version(self, ctx):
        """Show the cog version."""
        e = discord.Embed(title="Radiosonde Cog", description=f"Version {__version__}", colour=0x55AAFF)
        e.add_field(name="API", value="SondeHub V2", inline=False)
        await ctx.send(embed=e)