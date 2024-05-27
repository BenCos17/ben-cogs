import re
from redbot.core import commands

class Amazon(commands.Cog):
    """Cog for handling Amazon affiliate links."""
    
    def __init__(self, bot):
        self.bot = bot
        self.affiliate_tags = {}  # Dictionary to store affiliate tags per server

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot:
            return
        
        # Regex to find Amazon product links in messages
        amazon_link_pattern = r"https?://(?:www\.)?amazon\.[a-z]{2,3}(?:\.[a-z]{2})?/(?:.*/)?(?:dp|gp/product)/(\w+/)?(\w{10})"
        matches = re.findall(amazon_link_pattern, message.content)
        
        if matches:
            affiliate_links = []
            server_id = str(message.guild.id)
            affiliate_tag = self.affiliate_tags.get(server_id, "yourtag-20")  # Use default if not set
            for match in matches:
                # Generate affiliate link
                affiliate_link = f"https://www.amazon.com/dp/{match[1]}?tag={affiliate_tag}"
                affiliate_links.append(affiliate_link)
            
            if affiliate_links:
                response = "Here are the Amazon affiliate links:\n" + "\n".join(affiliate_links)
                await message.channel.send(response)

    @commands.command()
    async def set_affiliate_tag(self, ctx, tag: str):
        """Set the Amazon affiliate tag for this server."""
        server_id = str(ctx.guild.id)
        self.affiliate_tags[server_id] = tag
        await ctx.send(f"Affiliate tag set to: {tag} for this server.")

