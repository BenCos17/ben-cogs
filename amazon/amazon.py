import re
from redbot.core import commands, Config

class Amazon(commands.Cog):
    """Cog for handling Amazon affiliate links."""
    
    def __init__(self, bot):
        self.bot = bot
        self.config = Config.get_conf(self, identifier=1234567890, force_registration=True)
        default_guild = {"affiliate_tag": "yourtag-20"}
        self.config.register_guild(**default_guild)
        
        # Compile the regex pattern once and reuse it
        self.amazon_link_pattern = re.compile(
            r"https?://(?:www\.)?amazon\.[a-z]{2,3}(?:\.[a-z]{2})?/(?:.*/)?(?:dp|gp/product)/(\w+/)?(\w{10})"
        )

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot:
            return
        
        if not message.guild:
            return

        # Find all Amazon product links in the message
        matches = self.amazon_link_pattern.finditer(message.content)
        
        affiliate_links = []
        server_id = message.guild.id
        affiliate_tag = await self.config.guild(message.guild).affiliate_tag()
        
        for match in matches:
            product_id = match.group(2)
            if product_id:
                # Generate affiliate link
                affiliate_link = f"https://www.amazon.com/dp/{product_id}?tag={affiliate_tag}"
                affiliate_links.append(affiliate_link)
        
        if affiliate_links:
            response = "Here are the Amazon affiliate links:\n" + "\n".join(affiliate_links)
            await message.channel.send(response)

    @commands.command()
    async def set_affiliate_tag(self, ctx, tag: str):
        """Set the Amazon affiliate tag for this server."""
        if not tag:
            await ctx.send("Invalid affiliate tag.")
            return
        
        await self.config.guild(ctx.guild).affiliate_tag.set(tag)
        await ctx.send(f"Affiliate tag set to: {tag} for this server.")
