import re
from redbot.core import commands, Config
from redbot.core.bot import Red
from redbot.core.commands import Context
from discord import Message
from typing import Optional

class Amazon(commands.Cog):
    """Cog for handling Amazon affiliate links."""

    def __init__(self, bot: Red):
        self.bot = bot
        self.config = Config.get_conf(self, identifier=492089091320446976, force_registration=True)
        default_guild = {"affiliate_tag": "yourtag-20", "enabled": False}
        self.config.register_guild(**default_guild)

        # Compile the regex pattern once and reuse it
        self.amazon_link_pattern = re.compile(
            r"https?://(?:www\.)?(amazon\.[a-z]{2,3}(?:\.[a-z]{2})?)/(?:.*/)?(?:dp|gp/product)/(\w+/)?(\w{10})(?:[/?#]|$)"
        )

    def create_affiliate_link(self, domain: str, product_id: str, affiliate_tag: str) -> str:
        """Create an affiliate link based on domain, product ID, and affiliate tag."""
        return f"https://{domain}/dp/{product_id}?tag={affiliate_tag}"

    @commands.Cog.listener()
    async def on_message(self, message: Message) -> None:
        if message.author.bot or not message.guild:
            return
        
        if "amazon" not in message.content.lower():
            return

        # Check if the cog is enabled for this server
        enabled = await self.config.guild(message.guild).enabled()
        if not enabled:
            return

        # Find all Amazon product links in the message
        matches = self.amazon_link_pattern.finditer(message.content)
        
        affiliate_links = []
        affiliate_tag = await self.config.guild(message.guild).affiliate_tag()
        
        for match in matches:
            domain = match.group(1)
            product_id = match.group(3)
            if domain and product_id:
                # Generate affiliate link using the helper method
                affiliate_link = self.create_affiliate_link(domain, product_id, affiliate_tag)
                affiliate_links.append(affiliate_link)
        
        if affiliate_links:
            response = "Here are the Amazon affiliate links:\n" + "\n".join(affiliate_links)
            await message.channel.send(response)

    @commands.group(invoke_without_command=True)
    @commands.admin_or_permissions(manage_guild=True)
    async def amazon(self, ctx: Context) -> None:
        """Commands for managing Amazon affiliate settings."""
        await ctx.send_help('amazon')
    
    @amazon.command(name="set_tag")
    @commands.admin_or_permissions(manage_guild=True)
    async def set_tag(self, ctx: Context, tag: str) -> None:
        """Set the Amazon affiliate tag for this server."""
        if not tag:
            await ctx.send("Invalid affiliate tag.")
            return
        
        try:
            await self.config.guild(ctx.guild).affiliate_tag.set(tag)
            await ctx.send(f"Affiliate tag set to: {tag} for this server.")
        except Exception as e:
            await ctx.send("There was an error setting the affiliate tag. Please try again later.")
            # Optionally log the error for debugging
            print(f"Error setting affiliate tag: {e}")
    
    @amazon.command(name="show_tag")
    @commands.admin_or_permissions(manage_guild=True)
    async def show_tag(self, ctx: Context) -> None:
        """Show the current Amazon affiliate tag for this server."""
        current_tag = await self.config.guild(ctx.guild).affiliate_tag()
        await ctx.send(f"The current affiliate tag for this server is: {current_tag}")

    @amazon.command()
    @commands.admin_or_permissions(manage_guild=True)
    async def enable(self, ctx: Context) -> None:
        """Enable Amazon affiliate link handling for this server."""
        await self.config.guild(ctx.guild).enabled.set(True)
        await ctx.send("Amazon affiliate link handling has been enabled for this server.")

    @amazon.command()
    @commands.admin_or_permissions(manage_guild=True)
    async def disable(self, ctx: Context) -> None:
        """Disable Amazon affiliate link handling for this server."""
        await self.config.guild(ctx.guild).enabled.set(False)
        await ctx.send("Amazon affiliate link handling has been disabled for this server.")

    @amazon.command(name="current_tag")
    @commands.admin_or_permissions(manage_guild=True)
    async def current_tag(self, ctx: Context) -> None:
        """Display the current Amazon affiliate tag for this server."""
        current_tag = await self.config.guild(ctx.guild).affiliate_tag()
        if current_tag:
            await ctx.send(f"The current Amazon affiliate tag for this server is: {current_tag}")
        else:
            await ctx.send("No Amazon affiliate tag has been set for this server.")
