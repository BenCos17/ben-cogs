from redbot.core import commands
import requests
import re

class AmputatorBot(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.opted_in_users = set()
        self.opted_in_servers = set()

    @commands.group(name='amputator', invoke_without_command=True)
    async def amputator(self, ctx):
        """Base command for AmputatorBot operations"""
        await ctx.send("Use `[p]amputator optin`, `[p]amputator optout`, or `[p]amputator convert`.")

    @amputator.command(name='optin')
    async def opt_in(self, ctx):
        """Opt-in to use the AmputatorBot service"""
        if ctx.guild is None:  # DM context
            self.opted_in_users.add(ctx.author.id)
            await ctx.send(f"{ctx.author.mention}, you have opted in to use the AmputatorBot service in DMs.")
        else:  # Server context
            self.opted_in_servers.add(ctx.guild.id)
            await ctx.send(f"Server {ctx.guild.name} has opted in to use the AmputatorBot service.")

    @amputator.command(name='optout')
    async def opt_out(self, ctx):
        """Opt-out from using the AmputatorBot service"""
        if ctx.guild is None:  # DM context
            self.opted_in_users.discard(ctx.author.id)
            await ctx.send(f"{ctx.author.mention}, you have opted out from using the AmputatorBot service in DMs.")
        else:  # Server context
            self.opted_in_servers.discard(ctx.guild.id)
            await ctx.send(f"Server {ctx.guild.name} has opted out from using the AmputatorBot service.")

    @amputator.command(name='convert')
    async def convert_amp(self, ctx, *, message: str):
        """Converts AMP URLs to canonical URLs using AmputatorBot API"""
        urls = re.findall(r'(https?://\S+)', message)
        if not urls:
            await ctx.send("No URLs found in the message.")
            return

        if ctx.guild is not None and ctx.guild.id not in self.opted_in_servers:
            # If the server hasn't opted in, do not respond
            return

        canonical_links = []
        for url in urls:
            api_url = f"https://www.amputatorbot.com/api/v1/convert?gac=true&md=3&q={url}"
            response = requests.get(api_url)
            
            if response.status_code == 200:
                data = response.json()
                if 'error' in data:
                    await ctx.send(f"Error for {url}: {data['error']}")
                else:
                    links = [link['canonical']['url'] for link in data if link['canonical']]
                    canonical_links.extend(links)
            else:
                await ctx.send(f"Failed to fetch data from AmputatorBot API for {url}. Status code: {response.status_code}")

        if canonical_links:
            await ctx.send(f"Canonical URL(s): {'; '.join(canonical_links)}")
        else:
            await ctx.send("No canonical URLs found.")
