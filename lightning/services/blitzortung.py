"""Blitzortung service for real-time lightning tracking."""
from .base import LightningService
import discord
import aiohttp
import asyncio


class BlitzortungService(LightningService):
    """Blitzortung service for real-time crowdsourced lightning detection."""

    async def fetch(self, lat: float, lon: float, radius_km: int = 25) -> dict:
        """Fetch data from Blitzortung (real-time lightning strikes)"""
        session = await self.get_session()
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

    def format_display_name(self) -> str:
        """Return display name."""
        return "Blitzortung"

    def display_data(self, data: dict, location_name: str):
        """Format data as Discord embed."""
        strikes = data.get("strikes", [])

        embed = discord.Embed(
            title="⚡ Real-Time Lightning Strikes (Blitzortung)",
            color=discord.Color.gold() if strikes else discord.Color.blue(),
        )
        embed.add_field(name="Location", value=location_name, inline=False)

        if strikes:
            embed.add_field(
                name=f"Strikes Detected: {len(strikes)}",
                value=f"⚠️ **{len(strikes)}** active strike(s) in the area!",
                inline=False,
            )

            strikes_text = ""
            for i, strike in enumerate(strikes[:5], 1):
                lat = strike.get("lat", "N/A")
                lon = strike.get("lon", "N/A")
                strikes_text += f"{i}. Lat: {lat}, Lon: {lon}\n"

            embed.add_field(name="Recent Strikes", value=strikes_text[:1024], inline=False)
        else:
            embed.add_field(name="Status", value="✓ No recent lightning detected", inline=False)

        embed.set_footer(text="Data from Blitzortung (crowdsourced, real-time)")
        return embed
