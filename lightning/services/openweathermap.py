"""OpenWeatherMap service for lightning tracking."""
from .base import LightningService
import discord


class OpenWeatherMapService(LightningService):
    """OpenWeatherMap service for weather-based lightning detection."""

    async def fetch(self, lat: float, lon: float, api_key: str = "") -> dict:
        """Fetch data from OpenWeatherMap"""
        if not api_key:
            return {"error": "OpenWeatherMap key not set. Use `[p]lightning setkey <key>`"}

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

    def format_display_name(self) -> str:
        """Return display name."""
        return "OpenWeatherMap"

    def display_data(self, data: dict, location_name: str):
        """Format data as Discord embed."""
        weather_list = data.get("weather", [])
        is_thunderstorm = any(w["id"] >= 200 and w["id"] <= 232 for w in weather_list)

        embed = discord.Embed(
            title="⚡ Lightning Check (OpenWeatherMap)",
            color=discord.Color.gold() if is_thunderstorm else discord.Color.blue(),
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
        return embed
