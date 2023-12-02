from redbot.core import commands
import aiohttp

class ITADCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.api_key = None

    @commands.command()
    @commands.is_owner()
    async def set_api_key(self, ctx, api_key: str):
        """Set the IsThereAnyDeal API key (Bot Owner Only)"""
        self.api_key = api_key
        await ctx.send("API key has been set.")

    @commands.command()
    async def get_api_key(self, ctx):
        """Get the currently set IsThereAnyDeal API key"""
        if self.api_key:
            await ctx.send(f"Current API key: {self.api_key}")
        else:
            await ctx.send("No API key has been set.")

    @commands.command()
    async def deal(self, ctx, *, game_name: str):
        """Get deal information for a game from IsThereAnyDeal.com"""
        if not self.api_key:
            await ctx.send("Please set the API key first using !set_api_key [api_key]")
            return

        headers = {
            'User-Agent': 'Your Discord Bot Name',
            'X-IsThereAnyDeal-Key': self.api_key
        }

        async with aiohttp.ClientSession() as session:
            encoded_game_name = aiohttp.helpers.quote(game_name)
            api_url = f'https://api.isthereanydeal.com/v02/game/plain/?key={encoded_game_name}'

            try:
                async with session.get(api_url, headers=headers) as response:
                    if response.status == 200:
                        data = await response.json()
                        if data['data']:
                            game_info = data['data']
                            await ctx.send(f"Game: {game_info['title']} - Cheapest price: {game_info['price']}")
                        else:
                            await ctx.send("No deals found for that game.")
                    else:
                        await ctx.send("Failed to fetch data from the API.")
            except Exception as e:
                await ctx.send(f"An error occurred: {str(e)}")


def setup(bot):
    bot.add_cog(ITADCog(bot))
