from redbot.core import commands
import requests

class AmputatorBot(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.opted_in_users = set()

    @commands.group(name='amputator', invoke_without_command=True)
    async def amputator(self, ctx):
        """Base command for AmputatorBot operations"""
        await ctx.send("Use `[p]amputator optin`, `[p]amputator optout`, or `[p]amputator convert`.")

    @amputator.command(name='optin')
    async def opt_in(self, ctx):
        """Opt-in to use the AmputatorBot service"""
        self.opted_in_users.add(ctx.author.id)
        await ctx.send(f"{ctx.author.mention}, you have opted in to use the AmputatorBot service.")

    @amputator.command(name='optout')
    async def opt_out(self, ctx):
        """Opt-out from using the AmputatorBot service"""
        self.opted_in_users.discard(ctx.author.id)
        await ctx.send(f"{ctx.author.mention}, you have opted out from using the AmputatorBot service.")

    @amputator.command(name='convert')
    async def convert_amp(self, ctx, *, url: str):
        """Converts AMP URL to canonical URL using AmputatorBot API"""
        if ctx.author.id not in self.opted_in_users:
            await ctx.send(f"{ctx.author.mention}, you need to opt-in to use this service. Use the `[p]amputator optin` command.")
            return

        api_url = f"https://www.amputatorbot.com/api/v1/convert?gac=true&md=3&q={url}"
        response = requests.get(api_url)
        
        if response.status_code == 200:
            data = response.json()
            if 'error' in data:
                await ctx.send(f"Error: {data['error']}")
            else:
                canonical_links = [link['canonical']['url'] for link in data if link['canonical']]
                if canonical_links:
                    await ctx.send(f"Canonical URL(s): {'; '.join(canonical_links)}")
                else:
                    await ctx.send("No canonical URLs found.")
        else:
            await ctx.send(f"Failed to fetch data from AmputatorBot API. Status code: {response.status_code}")




