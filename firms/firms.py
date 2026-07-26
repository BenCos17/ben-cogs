import io
import discord
from redbot.core import commands
import pandas as pd
import requests

class Firms(cog := commands.Cog):
    """A cog to check NASA FIRMS active fire data via API."""

    def __init__(self, bot):
        self.bot = bot
        # Replace this or set it up via config/env vars if preferred
        self.MAP_KEY = 'c68db61c86cad79f0c2c208c952bdbb5'

    def get_transaction_count(self) -> int:
        url = f'https://firms.modaps.eosdis.nasa.gov/mapserver/mapkey_status/?MAP_KEY={self.MAP_KEY}'
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
        url = f'https://firms.modaps.eosdis.nasa.gov/mapserver/mapkey_status/?MAP_KEY={self.MAP_KEY}'
        try:
            response = requests.get(url)
            data = response.json()
            df = pd.Series(data)
            
            # Format dataframe into a readable string code block for Discord
            output = f"```yaml\n{df.to_string()}```"
            await ctx.send(output)
        except Exception as e:
            await ctx.send(f"There is an issue with the query. Error: `{e}`")

    @firms.command(name="fires")
    async def firms_fires(self, ctx: commands.Context, days: int = 1):
        """Get recent world-wide VIIRS NOAA-20 fire hotspots (Default: last 1 day)."""
        area_url = f'https://firms.modaps.eosdis.nasa.gov/api/area/csv/{self.MAP_KEY}/VIIRS_NOAA20_NRT/world/{days}'
        
        async with ctx.typing():
            try:
                start_count = self.get_transaction_count()
                df_area = pd.read_csv(area_url)
                end_count = self.get_transaction_count()
                
                used_tokens = end_count - start_count
                total_fires = len(df_area)

                # Send a summary text block back to Discord
                await ctx.send(
                    f"Successfully fetched **{total_fires}** fire hotspots worldwide "
                    f"using the VIIRS NOAA-20 sensor for the past {days} day(s).\n"
                    f"Transactions consumed: `{used_tokens}`"
                )
            except Exception as e:
                await ctx.send(f"Failed to fetch fire data. Error: `{e}`")