from redbot.core import commands, Config
import requests
import re

class AmputatorBot(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.config = Config.get_conf(self, identifier=492089091320446976)  # Use a unique identifier for your cog
        self.config.register_guild(opted_in=False)  # Register a guild-specific variable for opted-in status
        self.opted_in_users = set()

    async def initialize_config(self):
        """Initialize the configuration for the server."""
        # Load opted-in status from config
        self.opted_in_servers = await self.config.guild(ctx.guild).opted_in()  # Load opted-in status for the guild

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
            await self.config.guild(ctx.guild).opted_in.set(True)  # Save to config
            await ctx.send(f"Server {ctx.guild.name} has opted in to use the AmputatorBot service.")

    @amputator.command(name='optout')
    async def opt_out(self, ctx):
        """Opt-out from using the AmputatorBot service"""
        if ctx.guild is None:  # DM context
            self.opted_in_users.discard(ctx.author.id)
            await ctx.send(f"{ctx.author.mention}, you have opted out from using the AmputatorBot service in DMs.")
        else:  # Server context
            await self.config.guild(ctx.guild).opted_in.set(False)  # Save to config
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
        if message.guild and await self.config.guild(message.guild).opted_in():  # Check if the server is opted in
            urls = self.extract_urls(message.content)
            if urls:
                canonical_links = self.fetch_canonical_links(urls)
                if canonical_links:
                    await message.channel.send(f"Canonical URL(s): {'; '.join(canonical_links)}")

    @amputator.command(name='settings')
    async def show_settings(self, ctx):
        """Displays the current configuration settings for the AmputatorBot."""
        opted_in = await self.config.guild(ctx.guild).opted_in()  # Get opted-in status
        settings_message = f"Current settings for {ctx.guild.name}:\n"
        settings_message += f"Opted In: {'Yes' if opted_in else 'No'}"
        await ctx.send(settings_message)