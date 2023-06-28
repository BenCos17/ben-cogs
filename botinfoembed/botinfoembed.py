from redbot.core import commands, Config
import discord

class BotInfoEmbed(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.config = Config.get_conf(self, identifier=1234567890)  # Use a unique identifier for your cog
        default_settings = {
            "support_server_tos": "",
            "privacy_policy": "",
            "support_server": "",
            "bot_invite": "",
            "vote_link": "",
            "support_link": "",
            "hidden_links": [],  # List of hidden links
            "link_emojis": {}  # Dictionary to store link emojis
        }
        self.config.register_guild(**default_settings)
    
    @commands.command()
    @commands.is_owner()
    async def set_link_emoji(self, ctx, link_name: str, emoji: str):
        """Set the emoji for a specific link"""
        link_name = link_name.lower()
        await self.config.guild(ctx.guild).link_emojis.set_raw(link_name, value=emoji)
        await ctx.send(f"The emoji for '{link_name.capitalize()}' link has been set to '{emoji}'.")
    
    @commands.command()
    async def get_support_server_tos(self, ctx):
        """Get the current terms of service link for the support server"""
        bot_name = self.bot.user.name
        embed = discord.Embed(title=f"Useful Links for {bot_name}", color=discord.Color.green())
        if self.support_server_tos and "tos" not in self.hidden_links:
            emoji = await self.config.guild(ctx.guild).link_emojis.get_raw("tos")
            if emoji:
                embed.add_field(name="Terms of Service", value=f"{emoji} [Link]({self.support_server_tos})", inline=False)
            else:
                embed.add_field(name="Terms of Service", value=f"[Link]({self.support_server_tos})", inline=False)
        if self.privacy_policy and "privacy" not in self.hidden_links:
            emoji = await self.config.guild(ctx.guild).link_emojis.get_raw("privacy")
            if emoji:
                embed.add_field(name="Privacy Policy", value=f"{emoji} [Link]({self.privacy_policy})", inline=False)
            else:
                embed.add_field(name="Privacy Policy", value=f"[Link]({self.privacy_policy})", inline=False)
        if self.support_server and "support" not in self.hidden_links:
            emoji = await self.config.guild(ctx.guild).link_emojis.get_raw("support")
            if emoji:
                embed.add_field(name="Support Server", value=f"{emoji} [Link]({self.support_server})", inline=False)
            else:
                embed.add_field(name="Support Server", value=f"[Link]({self.support_server})", inline=False)
        if self.bot_invite and "invite" not in self.hidden_links:
            emoji = await self.config.guild(ctx.guild).link_emojis.get_raw("invite")
            if emoji:
                embed.add_field(name=f"Invite {bot_name}", value=f"{emoji} [Link]({self.bot_invite})", inline=False)
            else:
                embed.add_field(name=f"Invite {bot_name}", value=f"[Link]({self.bot_invite})", inline=False)
        if self.vote_link and "vote" not in self.hidden_links:
            emoji = await self.config.guild(ctx.guild).link_emojis.get_raw("vote")
            if emoji:
                embed.add_field(name=f"Vote for {bot_name}", value=f"{emoji} [Link]({self.vote_link})", inline=False)
            else:
                embed.add_field(name=f"Vote for {bot_name}", value=f"[Link]({self.vote_link})", inline=False)
        if self.support_link and "supportme" not in self.hidden_links:
            emoji = await self.config.guild(ctx.guild).link_emojis.get_raw("supportme")
            if emoji:
                embed.add_field(name="Support Me!", value=f"{emoji} [Link]({self.support_link})", inline=False)
            else:
                embed.add_field(name="Support Me!", value=f"[Link]({self.support_link})", inline=False)
        await ctx.send(embed=embed)

    # Add commands to set other links
    
    @commands.is_owner()
    @commands.command()
    async def hide_link(self, ctx, link_name: str):
        """Hide a specific link from the list"""
        link_name = link_name.lower()
        if link_name in self.hidden_links:
            await ctx.send(f"{link_name.capitalize()} link is already hidden.")
        else:
            self.hidden_links.append(link_name)
            await ctx.send(f"{link_name.capitalize()} link has been hidden.")
    
    @commands.is_owner()
    @commands.command()
    async def show_link(self, ctx, link_name: str):
        """Show a specific link in the list"""
        link_name = link_name.lower()
        if link_name in self.hidden_links:
            self.hidden_links.remove(link_name)
            await ctx.send(f"{link_name.capitalize()} link has been shown.")
        else:
            await ctx.send(f"{link_name.capitalize()} link is already shown or not hidden.")
    
def setup(bot):
    bot.add_cog(BotSettings(bot))
