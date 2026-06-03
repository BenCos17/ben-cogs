from __future__ import annotations

from redbot.core import commands, Config
import aiohttp
import asyncio
import json


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
        if api_key:
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
        s = json.dumps(data, indent=2, default=str)
        if len(s) > 1900:
            s = s[:1900] + "\n... (truncated)"
        await ctx.send(f"```json\n{s}\n```")

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
        await self._send_json(ctx, data)

    @airframes.command(name="get")
    async def airframe_get(self, ctx: commands.Context, id: str):
        """Get an airframe by ID."""
        data = await self._request(f"airframes/{id}")
        await self._send_json(ctx, data)

    @commands.group()
    async def airlines(self, ctx: commands.Context):
        """Airlines API commands."""
        pass

    @airlines.command(name="search")
    async def airlines_search(self, ctx: commands.Context):
        data = await self._request("airlines")
        await self._send_json(ctx, data)

    @commands.group()
    async def airports(self, ctx: commands.Context):
        """Airports API commands."""
        pass

    @airports.command(name="search")
    async def airports_search(self, ctx: commands.Context):
        data = await self._request("airports")
        await self._send_json(ctx, data)

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
        await self._send_json(ctx, data)

    @commands.group()
    async def messages(self, ctx: commands.Context):
        """Messages API commands."""
        pass

    @messages.command(name="get")
    async def messages_get(self, ctx: commands.Context, id: str):
        data = await self._request(f"messages/{id}")
        await self._send_json(ctx, data)

    @messages.command(name="list")
    async def messages_list(self, ctx: commands.Context, limit: int = 25, page: int = 1):
        """List messages with optional pagination."""
        params = {"limit": limit, "page": page}
        data = await self._request("messages", params=params)
        await self._send_json(ctx, data)

    @commands.group()
    async def stations(self, ctx: commands.Context):
        """Stations API commands."""
        pass

    @stations.command(name="list")
    async def stations_list(self, ctx: commands.Context):
        data = await self._request("stations")
        await self._send_json(ctx, data)


def setup(bot):
    bot.add_cog(Airframes(bot))
