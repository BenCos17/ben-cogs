from redbot.core import commands, Config
import requests
import re

class AmputatorBot(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.config = bot.get_cog('Config')  # Access the Config cog
        self.opted_in_users = set()
        self.opted_in_servers = set()

    async def initialize_config(self):
        """Initialize the configuration for the server."""
        self.opted_in_servers = await self.config.opted_in_servers()  # Load opted-in servers from config

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
            await self.config.opted_in_servers.set(self.opted_in_servers)  # Save to config
            await ctx.send(f"Server {ctx.guild.name} has opted in to use the AmputatorBot service.")

    @amputator.command(name='optout')
    async def opt_out(self, ctx):
        """Opt-out from using the AmputatorBot service"""
        if ctx.guild is None:  # DM context
            self.opted_in_users.discard(ctx.author.id)
            await ctx.send(f"{ctx.author.mention}, you have opted out from using the AmputatorBot service in DMs.")
        else:  # Server context
            self.opted_in_servers.discard(ctx.guild.id)
            await self.config.opted_in_servers.set(self.opted_in_servers)  # Save to config
            await ctx.send(f"Server {ctx.guild.name} has opted out from using the AmputatorBot service.")

    @amputator.command(name='convert')
    async def convert_amp(self, ctx, *, message: str):
        """Converts AMP URLs to canonical URLs using AmputatorBot API"""
        urls = self.extract_urls(message)
        if not urls:
            await ctx.send("No URLs found in the message.")
            return

        canonical_links = self.fetch_canonical_links(urls)
        if canonical_links:
            await ctx.send(f"Canonical URL(s): {'; '.join(canonical_links)}")
        else:
            await ctx.send("No canonical URLs found.")

    def extract_urls(self, message: str):
        """Extracts URLs from a given message"""
        return re.findall(r'(https?://\S+)', message)

    def fetch_canonical_links(self, urls):
        """Fetches canonical links for a list of URLs using the AmputatorBot API"""
        canonical_links = []
        for url in urls:
            api_url = f"https://www.amputatorbot.com/api/v1/convert?gac=true&md=3&q={url}"
            response = requests.get(api_url)
            
            if response.status_code == 200:
                data = response.json()
                if 'error' in data:
                    continue
                else:
                    links = [link['canonical']['url'] for link in data if link['canonical']]
                    canonical_links.extend(links)
            else:
                continue
        return canonical_links

    @commands.Cog.listener()
    async def on_message(self, message):
        """Detects links in messages and responds if the server has opted in"""
        if message.guild and message.guild.id in self.opted_in_servers:
            urls = self.extract_urls(message.content)
            if urls:
                canonical_links = self.fetch_canonical_links(urls)
                if canonical_links:
                    await message.channel.send(f"Canonical URL(s): {'; '.join(canonical_links)}")
#                else:
#                    await message.channel.send("No canonical URLs found.")
#commented out as it doesn't work for now 
#It'll be used for a future system 