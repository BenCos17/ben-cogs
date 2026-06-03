from __future__ import annotations

from redbot.core import commands, Config
import aiohttp
import asyncio
import json
import io
import discord


class Airframes(commands.Cog):
    """Integrates core Airframes REST API endpoints as simple commands.

    Commands:
    - `[p]airframesadmin set base <url>`: set API base URL (owner-only)
    - `[p]airframesadmin set key <key>`: set X-API-KEY (owner-only)
    - `[p]airframes search [tail]`: search airframes
    - `[p]airframes get <id>`: get airframe by id
    - `[p]airlines search`: search airlines
    - `[p]airports search`: search airports
    - `[p]flights active`: list active flights
    - `[p]messages get <id>`: get message by id
    - `[p]stations list`: list stations
    """

    def __init__(self, bot):
        self.bot = bot
        self.session = aiohttp.ClientSession()
        self.config = Config.get_conf(self, identifier=0xA1F4CE6B9B4D7E01, force_registration=True)
        default = {"base_url": "https://api.airframes.io/v1", "api_key": None}
        self.config.register_global(**default)

    def cog_unload(self) -> None:
        asyncio.create_task(self.session.close())

    async def _request(self, path: str, params: dict | None = None):
        base = await self.config.base_url()
        api_key = await self.config.api_key()
        headers = {}
        # Support either explicit Bearer tokens or X-API-KEY header
        if api_key:
            if isinstance(api_key, str) and api_key.strip().lower().startswith("bearer "):
                headers["Authorization"] = api_key.strip()
            else:
                headers["X-API-KEY"] = api_key
        url = base.rstrip("/") + "/" + path.lstrip("/")
        async with self.session.get(url, params=params or {}, headers=headers) as resp:
            text = await resp.text()
            if resp.status >= 200 and resp.status < 300:
                try:
                    return json.loads(text) if text else None
                except Exception:
                    return text
            raise commands.CommandError(f"{resp.status}: {text}")

    async def _send_json(self, ctx, data):
        # Backwards compatibility: keep raw JSON sender
        s = json.dumps(data, indent=2, default=str)
        if len(s) > 1800:
            await ctx.send(file=discord.File(io.BytesIO(s.encode()), filename="data.json"))
            return
        await ctx.send(f"```json\n{s}\n```")

    def _summarize_object(self, obj: dict) -> str:
        if not isinstance(obj, dict):
            return str(obj)
        # Attempt lightweight summaries for known schema types
        if "tail" in obj or "icao" in obj or "manufacturerModel" in obj:
            return f"Airframe {obj.get('id','?')}: tail={obj.get('tail')}, icao={obj.get('icao')}, model={obj.get('manufacturerModel') or obj.get('manufacturer')}"
        if "name" in obj and ("iata" in obj or "icao" in obj):
            return f"Airline {obj.get('id','?')}: {obj.get('name')} ({obj.get('iata') or obj.get('icao')})"
        if "ident" in obj and "latitude" in obj:
            return f"Airport {obj.get('id','?')}: {obj.get('name')} ({obj.get('ident')}) @ {obj.get('latitude')},{obj.get('longitude')}"
        if "flight" in obj:
            return f"Flight {obj.get('id','?')}: {obj.get('flight')} status={obj.get('status')} dep={obj.get('departingAirport')} dest={obj.get('destinationAirport')}"
        if "messageNumber" in obj or "fromHex" in obj or "text" in obj:
            txt = obj.get('text') or obj.get('fromHex') or ''
            txt = (txt[:140] + '...') if len(txt) > 140 else txt
            return f"Message {obj.get('id','?')}: tail={obj.get('tail')} time={obj.get('timestamp')} text={txt}"
        if "ident" in obj and "messageCount" in obj:
            return f"Station {obj.get('id','?')}: {obj.get('ident')} ({obj.get('countryName')}) messages={obj.get('messageCount')}"
        # Fallback: show top-level keys
        keys = ", ".join(list(obj.keys())[:6])
        return f"Object {obj.get('id','?')}: keys={keys}"

    def _summarize(self, data) -> str:
        if data is None:
            return "No results."
        if isinstance(data, list):
            if len(data) == 0:
                return "No results (empty list)."
            lines = []
            max_items = min(10, len(data))
            for i in range(max_items):
                item = data[i]
                if isinstance(item, dict):
                    lines.append(self._summarize_object(item))
                else:
                    lines.append(str(item))
            if len(data) > max_items:
                lines.append(f"... and {len(data)-max_items} more items")
            return "\n".join(lines)
        if isinstance(data, dict):
            return self._summarize_object(data)
        return str(data)

    async def _present_result(self, ctx, data, title: str | None = None):
        summary = self._summarize(data)
        header = f"**{title}**\n" if title else ""
        # Send summary first
        await ctx.send(header + summary)
        # Then send raw JSON if small enough, else as a file
        s = json.dumps(data, indent=2, default=str)
        if len(s) > 1800:
            await ctx.send(file=discord.File(io.BytesIO(s.encode()), filename="data.json"))
        else:
            await ctx.send(f"```json\n{s}\n```")

    def _make_message_embed(self, msg: dict) -> discord.Embed:
        # Create a rich embed for a single message record
        title = f"Message {msg.get('id', '')}"
        embed = discord.Embed(title=title, timestamp=None)
        # Timestamp
        try:
            if msg.get('timestamp'):
                embed.timestamp = discord.utils.parse_time(msg.get('timestamp'))
        except Exception:
            pass

        # Station info
        station = msg.get('station') or {}
        station_ident = station.get('ident') if isinstance(station, dict) else None
        if station_ident:
            embed.add_field(name="Station", value=f"{station_ident} (id {station.get('id')})", inline=True)

        # Airframe
        airframe = msg.get('airframe') or {}
        if airframe:
            embed.add_field(name="Airframe", value=f"{airframe.get('tail') or 'N/A'} — {airframe.get('icao') or ''}", inline=True)

        # Source and direction
        embed.add_field(name="Source", value=f"{msg.get('source','?')} / {msg.get('sourceType','?')} ({msg.get('linkDirection','?')})", inline=False)

        # Short text preview
        text = msg.get('text') or ''
        if text:
            t = text.strip()
            if len(t) > 750:
                t = t[:750] + "..."
            embed.add_field(name="Text", value=t, inline=False)

        # Other useful metadata
        meta = []
        if msg.get('tail'):
            meta.append(f"Tail: {msg.get('tail')}")
        if msg.get('fromHex'):
            meta.append(f"From: {msg.get('fromHex')}")
        if msg.get('toHex'):
            meta.append(f"To: {msg.get('toHex')}")
        if msg.get('uuid'):
            meta.append(f"UUID: {msg.get('uuid')}")
        if meta:
            embed.add_field(name="Meta", value=" • ".join(meta), inline=False)

        # Station thumbnail or user gravatar
        thumb = None
        user = station.get('user') if isinstance(station, dict) else None
        if user and isinstance(user, dict):
            thumb = user.get('gravatarUrl')
        if not thumb:
            thumb = station.get('flagImageUrl') if isinstance(station, dict) else None
        if thumb:
            try:
                embed.set_thumbnail(url=thumb)
            except Exception:
                pass

        # Footer with timestamps
        created = msg.get('createdAt') or msg.get('updatedAt')
        footer = []
        if created:
            footer.append(f"created: {created}")
        if station and station.get('lastReportAt'):
            footer.append(f"station last report: {station.get('lastReportAt')}")
        if footer:
            embed.set_footer(text=" | ".join(footer))

        return embed

    @commands.group()
    async def airframes(self, ctx: commands.Context):
        """Airframes API commands."""
        pass

    @commands.group()
    async def airframesadmin(self, ctx: commands.Context):
        """Admin commands for Airframes (owner-only)."""
        pass

    @airframesadmin.group()
    async def set(self, ctx: commands.Context):
        """Configuration for Airframes API (owner-only)."""
        pass

    @set.command(name="base")
    @commands.is_owner()
    async def admin_set_base(self, ctx: commands.Context, base_url: str):
        """Set the API base URL."""
        await self.config.base_url.set(base_url)
        await ctx.send(f"Base URL set to: {base_url}")

    @set.command(name="key")
    @commands.is_owner()
    async def admin_set_key(self, ctx: commands.Context, key: str):
        """Set the X-API-KEY header value."""
        await self.config.api_key.set(key)
        await ctx.send("API key saved.")

    @airframes.command(name="search")
    async def airframes_search(self, ctx: commands.Context, tail: str = None, limit: int = 25, page: int = 1):
        """Search Airframes. Optional `tail` filter."""
        params = {"limit": limit, "page": page}
        if tail:
            params["tail"] = tail
        data = await self._request("airframes", params=params)
        await self._present_result(ctx, data, title="Airframes Search")

    @airframes.command(name="get")
    async def airframe_get(self, ctx: commands.Context, id: str):
        """Get an airframe by ID."""
        data = await self._request(f"airframes/{id}")
        await self._present_result(ctx, data, title=f"Airframe {id}")

    @commands.group()
    async def airlines(self, ctx: commands.Context):
        """Airlines API commands."""
        pass

    @airlines.command(name="search")
    async def airlines_search(self, ctx: commands.Context):
        data = await self._request("airlines")
        await self._present_result(ctx, data, title="Airlines")

    @commands.group()
    async def airports(self, ctx: commands.Context):
        """Airports API commands."""
        pass

    @airports.command(name="search")
    async def airports_search(self, ctx: commands.Context):
        data = await self._request("airports")
        await self._present_result(ctx, data, title="Airports")

    @commands.group()
    async def flights(self, ctx: commands.Context):
        """Flights API commands."""
        pass

    @flights.command(name="active")
    async def flights_active(self, ctx: commands.Context, query: str = None):
        params = {}
        if query:
            params["query"] = query
        data = await self._request("flights/active", params=params)
        await self._present_result(ctx, data, title="Active Flights")

    @commands.group()
    async def messages(self, ctx: commands.Context):
        """Messages API commands."""
        pass

    @messages.command(name="get")
    async def messages_get(self, ctx: commands.Context, id: str):
        data = await self._request(f"messages/{id}")
        if isinstance(data, dict):
            embed = self._make_message_embed(data)
            await ctx.send(embed=embed)
            # also send raw JSON as file if large
            s = json.dumps(data, indent=2, default=str)
            if len(s) > 1800:
                await ctx.send(file=discord.File(io.BytesIO(s.encode()), filename="message.json"))
        else:
            await self._present_result(ctx, data, title=f"Message {id}")

    @messages.command(name="list")
    async def messages_list(self, ctx: commands.Context, limit: int = 25, page: int = 1):
        """List messages with optional pagination."""
        params = {"limit": limit, "page": page}
        data = await self._request("messages", params=params)
        # If we got a list of messages, present as embeds (up to 5) then summary
        if isinstance(data, list):
            embeds = []
            for item in data[:5]:
                if isinstance(item, dict):
                    embeds.append(self._make_message_embed(item))
            for e in embeds:
                await ctx.send(embed=e)
            await self._present_result(ctx, data, title="Messages List")
        else:
            await self._present_result(ctx, data, title="Messages List")

    @messages.command(name="find")
    async def messages_find(
        self,
        ctx: commands.Context,
        term: str,
        limit_per_page: int = 50,
        pages: int = 3,
        field: str = None,
        regex: bool = False,
        case_sensitive: bool = False,
    ):
        """Search messages client-side.

        term: search term or regex pattern (if --regex True)
        limit_per_page: how many items to fetch per page from the API
        pages: how many pages to fetch
        field: optional specific field to search (e.g. text, tail, fromHex)
        regex: whether to treat `term` as a regular expression
        case_sensitive: whether matching is case-sensitive
        """
        import re

        matches: list[dict] = []
        try:
            for p in range(1, max(1, pages) + 1):
                params = {"limit": max(1, limit_per_page), "page": p}
                data = await self._request("messages", params=params)
                if not data:
                    break
                for item in data:
                    hay_fields = []
                    if field:
                        v = item.get(field)
                        if v is None:
                            continue
                        hay_fields = [str(v)]
                    else:
                        hay_fields = [str(item.get("text", "")), str(item.get("fromHex", "")), str(item.get("tail", "")), str(item.get("id", ""))]

                    matched = False
                    for h in hay_fields:
                        if regex:
                            flags = 0 if case_sensitive else re.IGNORECASE
                            try:
                                if re.search(term, h, flags=flags):
                                    matched = True
                                    break
                            except re.error:
                                await ctx.send("Invalid regular expression pattern.")
                                return
                        else:
                            if case_sensitive:
                                if term in h:
                                    matched = True
                                    break
                            else:
                                if term.lower() in h.lower():
                                    matched = True
                                    break

                    if matched:
                        matches.append(item)

                # small safety: stop early if we gathered a reasonable number
                if len(matches) >= 500:
                    break

            if not matches:
                await ctx.send("No matches found.")
                return

            # Present first N matches as embeds (up to 5), then full summary
            if matches and isinstance(matches, list):
                embeds = []
                for item in matches[:5]:
                    if isinstance(item, dict):
                        embeds.append(self._make_message_embed(item))
                for e in embeds:
                    await ctx.send(embed=e)
            await self._present_result(ctx, matches, title=f"Found {len(matches)} matches for '{term}'")

        except commands.CommandError:
            raise
        except Exception as e:
            raise commands.CommandError(str(e))

    @commands.group()
    async def stations(self, ctx: commands.Context):
        """Stations API commands."""
        pass

    @stations.command(name="list")
    async def stations_list(self, ctx: commands.Context):
        data = await self._request("stations")
        await self._present_result(ctx, data, title="Stations")


def setup(bot):
    bot.add_cog(Airframes(bot))
