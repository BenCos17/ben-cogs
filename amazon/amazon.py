import re
from redbot.core import commands

class Amazon(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.affiliate_tag = "yourtag-20"  # Default affiliate tag, configure this per server

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot:
            return
        
        # Regex to find Amazon product links in messages
        amazon_link_pattern = r"https?://(?:www\.)?amazon\.[a-z]{2,3}(?:\.[a-z]{2})?/(?:.*/)?(?:dp|gp/product)/(\w+/)?(\w{10})"
        matches = re.findall(amazon_link_pattern, message.content)
        
        if matches:
            affiliate_links = []
            for match in matches:
                # Generate affiliate link
                affiliate_link = f"https://www.amazon.com/dp/{match[1]}?tag={self.affiliate_tag}"
                affiliate_links.append(affiliate_link)
            
            if affiliate_links:
                response = "Here are the Amazon affiliate links:\n" + "\n".join(affiliate_links)
                await message.channel.send(response)

    @commands.command()
    async def set_affiliate_tag(self, ctx, tag: str):
        """Set the Amazon affiliate tag for this server."""
        self.affiliate_tag = tag
        await ctx.send(f"Affiliate tag set to: {tag}")

def setup(bot):
    bot.add_cog(Amazon(bot))
