"""
Airport commands for SkySearch cog
"""

import discord
import aiohttp
import io
import asyncio
from discord.ext import commands


class AirportCommands:
    """Airport-related commands for SkySearch."""
    
    def __init__(self, cog):
        self.cog = cog
    
    async def paginate_embed(self, ctx, pages):
        """Paginate through multiple embeds."""
        message = await ctx.send(embed=pages[0])
        await message.add_reaction("⬅️")
        await message.add_reaction("❌")
        await message.add_reaction("➡️")

        def check(reaction, user):
            return user == ctx.author and str(reaction.emoji) in ["⬅️", "❌", "➡️"]

        i = 0
        reaction = None
        while True:
            if str(reaction) == "⬅️":
                if i > 0:
                    i -= 1
                    await message.edit(embed=pages[i])
            elif str(reaction) == "➡️":
                if i < len(pages) - 1:
                    i += 1
                    await message.edit(embed=pages[i])
            elif str(reaction) == "❌":
                await message.delete()
                break
            try:
                reaction, user = await self.cog.bot.wait_for("reaction_add", timeout=30.0, check=check)
                await asyncio.sleep(1)
                await message.remove_reaction(reaction, user)
            except asyncio.TimeoutError:
                await message.clear_reactions()
                break

    @commands.guild_only()
    @commands.group(name='airport', help='Command center for airport related commands')
    async def airport_group(self, ctx):
        """Command center for airport related commands"""
        # This will be handled by the main cog

    @commands.guild_only()
    @airport_group.command(name='info')
    async def airportinfo(self, ctx, code: str = None):
        """Query airport information by ICAO or IATA code."""
        if code is None:
            embed = discord.Embed(title="Error", description="Please provide an ICAO or IATA code.", color=0xff4545)
            await ctx.send(embed=embed)
            return

        # Determine if the code is ICAO or IATA based on length
        if len(code) == 4:
            code_type = 'icao'
        elif len(code) == 3:
            code_type = 'iata'
        else:
            embed = discord.Embed(title="Error", description="Invalid ICAO or IATA code. ICAO codes are 4 characters long and IATA codes are 3 characters long.", color=0xff4545)
            await ctx.send(embed=embed)
            return

        try:
            async with ctx.typing():
                url1 = f"https://airport-data.com/api/ap_info.json?{code_type}={code}"
                async with aiohttp.ClientSession() as session:
                    async with session.get(url1) as response1:
                        data1 = await response1.json()
                
                if 'error' in data1 or not data1 or 'name' not in data1:
                    embed = discord.Embed(title="Error", description="No airport found with the provided code.", color=0xff4545)
                    await ctx.send(embed=embed)
                    return

                embed = discord.Embed(title=f"{data1.get('name', 'Unknown Airport')}", color=0xfffffe)

                # Check for OpenAI API key and use it to generate a summary if available
                openai_api_key = await self.cog.bot.get_shared_api_tokens("openai")
                if openai_api_key and 'api_key' in openai_api_key:
                    openai_api_key = openai_api_key['api_key']
                    airport_name = data1.get('name', 'Unknown Airport')
                    openai_payload = {
                        "model": "gpt-4o-mini",
                        "messages": [
                            {
                                "role": "system",
                                "content": "You are an AI summarizer inside a Discord bot feature. Produce text without titles or headings, and use markdown for styling like - bulletpoints where appropriate. Don't mention terrorist attacks or other world terrorism events. Don't mention the airport's name, ICAO or IATA."
                            },
                            {
                                "role": "user",
                                "content": f"Generate a summary of the airport named {airport_name}. Include 3 links as bulletpoints where I can read more about the airport"
                            }
                        ]
                    }
                    headers = {
                        "Content-Type": "application/json",
                        "Authorization": f"Bearer {openai_api_key}"
                    }
                    async with aiohttp.ClientSession() as session:
                        async with session.post("https://api.openai.com/v1/chat/completions", headers=headers, json=openai_payload) as openai_response:
                            if openai_response.status == 200:
                                openai_data = await openai_response.json()
                                summary = openai_data.get('choices', [{}])[0].get('message', {}).get('content', '')
                                embed.description = summary
                                embed.set_footer(text="Summary generated using AI, check factual accuracy")

                googlemaps_tokens = await self.cog.bot.get_shared_api_tokens("googlemaps")
                google_street_view_api_key = googlemaps_tokens.get("api_key", "YOUR_API_KEY")
                
                file = None  # Initialize file to None to handle cases where no image is available
                if google_street_view_api_key != "YOUR_API_KEY":
                    street_view_base_url = "https://maps.googleapis.com/maps/api/staticmap"
                    street_view_params = {
                        "size": "1920x1080", # Width x Height
                        "zoom": "12",
                        "scale": "2", 
                        "center": f"{data1['latitude']},{data1['longitude']}",  # Latitude and Longitude as comma-separated string
                        "maptype": "hybrid",
                        "key": google_street_view_api_key
                    }
                    async with aiohttp.ClientSession() as session:
                        async with session.get(street_view_base_url, params=street_view_params) as street_view_response:
                            if street_view_response.status == 200:
                                # Save the raw binary that the API returns as an image to set in embed.set_image
                                street_view_image_url = "attachment://street_view_image.png"
                                embed.set_image(url=street_view_image_url)
                                street_view_image_stream = io.BytesIO(await street_view_response.read())
                                file = discord.File(fp=street_view_image_stream, filename="street_view_image.png")
                            else:
                                # Handle the error accordingly, e.g., log it or send a message to the user
                                pass

                view = discord.ui.View(timeout=180)  # Initialize view outside of the else block
                if 'icao' in data1:
                    embed.add_field(name='ICAO', value=f"{data1['icao']}", inline=True)
                if 'iata' in data1:
                    embed.add_field(name='IATA', value=f"{data1['iata']}", inline=True)
                if 'country_code' in data1:
                    embed.add_field(name='Country code', value=f":flag_{data1['country_code'].lower()}: {data1['country_code']}", inline=True)
                if 'location' in data1:
                    embed.add_field(name='Location', value=f"{data1['location']}", inline=True)
                if 'country' in data1:
                    embed.add_field(name='Country', value=f"{data1['country']}", inline=True)
                if 'longitude' in data1:
                    embed.add_field(name='Longitude', value=f"{data1['longitude']}", inline=True)
                if 'latitude' in data1:
                    embed.add_field(name='Latitude', value=f"{data1['latitude']}", inline=True)
                
                # Check if 'link' is in data1 and add it to the view
                if 'link' in data1:
                    link = data1['link']
                    if not (link.startswith('http://') or link.startswith('https://')):
                        link = 'https://airport-data.com' + link
                    # URL button
                    view_airport = discord.ui.Button(label=f"More info about {data1['icao']}", url=link, style=discord.ButtonStyle.link)
                    view.add_item(view_airport)

            # Send the message with the embed, view, and file (if available)
            await ctx.send(embed=embed, view=view, file=file)
        except Exception as e:
            embed = discord.Embed(title="Error", description=str(e), color=0xff4545)
            await ctx.send(embed=embed)

    @commands.guild_only()
    @airport_group.command(name='runway')
    async def runwayinfo(self, ctx, code: str):
        """Query runway information by ICAO code."""
        if len(code) != 4:
            if len(code) == 3:
                code_type = 'iata'
            else:
                embed = discord.Embed(title="Error", description="Invalid ICAO or IATA code. ICAO codes are 4 characters long and IATA codes are 3 characters long.", color=0xff4545)
                await ctx.send(embed=embed)
                return
        else:
            code_type = 'icao'

        try:
            if code_type == 'iata':
                url1 = f"https://airport-data.com/api/ap_info.json?iata={code}"
                async with aiohttp.ClientSession() as session:
                    async with session.get(url1) as response1:
                        data1 = await response1.json()
                        if 'icao' in data1:
                            code = data1['icao']
                        else:
                            embed = discord.Embed(title="Error", description="No ICAO code found for the provided IATA code.", color=0xff4545)
                            await ctx.send(embed=embed)
                            return

            api_token = await self.cog.bot.get_shared_api_tokens("airportdbio")
            if api_token and 'api_token' in api_token:
                url2 = f"https://airportdb.io/api/v1/airport/{code}?apiToken={api_token['api_token']}"
                async with aiohttp.ClientSession() as session:
                    async with session.get(url2) as response2:
                        data2 = await response2.json()

                if 'error' in data2:
                    error_message = data2['error']
                    if len(error_message) > 1024:
                        error_message = error_message[:1021] + "..."
                    embed = discord.Embed(title="Error", description=error_message, color=0xff4545)
                    await ctx.send(embed=embed)
                elif not data2 or 'name' not in data2:
                    embed = discord.Embed(title="Error", description="No airport found with the provided code.", color=0xff4545)
                    await ctx.send(embed=embed)
                else:
                    combined_pages = []
                    if 'runways' in data2:
                        embed = discord.Embed(title=f"Runway information for {code.upper()}", color=0xfffffe)
                        embed.set_thumbnail(url="https://www.beehive.systems/hubfs/Icon%20Packs/White/layers.png")
                        runways = data2['runways']
                        for runway in runways:
                            if 'id' in runway:
                                embed.add_field(name="Runway ID", value=f"**`{runway['id']}`**", inline=True)

                            if 'surface' in runway:
                                embed.add_field(name="Surface", value=f"**`{runway['surface']}`**", inline=True)

                            if 'length_ft' in runway and 'width_ft' in runway:
                                embed.add_field(name="Dimensions", value=f"**`{runway['length_ft']}ft long`\n`{runway['width_ft']}ft wide`**", inline=True)

                            if 'le_ident' in runway or 'he_ident' in runway:
                                ils_value = ""
                                if 'le_ident' in runway:
                                    ils_info = runway.get('le_ils', {})
                                    ils_freq = ils_info.get('freq', 'N/A')
                                    ils_course = ils_info.get('course', 'N/A')
                                    ils_value += f"**{runway['le_ident']}** *`{ils_freq} MHz @ {ils_course}°`*\n"
                                if 'he_ident' in runway:
                                    ils_info = runway.get('he_ils', {})
                                    ils_freq = ils_info.get('freq', 'N/A')
                                    ils_course = ils_info.get('course', 'N/A')
                                    ils_value += f"**{runway['he_ident']}** *`{ils_freq} MHz @ {ils_course}°`*\n"
                                embed.add_field(name="Landing assistance", value=ils_value.strip(), inline=True)

                            runway_status = ":white_check_mark: **`Open`**" if str(runway.get('closed', 0)) == '0' else ":x: **`Closed`**"
                            embed.add_field(name="Runway status", value=runway_status, inline=True)

                            lighted_status = ":bulb: **`Lighted`**" if str(runway.get('lighted', 0)) == '1' else ":x: **`Not Lighted`**"
                            embed.add_field(name="Lighting", value=lighted_status, inline=True)

                            combined_pages.append(embed)
                            embed = discord.Embed(title=f"Runway information for {code.upper()}", color=0xfffffe)
                            embed.set_thumbnail(url="https://www.beehive.systems/hubfs/Icon%20Packs/White/layers.png")

                    await self.paginate_embed(ctx, combined_pages)
            else:
                embed = discord.Embed(title="Error", description="API token for airportdb.io not configured.", color=0xff4545)
                await ctx.send(embed=embed)
        except Exception as e:
            embed = discord.Embed(title="Error", description=str(e), color=0xff4545)
            await ctx.send(embed=embed)

    @commands.guild_only()
    @airport_group.command(name='navaid')
    async def navaidinfo(self, ctx, code: str):
        """Query navaid information by ICAO code."""
        if len(code) != 4:
            if len(code) == 3:
                code_type = 'iata'
            else:
                embed = discord.Embed(title="Error", description="Invalid ICAO or IATA code. ICAO codes are 4 characters long and IATA codes are 3 characters long.", color=0xff4545)
                await ctx.send(embed=embed)
                return
        else:
            code_type = 'icao'

        try:
            if code_type == 'iata':
                url1 = f"https://airport-data.com/api/ap_info.json?iata={code}"
                async with aiohttp.ClientSession() as session:
                    async with session.get(url1) as response1:
                        data1 = await response1.json()
                        if 'icao' in data1:
                            code = data1['icao']
                        else:
                            embed = discord.Embed(title="Error", description="No ICAO code found for the provided IATA code.", color=0xff4545)
                            await ctx.send(embed=embed)
                            return

            api_token = await self.cog.bot.get_shared_api_tokens("airportdbio")
            if api_token and 'api_token' in api_token:
                url = f"https://airportdb.io/api/v1/airport/{code}?apiToken={api_token['api_token']}"
                async with aiohttp.ClientSession() as session:
                    async with session.get(url) as response:
                        data = await response.json()

                if 'error' in data:
                    error_message = data['error']
                    if len(error_message) > 1024:
                        error_message = error_message[:1021] + "..."
                    embed = discord.Embed(title="Error", description=error_message, color=0xff4545)
                    await ctx.send(embed=embed)
                elif not data or 'name' not in data:
                    embed = discord.Embed(title="Error", description="No airport found with the provided code.", color=0xff4545)
                    await ctx.send(embed=embed)
                else:
                    combined_pages = []
                    if 'navaids' in data:
                        embed = discord.Embed(title=f"Navigational aids at {code.upper()}", color=0xfffffe)
                        embed.set_thumbnail(url="https://www.beehive.systems/hubfs/Icon%20Packs/White/navigate.png")
                        navaids = data['navaids']
                        for navaid in navaids:
                            if 'ident' in navaid and navaid['ident']:
                                embed.add_field(name="Ident", value=f"**`{navaid['ident']}`**", inline=True)

                            if 'name' in navaid and navaid['name']:
                                embed.add_field(name="Name", value=f"**`{navaid['name']}`**", inline=True)

                            if 'type' in navaid and navaid['type']:
                                embed.add_field(name="Type", value=f"**`{navaid['type']}`**", inline=True)

                            if 'frequency_khz' in navaid and navaid['frequency_khz']:
                                embed.add_field(name="Frequency", value=f"**`{navaid['frequency_khz']}khz`**", inline=True)

                            if 'latitude_deg' in navaid and 'longitude_deg' in navaid and navaid['latitude_deg'] and navaid['longitude_deg']:
                                latitude = "{:.6f}".format(float(navaid['latitude_deg']))
                                longitude = "{:.6f}".format(float(navaid['longitude_deg']))
                                embed.add_field(name="Coordinates", value="**`{}°, {}°`**".format(latitude, longitude), inline=True)

                            if 'elevation_ft' in navaid and navaid['elevation_ft']:
                                embed.add_field(name="Elevation", value=f"**`{navaid['elevation_ft']}ft`**", inline=True)

                            if 'usageType' in navaid and navaid['usageType']:
                                embed.add_field(name="Usage", value=f"**`{navaid['usageType']}`**", inline=True)

                            if 'power' in navaid and navaid['power']:
                                embed.add_field(name="Signal power", value=f"**`{navaid['power']}`**", inline=True)

                            if 'associated_airport' in navaid and navaid['associated_airport']:
                                embed.add_field(name="Airport", value=f"**`{navaid['associated_airport']}`**", inline=True)

                            combined_pages.append(embed)
                            embed = discord.Embed(title=f"Navaid information for {code.upper()}", color=0xfffffe)
                            embed.set_thumbnail(url="https://www.beehive.systems/hubfs/Icon%20Packs/White/navigate.png")

                    await self.paginate_embed(ctx, combined_pages)
            else:
                embed = discord.Embed(title="Error", description="API token for airportdb.io not configured.", color=0xff4545)
                await ctx.send(embed=embed)
        except Exception as e:
            embed = discord.Embed(title="Error", description=str(e), color=0xff4545)
            await ctx.send(embed=embed)

    @commands.guild_only()
    @airport_group.command(name='forecast', help='Get the weather for an airport by ICAO or IATA code.')
    async def get_forecast(self, ctx, code: str):
        """Fetch the latitude and longitude of an airport via IATA or ICAO code, then show the forecast"""
        code_type = 'icao' if len(code) == 4 else 'iata' if len(code) == 3 else None
        if not code_type:
            await ctx.send(embed=discord.Embed(title="Error", description="Invalid ICAO or IATA code. ICAO codes are 4 characters long and IATA codes are 3 characters long.", color=0xff4545))
            return

        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(f"https://airport-data.com/api/ap_info.json?{code_type}={code}") as response1:
                    data1 = await response1.json()
                    latitude, longitude = data1.get('latitude'), data1.get('longitude')
                    if not latitude or not longitude:
                        await ctx.send(embed=discord.Embed(title="Error", description="Could not fetch latitude and longitude for the provided code.", color=0xff4545))
                        return
                    if data1.get('country_code') != 'US':
                        await ctx.send(embed=discord.Embed(title="Error", description="Weather forecasts are currently only available for airports in the United States.", color=0xff4545))
                        return

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
                description = f" # {timeemoji} {period['name']}"
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
                    'N': '⬆️', 'NNE': '⬆️↗️', 'NE': '↗️', 'ENE': '↗️➡️', 'E': '➡️',
                    'ESE': '➡️↘️', 'SE': '↘️', 'SSE': '↘️⬇️', 'S': '⬇️', 'SSW': '⬇️↙️',
                    'SW': '↙️', 'WSW': '↙️⬅️', 'W': '⬅️', 'WNW': '⬅️↖️', 'NW': '↖️', 'NNW': '↖️⬆️'
                }.get(wind_direction, '❓')  # Default to question mark if direction is unknown
                
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

        except Exception as e:
            await ctx.send(embed=discord.Embed(title="Error", description=str(e), color=0xff4545)) 