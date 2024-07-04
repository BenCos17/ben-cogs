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
            "base_url": "https://api.freecurrencyapi.com/v1/",
        }
        self.config.register_global(**default_global)

    async def red_get_api_key(self):
        api_key = await self.bot.get_shared_api_tokens("freecurrencyapi")
        return api_key.get("api_key")

    @commands.command(name='currency')
    async def convert_currency(self, ctx, amount: float, from_currency: str, to_currency: str):
        api_key = await self.red_get_api_key()
        if not api_key:
            await ctx.send("API key not set. Please set it using `[p]set api freecurrencyapi api_key,YOUR_API_KEY`")
            return
        base_url = await self.config.base_url()
        url = f"{base_url}latest?apikey={api_key}&currencies={from_currency},{to_currency}"
        async with aiohttp.ClientSession() as session:
            try:
                async with session.get(url) as response:
                    if response.status == 422:
                        await ctx.send(f'Invalid currency code(s) provided: {from_currency}, {to_currency}. Please check the currency codes and try again.')
                        return
                    response.raise_for_status()
                    data = await response.json()
                    rates = data['data']
                    from_rate = rates[from_currency]
                    to_rate = rates[to_currency]
                    converted_amount = (amount / from_rate) * to_rate
                    await ctx.send(f'{amount} {from_currency} is equal to {converted_amount:.2f} {to_currency}')
            except Exception as e:
                await ctx.send(f'Failed to fetch currency data. Please try again later. Error: {str(e)}')

    @commands.command(name='rates')
    async def get_rates(self, ctx, base_currency: str):
        api_key = await self.red_get_api_key()
        if not api_key:
            await ctx.send("API key not set. Please set it using `[p]set api freecurrencyapi api_key,YOUR_API_KEY`")
            return
        base_url = await self.config.base_url()
        url = f"{base_url}latest?apikey={api_key}&base_currency={base_currency}"
        async with aiohttp.ClientSession() as session:
            try:
                async with session.get(url) as response:
                    if response.status == 422:
                        await ctx.send(f'Invalid base currency code provided: {base_currency}. Please check the currency code and try again.')
                        return
                    response.raise_for_status()
                    data = await response.json()
                    rates = data['data']
                    rates_message = '\n'.join([f'{currency}: {rate}' for currency, rate in rates.items()])
                    await ctx.send(f'Exchange rates for {base_currency}:\n{rates_message}')
            except Exception as e:
                await ctx.send(f'Failed to fetch currency data. Please try again later. Error: {str(e)}')
