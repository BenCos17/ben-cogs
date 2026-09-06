"""WeatherAPI.com service for lightning tracking."""
from .base import LightningService
import discord


class WeatherAPIService(LightningService):
    """WeatherAPI.com service for weather-based lightning detection."""

    async def fetch(self, lat: float, lon: float, api_key: str = "") -> dict:
        """Fetch data from WeatherAPI.com"""
        if not api_key:
            return {"error": "WeatherAPI key not set. Use `[p]lightning setkey <key>`"}

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

    def format_display_name(self) -> str:
        """Return display name."""
        return "WeatherAPI"

    def display_data(self, data: dict, location_name: str):
        """Format data as Discord embed."""
        current = data.get("current", {})
        condition = current.get("condition", {})
        is_thunderstorm = "thunder" in condition.get("text", "").lower()

        embed = discord.Embed(
            title="⚡ Lightning Check (WeatherAPI)",
            color=discord.Color.gold() if is_thunderstorm else discord.Color.blue(),
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
        return embed
