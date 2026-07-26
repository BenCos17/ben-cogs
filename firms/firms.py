import discord
from redbot.core import commands
from redbot.core.utils.menus import SimpleMenu
import pandas as pd
import requests

class Firms(commands.Cog):
    """A cog to check NASA FIRMS active fire data via API."""

    def __init__(self, bot):
        self.bot = bot

    async def get_map_key(self):
        """Helper to fetch the firms map key from Red's shared API storage."""
        tokens = await self.bot.get_shared_api_tokens("firms")
        return tokens.get("map_key")

    async def get_transaction_count(self, map_key: str) -> int:
        url = f'https://firms.modaps.eosdis.nasa.gov/mapserver/mapkey_status/?MAP_KEY={map_key}'
        count = 0
        try:
            response = requests.get(url)
            data = response.json()
            df = pd.Series(data)
            count = int(df['current_transactions'])
        except Exception:
            pass
        return count

    @commands.group(name="firms")
    async def firms(self, ctx: commands.Context):
        """NASA FIRMS fire data commands."""
        pass

    @firms.command(name="status")
    async def firms_status(self, ctx: commands.Context):
        """Check your current NASA FIRMS API key status and transactions."""
        map_key = await self.get_map_key()
        if not map_key:
            return await ctx.send(
                "The NASA FIRMS `map_key` has not been set yet!\n"
                "Set it using: `[p]set api firms map_key,YOUR_KEY_HERE`"
            )

        url = f'https://firms.modaps.eosdis.nasa.gov/mapserver/mapkey_status/?MAP_KEY={map_key}'
        try:
            response = requests.get(url)
            data = response.json()
            df = pd.Series(data)
            output = f"```yaml\n{df.to_string()}```"
            await ctx.send(output)
        except Exception as e:
            await ctx.send(f"There is an issue with the query. Error: `{e}`")

    @firms.command(name="fires")
    async def firms_fires(self, ctx: commands.Context, days: int = 1):
        """Get recent world-wide VIIRS NOAA-20 fire hotspots using clean interactive embeds."""
        map_key = await self.get_map_key()
        if not map_key:
            return await ctx.send(
                "The NASA FIRMS `map_key` has not been set yet!\n"
                "Set it using: `[p]set api firms map_key,YOUR_KEY_HERE`"
            )

        area_url = f'https://firms.modaps.eosdis.nasa.gov/api/area/csv/{map_key}/VIIRS_NOAA20_NRT/world/{days}'
        
        async with ctx.typing():
            try:
                start_count = await self.get_transaction_count(map_key)
                df_area = pd.read_csv(area_url)
                end_count = await self.get_transaction_count(map_key)
                
                used_tokens = end_count - start_count
                total_fires = len(df_area)

                if total_fires == 0:
                    return await ctx.send("No fire data found for the given time frame.")

                # Group rows into chunks of 5 per page for a structured embed layout
                rows_per_page = 5
                pages = []
                total_pages = (total_fires + rows_per_page - 1) // rows_per_page

                for page_idx, i in enumerate(range(0, total_fires, rows_per_page), 1):
                    chunk = df_area.iloc[i:i + rows_per_page]
                    
                    embed = discord.Embed(
                        title="🔥 NASA FIRMS Worldwide Fire Detections",
                        description=f"Sensor: **VIIRS NOAA-20 (NRT)** | Timeframe: **Past {days} day(s)**",
                        color=discord.Color.orange()
                    )
                    embed.set_footer(
                        text=f"Page {page_idx} of {total_pages} • Total Fires Tracked: {total_fires:,} • API Cost: {used_tokens} tx"
                    )

                    for _, row in chunk.iterrows():
                        # Add helpful formatting symbols
                        time_icon = "☀️" if str(row.get('daynight')) == "D" else "🌙"
                        
                        field_title = f"{time_icon} Location: {row['latitude']}°, {row['longitude']}°"
                        field_value = (
                            f"• **Date/Time (UTC):** {row['acq_date']} at {row['acq_time']}\n"
                            f"• **Confidence:** `{row['confidence']}` | **FRP:** `{row['frp']} MW`\n"
                            f"• **Satellite:** {row['satellite']}"
                        )
                        embed.add_field(name=field_title, value=field_value, inline=False)

                    pages.append(embed)

                await SimpleMenu(pages, use_select_menu=False).start(ctx)

            except Exception as e:
                await ctx.send(f"Failed to fetch fire data. Error: `{e}`")