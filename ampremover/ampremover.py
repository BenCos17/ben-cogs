from redbot.core import commands, Config
import requests
import re
from discord import Embed

class AmputatorBot(commands.Cog):
    """A cog to convert AMP URLs to their canonical forms using AmputatorBot API.
    
    This cog provides functionality to automatically detect and convert AMP URLs in messages,
    with opt-in/opt-out capabilities for servers and users.
    """
    
    def __init__(self, bot):
        self.bot = bot
        self.config = Config.get_conf(self, identifier=492089091320446976)  # Use a unique identifier for your cog
        self.config.register_guild(opted_in=False)  # Register a guild-specific variable for opted-in status
        self.opted_in_users = set()

    async def initialize_config(self, guild):
        """Initialize the configuration for the server.
        
        Parameters
        ----------
        guild : discord.Guild
            The guild to initialize configuration for
            
        Returns
        -------
        bool
            The opted-in status for the guild
        """
        return await self.config.guild(guild).opted_in()

    @commands.group(name='amputator', invoke_without_command=True)
    async def amputator(self, ctx):
        """Base command for AmputatorBot operations.
        
        If no subcommand is provided, displays the available commands.
        
        Subcommands
        -----------
        optin : Opt-in to the service
        optout : Opt-out from the service
        convert : Convert AMP URLs in a message
        settings : Display current settings
        """
        await ctx.send("Use `[p]amputator optin`, `[p]amputator optout`, or `[p]amputator convert`.")

    @amputator.command(name='optin')
    async def opt_in(self, ctx):
        """Opt-in to use the AmputatorBot service"""
        if ctx.guild:
            await self.config.guild(ctx.guild).opted_in.set(True)
            await ctx.send("Successfully opted in to use the AmputatorBot service.")
        else:
            await ctx.send("This command cannot be used in DMs.")

    @amputator.command(name='optout')
    async def opt_out(self, ctx):
        """Opt-out from using the AmputatorBot service"""
        if ctx.guild:
            await self.config.guild(ctx.guild).opted_in.set(False)
            await ctx.send("Successfully opted out from using the AmputatorBot service.")
        else:
            await ctx.send("This command cannot be used in DMs.")

    @amputator.command(name='convert')
    async def convert_amp(self, ctx, *, message: str):
        """Converts AMP URLs to canonical URLs using AmputatorBot API"""
        urls = self.extract_urls(message)
        if not urls:
            await ctx.send("No URLs found in the message.")
            return

        canonical_links = self.fetch_canonical_links(urls)
        if canonical_links:
            if ctx.guild:  # If in a server, respond in the channel
                await ctx.send(f"Canonical URL(s): {'; '.join(canonical_links)}")
            else:  # If in DMs, respond in DMs
                await ctx.author.send(f"Canonical URL(s): {'; '.join(canonical_links)}")
        else:
            await ctx.send("No canonical URLs found.")

    def extract_urls(self, message: str):
        """Extracts URLs from a given message.
        
        Parameters
        ----------
        message : str
            The message to extract URLs from
            
        Returns
        -------
        list
            A list of URLs found in the message
            
        Note
        ----
        Uses regex pattern to match http:// and https:// URLs
        """
        return re.findall(r'(https?://\S+)', message)

    def fetch_canonical_links(self, urls):
        """Fetches canonical links for a list of URLs using the AmputatorBot API.
        
        Parameters
        ----------
        urls : list
            List of URLs to convert
            
        Returns
        -------
        list
            List of canonical URLs found
            
        Note
        ----
        Makes HTTP requests to AmputatorBot API (https://www.amputatorbot.com/api/v1/convert)
        Returns empty list if API calls fail or no canonical URLs are found
        """
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
        """Automatically detects and converts AMP links in messages.
        
        This event listener triggers when a message is sent in:
        - A guild channel where the server has opted in
        - DMs where the user has opted in
        
        Parameters
        ----------
        message : discord.Message
            The message to process
            
        Note
        ----
        Will only respond if valid canonical URLs are found
        """
        if message.guild:  # Check if the message is in a guild
            if await self.config.guild(message.guild).opted_in():  # Check if the server is opted in
                urls = self.extract_urls(message.content)
                if urls:
                    canonical_links = self.fetch_canonical_links(urls)
                    if canonical_links:
                        await message.channel.send(f"Canonical URL(s): {'; '.join(canonical_links)}")
        else:  # DM context
            if message.author.id in self.opted_in_users:  # Check if the user is opted in
                urls = self.extract_urls(message.content)
                if urls:
                    canonical_links = self.fetch_canonical_links(urls)
                    if canonical_links:
                        await message.author.send(f"Canonical URL(s): {'; '.join(canonical_links)}")

    @amputator.command(name='settings')
    async def show_settings(self, ctx):
        """Displays the current configuration settings for the AmputatorBot.
        
        Shows the opted-in status for the current guild using an embedded message.
        
        Parameters
        ----------
        ctx : commands.Context
            The command context
            
        Note
        ----
        Can only be used in guild channels, not in DMs
        Uses color-coding: Green for opted-in, Red for opted-out
        """
        if ctx.guild:  # Check if the command is invoked in a guild
            opted_in = await self.config.guild(ctx.guild).opted_in()  # Get opted-in status
            status_color = "✅" if opted_in else "❌"  # Use checkmark for Yes and cross for No
            status_text = "Opted In: " + (f"{status_color} Yes" if opted_in else f"{status_color} No")  # Create status text
            
            embed = Embed(title=f"Settings for {ctx.guild.name}", color=0x00ff00 if opted_in else 0xff0000)  # Green for Yes, Red for No
            embed.add_field(name="Status", value=status_text, inline=False)  # Add status field
            embed.set_footer(text="Use [p]amputator for more commands.")  # Add a footer for additional context
            
            await ctx.send(embed=embed)  # Send the embed message
        else:  # DM context
            await ctx.send("This command cannot be used in DMs.")