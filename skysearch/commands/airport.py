"""
Airport commands for SkySearch cog
"""

import discord
import aiohttp
import asyncio
from redbot.core.utils.menus import menu, DEFAULT_CONTROLS

from ..utils.api import APIManager
from ..utils.helpers import HelperUtils
from redbot.core import commands
from redbot.core.i18n import Translator, cog_i18n

# Internationalization
_ = Translator("Skysearch", __file__)


@cog_i18n(_)
class AirportCommands:
    """Airport-related commands for SkySearch."""
    
    def __init__(self, cog):
        self.cog = cog
        self.api = APIManager(cog)
        self.helpers = HelperUtils(cog)
    
    async def airport_info(self, ctx, airport_code: str):
        """Get airport information by ICAO or IATA code."""
        airport_code = airport_code.upper()
        
        # Try to get airport data
        airport_data = await self.helpers.get_airport_data(airport_code)
        
        if airport_data:
            embed = discord.Embed(title=f"Airport Information - {airport_code}", color=0xfffffe)
            embed.set_thumbnail(url="https://www.beehive.systems/hubfs/Icon%20Packs/White/airplane.png")
            
            # Basic airport information
            name = airport_data.get('name', 'N/A')
            city = airport_data.get('city', 'N/A')
            country = airport_data.get('country', 'N/A')
            
            embed.add_field(name="Name", value=name, inline=True)
            embed.add_field(name="City", value=city, inline=True)
            embed.add_field(name="Country", value=country, inline=True)
            
            # Coordinates
            lat = airport_data.get('latitude', 'N/A')
            lon = airport_data.get('longitude', 'N/A')
            if lat != 'N/A' and lon != 'N/A':
                embed.add_field(name="Coordinates", value=f"{lat}, {lon}", inline=False)
            
            # Elevation
            elevation = airport_data.get('elevation', 'N/A')
            if elevation != 'N/A':
                embed.add_field(name="Elevation", value=f"{elevation} ft", inline=True)
            
            # Timezone
            timezone = airport_data.get('timezone', 'N/A')
            if timezone != 'N/A':
                embed.add_field(name="Timezone", value=timezone, inline=True)
            
            # Get airport image
            image_url = await self.helpers.get_airport_image(lat, lon)
            if image_url:
                embed.set_image(url=image_url)
            
            # Add view with buttons
            view = discord.ui.View()
            if lat != 'N/A' and lon != 'N/A':
                google_maps_url = f"https://www.google.com/maps?q={lat},{lon}"
                view.add_item(discord.ui.Button(label="View on Google Maps", emoji="🗺️", url=google_maps_url, style=discord.ButtonStyle.link))
            
            await ctx.send(embed=embed, view=view)
        else:
            embed = discord.Embed(title="Airport Not Found", description=f"No airport found with code {airport_code}.", color=0xff4545)
            await ctx.send(embed=embed)

    async def runway_info(self, ctx, airport_code: str):
        """Get runway information for an airport."""
        airport_code = airport_code.upper()
        
        # Get runway data
        runway_data = await self.helpers.get_runway_data(airport_code)
        
        if runway_data and runway_data.get('runways'):
            embed = discord.Embed(title=f"Runway Information - {airport_code}", color=0xfffffe)
            embed.set_thumbnail(url="https://www.beehive.systems/hubfs/Icon%20Packs/White/airplane.png")
            
            runways = runway_data['runways']
            for runway in runways:
                runway_name = runway.get('name', 'N/A')
                length = runway.get('length', 'N/A')
                width = runway.get('width', 'N/A')
                surface = runway.get('surface', 'N/A')
                
                runway_info = f"**Length:** {length} ft\n"
                runway_info += f"**Width:** {width} ft\n"
                runway_info += f"**Surface:** {surface}"
                
                embed.add_field(name=f"Runway {runway_name}", value=runway_info, inline=False)
            
            await ctx.send(embed=embed)
        else:
            embed = discord.Embed(title="No Runway Data", description=f"No runway information found for {airport_code}.", color=0xff4545)
            await ctx.send(embed=embed)

    async def navaid_info(self, ctx, airport_code: str):
        """Get navigational aids for an airport."""
        airport_code = airport_code.upper()
        
        # Get navaid data
        navaid_data = await self.helpers.get_navaid_data(airport_code)
        
        if navaid_data and navaid_data.get('navaids'):
            embed = discord.Embed(title=f"Navigational Aids - {airport_code}", color=0xfffffe)
            embed.set_thumbnail(url="https://www.beehive.systems/hubfs/Icon%20Packs/White/airplane.png")
            
            navaids = navaid_data['navaids']
            for navaid in navaids:
                navaid_name = navaid.get('name', 'N/A')
                navaid_type = navaid.get('type', 'N/A')
                frequency = navaid.get('frequency', 'N/A')
                
                navaid_info = f"**Type:** {navaid_type}\n"
                navaid_info += f"**Frequency:** {frequency}"
                
                embed.add_field(name=navaid_name, value=navaid_info, inline=True)
            
            await ctx.send(embed=embed)
        else:
            embed = discord.Embed(title="No Navaid Data", description=f"No navigational aid information found for {airport_code}.", color=0xff4545)
            await ctx.send(embed=embed)

    async def weather_forecast(self, ctx, airport_code: str):
        """Get weather forecast for an airport."""
        airport_code = airport_code.upper()
        
        # Get airport coordinates first
        airport_data = await self.helpers.get_airport_data(airport_code)
        
        if airport_data:
            lat = airport_data.get('latitude', 'N/A')
            lon = airport_data.get('longitude', 'N/A')
            
            if lat != 'N/A' and lon != 'N/A':
                # Get weather forecast
                weather_data = await self.helpers.get_weather_forecast(lat, lon)
                
                if weather_data:
                    embed = discord.Embed(title=f"Weather Forecast - {airport_code}", color=0xfffffe)
                    embed.set_thumbnail(url="https://www.beehive.systems/hubfs/Icon%20Packs/White/airplane.png")
                    
                    # Current weather
                    current = weather_data.get('current', {})
                    if current:
                        temp = current.get('temp', 'N/A')
                        condition = current.get('condition', {}).get('text', 'N/A')
                        wind_speed = current.get('wind_kph', 'N/A')
                        humidity = current.get('humidity', 'N/A')
                        
                        embed.add_field(name="Current Weather", value=f"**Temperature:** {temp}°C\n**Condition:** {condition}\n**Wind:** {wind_speed} km/h\n**Humidity:** {humidity}%", inline=False)
                    
                    # Forecast
                    forecast = weather_data.get('forecast', {}).get('forecastday', [])
                    if forecast:
                        for day in forecast[:3]:  # Show next 3 days
                            date = day.get('date', 'N/A')
                            max_temp = day.get('day', {}).get('maxtemp_c', 'N/A')
                            min_temp = day.get('day', {}).get('mintemp_c', 'N/A')
                            condition = day.get('day', {}).get('condition', {}).get('text', 'N/A')
                            
                            day_info = f"**Max:** {max_temp}°C\n**Min:** {min_temp}°C\n**Condition:** {condition}"
                            embed.add_field(name=date, value=day_info, inline=True)
                    
                    await ctx.send(embed=embed)
                else:
                    embed = discord.Embed(title="Weather Data Unavailable", description=f"Weather forecast data is not available for {airport_code}.", color=0xff4545)
                    await ctx.send(embed=embed)
            else:
                embed = discord.Embed(title="Invalid Coordinates", description=f"Could not get coordinates for {airport_code}.", color=0xff4545)
                await ctx.send(embed=embed)
        else:
            embed = discord.Embed(title="Airport Not Found", description=f"No airport found with code {airport_code}.", color=0xff4545)
            await ctx.send(embed=embed) 

    async def paginate_embed(self, ctx, embeds):
        await menu(ctx, embeds, DEFAULT_CONTROLS)

    async def forecast(self, ctx, code: str):
        code_type = 'icao' if len(code) == 4 else 'iata' if len(code) == 3 else None
        if not code_type:
            await ctx.send(embed=discord.Embed(title="Error", description="Invalid ICAO or IATA code. ICAO codes are 4 characters long and IATA codes are 3 characters long.", color=0xff4545))
            return

        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(f"https://airport-data.com/api/ap_info.json?{code_type}={code}") as response1:
                    data1 = await response1.json()
                    latitude, longitude = data1.get('latitude'), data1.get('longitude')
                    country_code = data1.get('country_code')
                    airport_name = data1.get('name')
                    if not latitude or not longitude:
                        await ctx.send(embed=discord.Embed(title="Error", description="Could not fetch latitude and longitude for the provided code.", color=0xff4545))
                        return

                if country_code == 'US':
                    # US logic (NOAA/NWS)
                    async with session.get(f"https://api.weather.gov/points/{latitude},{longitude}") as response2:
                        data2 = await response2.json()
                        forecast_url = data2.get('properties', {}).get('forecast')
                        if not forecast_url:
                            await ctx.send(embed=discord.Embed(title="Error", description="Could not fetch forecast URL.", color=0xff4545))
                            return

                    async with session.get(forecast_url) as response3:
                        data3 = await response3.json()
                        periods = data3.get('properties', {}).get('periods')
                        if not periods:
                            await ctx.send(embed=discord.Embed(title="Error", description="Could not fetch forecast details.", color=0xff4545))
                            return

                    combined_pages = []
                    for period in periods:
                        timeemoji = "☀️" if period.get('isDaytime') else "🌙"
                        description = f"{timeemoji} {period['name']}"
                        embed = discord.Embed(title=f"Weather forecast for {code.upper()}", description=description, color=0xfffffe)
                        temperature = period['temperature']
                        temperature_unit = period['temperatureUnit']
                        # Determine the emoji based on temperature
                        if temperature_unit == 'F':
                            if temperature >= 90:
                                emoji = '🔥'  # Hot
                            elif temperature <= 32:
                                emoji = '❄️'  # Cold
                            else:
                                emoji = '🌡️'  # Moderate
                        else:  # Assuming Celsius
                            if temperature >= 32:
                                emoji = '🔥'  # Hot
                            elif temperature <= 0:
                                emoji = '❄️'  # Cold
                            else:
                                emoji = '🌡️'  # Moderate
                        embed.add_field(name="Temperature", value=f"{emoji} **`{temperature}° {temperature_unit}`**", inline=True)
                        wind_speed = period['windSpeed']
                        wind_direction = period['windDirection']
                        # Determine the emoji based on wind speed
                        try:
                            speed_value = int(wind_speed.split()[0])
                            if speed_value >= 30:
                                wind_emoji = '💨'  # Strong wind
                            elif speed_value >= 15:
                                wind_emoji = '🌬️'  # Moderate wind
                            else:
                                wind_emoji = '🍃'  # Light wind
                        except ValueError:
                            wind_emoji = '🍃'  # Default to light wind if parsing fails
                        # Determine the emoji based on wind direction
                        direction_emoji = {
                            'N': '⬆️', 'NNE': '⬆️↗️', 'NE': '↗️', 'ENE': '↗️➡️', 'E': '➡️', 'ESE': '➡️↘️', 'SE': '↘️',
                            'SSE': '↘️⬇️', 'S': '⬇️', 'SSW': '⬇️↙️', 'SW': '↙️', 'WSW': '↙️⬅️', 'W': '⬅️',
                            'WNW': '⬅️↖️', 'NW': '↖️', 'NNW': '↖️⬆️'
                        }.get(wind_direction, '❓')
                        embed.add_field(name="Wind speed", value=f"{wind_emoji} **`{wind_speed}`**", inline=True)
                        embed.add_field(name="Wind direction", value=f"{direction_emoji} **`{wind_direction}`**", inline=True)
                        if 'relativeHumidity' in period and period['relativeHumidity']['value'] is not None:
                            embed.add_field(name="Humidity", value=f"**`{period['relativeHumidity']['value']}%`**", inline=True)
                        if 'probabilityOfPrecipitation' in period and period['probabilityOfPrecipitation']['value'] is not None:
                            embed.add_field(name="Chance of precipitation", value=f"**`{period['probabilityOfPrecipitation']['value']}%`**", inline=True)
                        if 'dewpoint' in period and period['dewpoint']['value'] is not None:
                            dewpoint_celsius = period['dewpoint']['value']
                            dewpoint_fahrenheit = (dewpoint_celsius * 9/5) + 32
                            embed.add_field(name="Dewpoint", value=f"**`{dewpoint_fahrenheit:.1f}°F`**", inline=True)
                        embed.add_field(name="Forecast", value=f"**`{period['detailedForecast']}`**", inline=False)
                        combined_pages.append(embed)
                    await self.paginate_embed(ctx, combined_pages)
                else:
                    # Non-US logic (OpenWeatherMap)
                    data = await self.cog.api.get_openweathermap_forecast(latitude, longitude)
                    if not data or 'list' not in data:
                        await ctx.send(embed=discord.Embed(title="Error", description="Could not fetch forecast from OpenWeatherMap.", color=0xff4545))
                        return
                    city = data.get('city', {}).get('name', code.upper())
                    country = data.get('city', {}).get('country', '')
                    combined_pages = []
                    for entry in data['list']:
                        dt_txt = entry.get('dt_txt', '')
                        main = entry.get('main', {})
                        weather = entry.get('weather', [{}])[0]
                        wind = entry.get('wind', {})
                        temp = main.get('temp')
                        feels_like = main.get('feels_like')
                        humidity = main.get('humidity')
                        description = weather.get('description', '').capitalize()
                        icon = weather.get('icon', '')
                        wind_speed = wind.get('speed')
                        wind_deg = wind.get('deg')
                        # Emoji logic for temperature
                        if temp is not None:
                            if temp >= 32:
                                emoji = '🔥'
                            elif temp <= 0:
                                emoji = '❄️'
                            else:
                                emoji = '🌡️'
                        else:
                            emoji = '🌡️'
                        # Wind speed emoji
                        try:
                            speed_value = float(wind_speed) if wind_speed is not None else 0
                            if speed_value >= 13.4:  # ~30 mph
                                wind_emoji = '💨'
                            elif speed_value >= 6.7:  # ~15 mph
                                wind_emoji = '🌬️'
                            else:
                                wind_emoji = '🍃'
                        except Exception:
                            wind_emoji = '🍃'
                        # Wind direction emoji
                        def deg_to_compass(deg):
                            if deg is None:
                                return '❓'
                            dirs = ['⬆️', '⬆️↗️', '↗️', '↗️➡️', '➡️', '➡️↘️', '↘️', '↘️⬇️', '⬇️', '⬇️↙️', '↙️', '↙️⬅️', '⬅️', '⬅️↖️', '↖️', '↖️⬆️']
                            ix = int((float(deg) + 11.25) / 22.5) % 16
                            return dirs[ix]
                        direction_emoji = deg_to_compass(wind_deg)
                        embed = discord.Embed(
                            title=f"Weather forecast for {airport_name or code.upper()}",
                            description=dt_txt,
                            color=0xfffffe
                        )
                        if icon:
                            embed.set_thumbnail(url=f"https://openweathermap.org/img/wn/{icon}@2x.png")
                        embed.add_field(name="Description", value=description, inline=False)
                        embed.add_field(name="Temperature", value=f"{emoji} **`{temp}°C (feels like {feels_like}°C)`**", inline=True)
                        embed.add_field(name="Wind speed", value=f"{wind_emoji} **`{wind_speed} m/s`**", inline=True)
                        embed.add_field(name="Wind direction", value=f"{direction_emoji} **`{wind_deg}°`**", inline=True)
                        embed.add_field(name="Humidity", value=f"**`{humidity}%`**", inline=True)
                        embed.add_field(name="Forecast", value=f"**`{description}`**", inline=False)
                        combined_pages.append(embed)
                    await self.paginate_embed(ctx, combined_pages)
        except Exception as e:
            await ctx.send(embed=discord.Embed(title="Error", description=str(e), color=0xff4545)) 

    @commands.is_owner()
    @commands.command(name="setowmkey")
    async def setowmkey(self, ctx, api_key: str):
        """Set the OpenWeatherMap API key."""
        await self.cog.config.openweathermap_api.set(api_key)
        await ctx.send("OpenWeatherMap API key set.")

    @commands.is_owner()
    @commands.command(name="owmkey")
    async def owmkey(self, ctx):
        """Show the current OpenWeatherMap API key (partially masked)."""
        key = await self.cog.config.openweathermap_api()
        if key:
            await ctx.send(f"OpenWeatherMap API key: `{key[:4]}{'*' * (len(key) - 8)}{key[-4:]}`")
        else:
            await ctx.send("No OpenWeatherMap API key set.")

    @commands.is_owner()
    @commands.command(name="clearowmkey")
    async def clearowmkey(self, ctx):
        """Clear the OpenWeatherMap API key."""
        await self.cog.config.openweathermap_api.set(None)
        await ctx.send("OpenWeatherMap API key cleared.") 