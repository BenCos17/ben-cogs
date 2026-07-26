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
        """Get recent world-wide VIIRS NOAA-20 fire hotspots with interactive pages."""
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

                # Clean and isolate useful columns
                sub_df = df_area[['latitude', 'longitude', 'acq_date', 'confidence', 'frp']]
                
                # Split the dataframe into pages of 10 rows each
                rows_per_page = 10
                pages = []
                
                for i in range(0, total_fires, rows_per_page):
                    chunk = sub_df.iloc[i:i + rows_per_page]
                    page_text = (
                        f"**NASA FIRMS Fire Data** (Showing results {i+1} to {min(i+rows_per_page, total_fires)} of {total_fires})\n"
                        f"Transactions consumed: `{used_tokens}`\n"
                        f"```yaml\n{chunk.to_string()}```"
                    )
                    pages.append(page_text)

                await SimpleMenu(pages, use_select_menu=False).start(ctx)

            except Exception as e:
                await ctx.send(f"Failed to fetch fire data. Error: `{e}`")