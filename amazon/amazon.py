import re
from redbot.core import commands, Config

class Amazon(commands.Cog):
    """Cog for handling Amazon affiliate links."""

    def __init__(self, bot):
        self.bot = bot
        self.config = Config.get_conf(self, identifier=1234567890, force_registration=True)
        default_guild = {"affiliate_tag": "yourtag-20", "enabled": False}
        self.config.register_guild(**default_guild)

        # Compile the regex pattern once and reuse it
        self.amazon_link_pattern = re.compile(
            r"https?://(?:www\.)?(amazon\.[a-z]{2,3}(?:\.[a-z]{2})?)/(?:.*/)?(?:dp|gp/product)/(\w+/)?(\w{10})(?:[/?#]|$)"
        )

    def create_affiliate_link(self, domain, product_id, affiliate_tag):
        """Create an affiliate link based on domain, product ID, and affiliate tag."""
        return f"https://{domain}/dp/{product_id}?tag={affiliate_tag}"

    @commands.Cog.listener()
    async def on_message(self, message):
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

    @commands.group()
    async def amazon(self, ctx):
        """Commands for managing Amazon affiliate settings."""
        if ctx.invoked_subcommand is None:
            await ctx.send("Invalid subcommand passed. Use [p]help amazon for available subcommands.")
    
    @amazon.command()
    async def set_tag(self, ctx, tag: str):
        """Set the Amazon affiliate tag for this server."""
        if not tag:
            await ctx.send("Invalid affiliate tag.")
            return
        
        try:
            await self.config.guild(ctx.guild).affiliate_tag.set(tag)
            await ctx.send(f"Affiliate tag set to: {tag} for this server.")
        except Exception as e:
            await ctx.send("There was an error setting the affiliate tag. Please try again later.")
    
    @amazon.command()
    async def enable(self, ctx):
        """Enable Amazon affiliate link handling for this server."""
        await self.config.guild(ctx.guild).enabled.set(True)
        await ctx.send("Amazon affiliate link handling has been enabled for this server.")

    @amazon.command()
    async def disable(self, ctx):
        """Disable Amazon affiliate link handling for this server."""
        await self.config.guild(ctx.guild).enabled.set(False)
        await ctx.send("Amazon affiliate link handling has been disabled for this server.")
