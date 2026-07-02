"""Lightning tracking cog for Redbot with multi-API support."""
import discord
from redbot.core import commands, Config
from datetime import datetime
from typing import Optional, Literal
import aiohttp

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
        self.session = None

    async def get_session(self):
        """Get or create aiohttp session."""
        if not self.session:
            self.session = aiohttp.ClientSession()
        return self.session

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
        session = await self.get_session()
        url = f"https://api.weatherapi.com/v1/current.json?key={api_key}&q={lat},{lon}&aqi=no"
        
        try:
            async with session.get(url) as resp:
                if resp.status == 200:
                    return await resp.json()
                else:
                    return {"error": f"WeatherAPI returned status {resp.status}"}
        except Exception as e:
            return {"error": f"WeatherAPI error: {str(e)}"}

    async def fetch_openweathermap(self, lat: float, lon: float, api_key: str) -> dict:
        """Fetch data from OpenWeatherMap"""
        session = await self.get_session()
        url = f"https://api.openweathermap.org/data/2.5/weather?lat={lat}&lon={lon}&appid={api_key}"
        
        try:
            async with session.get(url) as resp:
                if resp.status == 200:
                    return await resp.json()
                else:
                    return {"error": f"OpenWeatherMap returned status {resp.status}"}
        except Exception as e:
            return {"error": f"OpenWeatherMap error: {str(e)}"}

    async def fetch_blitzortung(self, lat: float, lon: float, radius_km: int = 25) -> dict:
        """Fetch data from Blitzortung (real-time lightning strikes)"""
        session = await self.get_session()
        # Try the correct Blitzortung endpoint
        url = f"https://api.blitzortung.org/webservice/json/3/strikes/region/{lat}/{lon}/{radius_km}"
        
        try:
            async with session.get(url, timeout=aiohttp.ClientTimeout(total=10)) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    # Blitzortung returns the data directly or in a "strikes" field
                    if isinstance(data, list):
                        return {"strikes": data}
                    return data
                else:
                    return {"error": f"Blitzortung returned status {resp.status}"}
        except asyncio.TimeoutError:
            return {"error": "Blitzortung request timed out"}
        except Exception as e:
            return {"error": f"Blitzortung error: {str(e)}"}

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
        
        if provider == "blitzortung":
            await self._display_blitzortung(ctx, data, location_name)
        elif provider == "weatherapi":
            await self._display_weatherapi(ctx, data, location_name)
        elif provider == "owm":
            await self._display_openweathermap(ctx, data, location_name)

    async def _display_blitzortung(self, ctx, data: dict, location_name: str):
        """Display Blitzortung real-time lightning data."""
        strikes = data.get("strikes", [])
        
        embed = discord.Embed(
            title="⚡ Real-Time Lightning Strikes (Blitzortung)",
            color=discord.Color.gold() if strikes else discord.Color.blue(),
            timestamp=datetime.now()
        )
        embed.add_field(name="Location", value=location_name, inline=False)
        
        if strikes:
            embed.add_field(name=f"Strikes Detected: {len(strikes)}", value=f"⚠️ **{len(strikes)}** active strike(s) in the area!", inline=False)
            
            strikes_text = ""
            for i, strike in enumerate(strikes[:5], 1):
                lat = strike.get("lat", "N/A")
                lon = strike.get("lon", "N/A")
                strikes_text += f"{i}. Lat: {lat}, Lon: {lon}\n"
            
            embed.add_field(name="Recent Strikes", value=strikes_text[:1024], inline=False)
        else:
            embed.add_field(name="Status", value="✓ No recent lightning detected", inline=False)
        
        embed.set_footer(text="Data from Blitzortung (crowdsourced, real-time)")
        await ctx.send(embed=embed)

    async def _display_weatherapi(self, ctx, data: dict, location_name: str):
        """Display WeatherAPI weather data."""
        current = data.get("current", {})
        condition = current.get("condition", {})
        is_thunderstorm = "thunder" in condition.get("text", "").lower()
        
        embed = discord.Embed(
            title="⚡ Lightning Check (WeatherAPI)",
            color=discord.Color.gold() if is_thunderstorm else discord.Color.blue(),
            timestamp=datetime.now()
        )
        embed.add_field(name="Location", value=location_name, inline=False)
        embed.add_field(name="Weather", value=condition.get("text", "N/A"), inline=True)
        embed.add_field(name="Temperature", value=f"{current.get('temp_c', 'N/A')}°C", inline=True)
        embed.add_field(name="Humidity", value=f"{current.get('humidity', 'N/A')}%", inline=True)
        embed.add_field(name="Wind Speed", value=f"{current.get('wind_kph', 'N/A')} kph", inline=True)
        embed.add_field(name="Cloud Cover", value=f"{current.get('cloud', 'N/A')}%", inline=True)
        embed.add_field(name="Pressure", value=f"{current.get('pressure_mb', 'N/A')} mb", inline=True)
        
        if is_thunderstorm:
            embed.add_field(name="⚠️ Thunderstorm Active", value="Lightning possible in this area!", inline=False)
        else:
            embed.add_field(name="✓ No Thunderstorm", value="No lightning currently detected.", inline=False)
        
        embed.set_footer(text="Data from WeatherAPI")
        await ctx.send(embed=embed)

    async def _display_openweathermap(self, ctx, data: dict, location_name: str):
        """Display OpenWeatherMap weather data."""
        weather_list = data.get("weather", [])
        is_thunderstorm = any(w["id"] >= 200 and w["id"] <= 232 for w in weather_list)
        
        embed = discord.Embed(
            title="⚡ Lightning Check (OpenWeatherMap)",
            color=discord.Color.gold() if is_thunderstorm else discord.Color.blue(),
            timestamp=datetime.now()
        )
        embed.add_field(name="Location", value=location_name, inline=False)
        embed.add_field(name="Weather", value=weather_list[0].get("description", "N/A") if weather_list else "N/A", inline=True)
        embed.add_field(name="Temperature", value=f"{data.get('main', {}).get('temp', 'N/A')}K", inline=True)
        embed.add_field(name="Humidity", value=f"{data.get('main', {}).get('humidity', 'N/A')}%", inline=True)
        embed.add_field(name="Wind Speed", value=f"{data.get('wind', {}).get('speed', 'N/A')} m/s", inline=True)
        embed.add_field(name="Cloud Cover", value=f"{data.get('clouds', {}).get('all', 'N/A')}%", inline=True)
        embed.add_field(name="Pressure", value=f"{data.get('main', {}).get('pressure', 'N/A')} hPa", inline=True)
        
        if is_thunderstorm:
            embed.add_field(name="⚠️ Thunderstorm Active", value="Lightning possible in this area!", inline=False)
        else:
            embed.add_field(name="✓ No Thunderstorm", value="No lightning currently detected.", inline=False)
        
        embed.set_footer(text="Data from OpenWeatherMap")
        await ctx.send(embed=embed)

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
