import discord
from discord.ext import commands
import aiohttp
from redbot.core import Config, commands, bank
from redbot.core.utils import AsyncIter
from redbot.core.utils.chat_formatting import box, humanize_list, pagify
from redbot.core.bot import Red

class Currency(commands.Cog):
    def __init__(self, bot: Red):
        self.bot = bot
        self.config = Config.get_conf(self, identifier=492089091320446976)
        default_global = {
            "base_url": "https://api.freecurrencyapi.com/v1/"
        }
        self.config.register_global(**default_global)

    async def red_get_api_key(self, api_key_name: str):
        return await self.bot.get_shared_api_tokens(api_key_name)

    @commands.command(name='currency')
    async def convert_currency(self, ctx, amount: float, from_currency: str, to_currency: str):
        api_tokens = await self.red_get_api_key("freecurrencyapi")
        api_key = api_tokens.get("api_key")
        if not api_key:
            await ctx.send("API key not set. Please set it using `[p]set api freecurrencyapi api_key,YOUR_API_KEY`")
            return
        base_url = await self.config.base_url()
        async with aiohttp.ClientSession() as session:
            url = f'{base_url}latest?apikey={api_key}&base_currency={from_currency}&currencies={to_currency}'
            async with session.get(url) as response:
                if response.status == 200:
                    data = await response.json()
                    rate = data['data'][to_currency]
                    converted_amount = amount * rate
                    await ctx.send(f'{amount} {from_currency} is equal to {converted_amount:.2f} {to_currency}')
                else:
                    await ctx.send('Failed to fetch currency data. Please try again later. Error code: {response.status}')

    @commands.command(name='rates')
    async def get_rates(self, ctx, base_currency: str):
        api_tokens = await self.red_get_api_key("freecurrencyapi")
        api_key = api_tokens.get("api_key")
        if not api_key:
            await ctx.send("API key not set. Please set it using `[p]set api freecurrencyapi api_key,YOUR_API_KEY`")
            return
        base_url = await self.config.base_url()
        async with aiohttp.ClientSession() as session:
            url = f'{base_url}latest?apikey={api_key}&base_currency={base_currency}'
            async with session.get(url) as response:
                if response.status == 200:
                    data = await response.json()
                    rates = data['data']
                    rates_message = '\n'.join([f'{currency}: {rate}' for currency, rate in rates.items()])
                    await ctx.send(f'Exchange rates for {base_currency}:\n{rates_message}')
                else:
                    await ctx.send('Failed to fetch currency data. Please try again later. Error code: {response.status}')
