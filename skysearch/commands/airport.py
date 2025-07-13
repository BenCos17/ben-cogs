"""
Airport commands for SkySearch cog
"""

import discord
import aiohttp
import asyncio
from discord.ext import commands
from redbot.core import commands as red_commands

from ..utils.api import APIManager
from ..utils.helpers import HelperUtils


class AirportCommands:
    """Airport-related commands for SkySearch."""
    
    def __init__(self, cog):
        self.cog = cog
        self.api = APIManager(cog)
        self.helpers = HelperUtils(cog)
    
    @red_commands.guild_only()
    @red_commands.group(name='airport', help='Command center for airport related commands')
    async def airport_group(self, ctx):
        """Command center for airport related commands"""
        # This will be handled by the main cog

    @red_commands.guild_only()
    @airport_group.command(name='info', help='Get information about an airport by its ICAO or IATA code.')
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
                embed.add_field(name="Coordinates", value=f"{lat}, {lon}", inline=True)
            
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

    @red_commands.guild_only()
    @airport_group.command(name='runway', help='Get runway information for an airport.')
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

    @red_commands.guild_only()
    @airport_group.command(name='navaid', help='Get navigational aids for an airport.')
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

    @red_commands.guild_only()
    @airport_group.command(name='forecast', help='Get weather forecast for an airport.')
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