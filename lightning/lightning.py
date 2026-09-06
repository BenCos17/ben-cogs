"""Lightning tracking cog for Redbot with multi-API support."""
import discord
from redbot.core import commands, Config
from datetime import datetime
from typing import Optional, Literal

from .services import (
    BlitzortungService,
    WeatherAPIService,
    OpenWeatherMapService,
)
from .services.map_parser import MapParser

class Lightning(commands.Cog):
    """Track and display lightning strike statistics from multiple free APIs."""

    def __init__(self, bot):
        self.bot = bot
        self.config = Config.get_conf(self, identifier=492089091320446976, force_registration=True)
        
        # Register default settings
        self.config.register_guild(
            strikes=0,
            last_strike_time=None,
            strike_log=[],
            api_provider="weatherapi",
            owm_api_key="",
            weatherapi_key="",
            tracked_locations=[]
        )
        self.config.register_user(
            strikes_triggered=0
        )
        
        # Initialize services
        self.services = {
            "weatherapi": WeatherAPIService(),
            "owm": OpenWeatherMapService(),
            "blitzortung": BlitzortungService(),
        }

    @commands.group(invoke_without_command=True)
    @commands.guild_only()
    async def lightning(self, ctx: commands.Context):
        """Lightning tracking commands."""
        await ctx.send_help(ctx.command)

    @lightning.command(name="setprovider")
    @commands.admin_or_permissions(manage_guild=True)
    @commands.guild_only()
    async def set_provider(self, ctx: commands.Context, provider: Literal["weatherapi", "owm", "blitzortung"]):
        """
        Set which API to use for lightning tracking.
        
        Options:
        - weatherapi: Free, requires API key, weather-based
        - owm: OpenWeatherMap, requires free API key, weather-based
        - blitzortung: Free, no key needed, real-time lightning detection
        """
        await self.config.guild(ctx.guild).api_provider.set(provider)
        
        info = {
            "weatherapi": "WeatherAPI (requires free key from weatherapi.com)",
            "owm": "OpenWeatherMap (requires free key from openweathermap.org)",
            "blitzortung": "Blitzortung (free, no key needed - real-time strikes)"
        }
        
        embed = discord.Embed(
            title="✓ Provider Set",
            description=f"Now using: {info.get(provider, provider)}",
            color=discord.Color.green()
        )
        await ctx.send(embed=embed)

    @lightning.command(name="setkey")
    @commands.admin_or_permissions(manage_guild=True)
    @commands.guild_only()
    async def set_api_key(self, ctx: commands.Context, api_key: str):
        """
        Set the API key for the current provider.
        
        For WeatherAPI: Get at https://www.weatherapi.com/
        For OpenWeatherMap: Get at https://openweathermap.org/api
        """
        provider = await self.config.guild(ctx.guild).api_provider()
        
        if provider == "weatherapi":
            await self.config.guild(ctx.guild).weatherapi_key.set(api_key)
            service = "WeatherAPI"
        elif provider == "owm":
            await self.config.guild(ctx.guild).owm_api_key.set(api_key)
            service = "OpenWeatherMap"
        else:
            await ctx.send("❌ Blitzortung doesn't require an API key. Use `[p]lightning setprovider` to switch providers.")
            return
        
        embed = discord.Embed(
            title="✓ API Key Set",
            description=f"{service} API key configured for this server.",
            color=discord.Color.green()
        )
        await ctx.send(embed=embed)

    async def fetch_weatherapi(self, lat: float, lon: float, api_key: str) -> dict:
        """Fetch data from WeatherAPI.com"""
        service = self.services["weatherapi"]
        return await service.fetch(lat, lon, api_key=api_key)

    async def fetch_openweathermap(self, lat: float, lon: float, api_key: str) -> dict:
        """Fetch data from OpenWeatherMap"""
        service = self.services["owm"]
        return await service.fetch(lat, lon, api_key=api_key)

    async def fetch_blitzortung(self, lat: float, lon: float, radius_km: int = 25) -> dict:
        """Fetch data from Blitzortung (real-time lightning strikes)"""
        service = self.services["blitzortung"]
        return await service.fetch(lat, lon, radius_km=radius_km)

    async def get_lightning_data(self, guild_id: int, lat: float, lon: float) -> dict:
        """Get lightning data from configured provider."""
        provider = await self.config.guild_from_id(guild_id).api_provider()
        
        if provider == "weatherapi":
            api_key = await self.config.guild_from_id(guild_id).weatherapi_key()
            if not api_key:
                return {"error": "WeatherAPI key not set. Use `[p]lightning setkey <key>`"}
            return await self.fetch_weatherapi(lat, lon, api_key)
        
        elif provider == "owm":
            api_key = await self.config.guild_from_id(guild_id).owm_api_key()
            if not api_key:
                return {"error": "OpenWeatherMap key not set. Use `[p]lightning setkey <key>`"}
            return await self.fetch_openweathermap(lat, lon, api_key)
        
        elif provider == "blitzortung":
            return await self.fetch_blitzortung(lat, lon)
        
        return {"error": "Unknown provider"}

    @lightning.command(name="check")
    @commands.guild_only()
    async def check_lightning(self, ctx: commands.Context, latitude: float, longitude: float, label: str = ""):
        """
        Check for lightning at a specific location using the configured API.
        
        Parameters:
            latitude: Location latitude
            longitude: Location longitude
            label: Optional name for the location (e.g., "My City")
        """
        async with ctx.typing():
            data = await self.get_lightning_data(ctx.guild.id, latitude, longitude)
        
        if data is None or data.get("error"):
            error_msg = data.get("error", "Failed to fetch data") if data else "Failed to fetch data"
            await ctx.send(f"❌ {error_msg}")
            return
        
        provider = await self.config.guild(ctx.guild).api_provider()
        location_name = label if label else f"{latitude}, {longitude}"
        
        # Use the service's display method
        service = self.services.get(provider)
        if service:
            embed = service.display_data(data, location_name)
            await ctx.send(embed=embed)
        else:
            await ctx.send("❌ Unknown provider configured")

    @lightning.command(name="map")
    @commands.guild_only()
    async def check_lightning_map(self, ctx: commands.Context, *, map_url: str):
        """
        Check for lightning at a location from a Google Maps link.
        
        Parameters:
            map_url: Google Maps URL (e.g., https://maps.google.com/?q=40.7128,-74.0060)
        
        Supported formats:
        - https://maps.google.com/?q=40.7128,-74.0060
        - https://www.google.com/maps/place/40.7128,-74.0060
        - https://www.google.com/maps/@40.7128,-74.0060,15z
        """
        # Parse the map URL
        coords = MapParser.parse_maps_url(map_url)
        
        if coords is None:
            embed = discord.Embed(
                title="❌ Invalid Map Link",
                description="Could not extract coordinates from the provided Google Maps link.",
                color=discord.Color.red()
            )
            embed.add_field(
                name="Supported Formats",
                value="```\nhttps://maps.google.com/?q=LAT,LNG\nhttps://www.google.com/maps/@LAT,LNG,15z\nhttps://www.google.com/maps/place/LAT,LNG\n```",
                inline=False
            )
            await ctx.send(embed=embed)
            return
        
        latitude, longitude = coords
        location_name = MapParser.format_location_name(map_url)
        
        # If no location name extracted, use coordinates
        if not location_name:
            location_name = f"{latitude}, {longitude}"
        
        async with ctx.typing():
            data = await self.get_lightning_data(ctx.guild.id, latitude, longitude)
        
        if data is None or data.get("error"):
            error_msg = data.get("error", "Failed to fetch data") if data else "Failed to fetch data"
            await ctx.send(f"❌ {error_msg}")
            return
        
        provider = await self.config.guild(ctx.guild).api_provider()
        
        # Use the service's display method
        service = self.services.get(provider)
        if service:
            embed = service.display_data(data, location_name)
            await ctx.send(embed=embed)
        else:
            await ctx.send("❌ Unknown provider configured")

    @lightning.command(name="strike")
    @commands.guild_only()
    async def strike(self, ctx: commands.Context, intensity: Optional[int] = None):
        """
        Manually record a lightning strike (for fun/games).
        
        Parameters:
            intensity: Intensity of the strike (1-10). Defaults to random.
        """
        if intensity is None:
            import random
            intensity = random.randint(1, 10)
        else:
            intensity = max(1, min(10, intensity))
        
        # Update guild stats
        async with self.config.guild(ctx.guild).all() as guild_data:
            guild_data["strikes"] += 1
            guild_data["last_strike_time"] = datetime.now().isoformat()
            guild_data["strike_log"].append({
                "user": ctx.author.name,
                "intensity": intensity,
                "time": datetime.now().isoformat()
            })
        
        # Update user stats
        async with self.config.user(ctx.author).all() as user_data:
            user_data["strikes_triggered"] += 1
        
        # Create visual representation
        power_bar = "⚡" * intensity + "░" * (10 - intensity)
        
        embed = discord.Embed(
            title="⛈️ Lightning Strike Recorded!",
            description=f"**Intensity: {power_bar}** ({intensity}/10)",
            color=discord.Color.gold(),
            timestamp=datetime.now()
        )
        embed.set_author(name=ctx.author.display_name, icon_url=ctx.author.display_avatar.url)
        
        guild_data = await self.config.guild(ctx.guild).all()
        user_data = await self.config.user(ctx.author).all()
        
        embed.add_field(name="Total Strikes (Guild)", value=guild_data["strikes"], inline=True)
        embed.add_field(name="Your Strikes", value=user_data["strikes_triggered"], inline=True)
        
        await ctx.send(embed=embed)

    @lightning.command(name="stats")
    @commands.guild_only()
    async def stats(self, ctx: commands.Context, user: Optional[discord.Member] = None):
        """
        View lightning statistics.
        
        Parameters:
            user: User to check stats for. Defaults to yourself.
        """
        if user is None:
            user = ctx.author
        
        user_strikes = await self.config.user(user).strikes_triggered()
        guild_data = await self.config.guild(ctx.guild).all()
        
        embed = discord.Embed(
            title="⚡ Lightning Statistics",
            color=discord.Color.gold(),
            timestamp=datetime.now()
        )
        
        embed.add_field(name="Guild Total Strikes", value=guild_data["strikes"], inline=False)
        embed.add_field(name=f"{user.display_name}'s Strikes", value=user_strikes, inline=False)
        
        if guild_data["last_strike_time"]:
            embed.add_field(
                name="Last Strike",
                value=guild_data["last_strike_time"],
                inline=False
            )
        
        # Top strikers from log
        if guild_data["strike_log"]:
            from collections import Counter
            strikers = Counter(strike["user"] for strike in guild_data["strike_log"])
            top_3 = strikers.most_common(3)
            top_strikers_text = "\n".join([f"{i+1}. {name}: {count}" for i, (name, count) in enumerate(top_3)])
            embed.add_field(name="Top Strikers", value=top_strikers_text, inline=False)
        
        embed.set_thumbnail(url="https://cdn-icons-png.flaticon.com/512/992/992566.png")
        await ctx.send(embed=embed)

    @lightning.command(name="reset")
    @commands.admin_or_permissions(manage_guild=True)
    @commands.guild_only()
    async def reset(self, ctx: commands.Context):
        """Reset all lightning statistics for this server."""
        await self.config.guild(ctx.guild).clear()
        
        embed = discord.Embed(
            title="⚡ Statistics Reset",
            description="All lightning statistics for this server have been cleared.",
            color=discord.Color.green()
        )
        await ctx.send(embed=embed)

    @lightning.command(name="log")
    @commands.guild_only()
    async def log(self, ctx: commands.Context, limit: int = 10):
        """
        View recent lightning strikes.
        
        Parameters:
            limit: Number of recent strikes to display (default 10, max 50).
        """
        limit = max(1, min(50, limit))
        
        guild_data = await self.config.guild(ctx.guild).all()
        strikes = guild_data["strike_log"][-limit:]
        
        if not strikes:
            await ctx.send("No lightning strikes recorded yet.")
            return
        
        log_text = "\n".join([
            f"**{strike['user']}** - Intensity: {strike['intensity']}/10 - {strike['time']}"
            for strike in reversed(strikes)
        ])
        
        embed = discord.Embed(
            title=f"⛈️ Recent Lightning Strikes (Last {len(strikes)})",
            description=log_text,
            color=discord.Color.gold()
        )
        await ctx.send(embed=embed)


async def setup(bot):
    """Load the Lightning cog."""
    await bot.add_cog(Lightning(bot))
