from redbot.core import commands

class BotInfoEmbed(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.support_server_tos = ""
        self.privacy_policy = ""
        self.support_server = ""
        self.bot_invite = ""
        self.vote_link = ""
        self.support_link = ""
        self.hidden_links = []  # List of hidden links
    
    async def red_get_data_for_user(self, *, user_id):
        # This is required by Red-DiscordBot to save data for the user.
        # Return a dictionary of data you want to save for the user.
        return {}
    
    async def red_delete_data_for_user(self, *, requester, user_id):
        # This is required by Red-DiscordBot to delete saved data for the user.
        # Implement this if you need to save data for the user.
        pass
    
    @commands.is_owner()
    @commands.command()
    async def set_support_server_tos(self, ctx, tos_link: str):
        """Set the terms of service link for the support server"""
        self.support_server_tos = tos_link
        await ctx.send("Support server terms of service link has been set.")
    
    @commands.command()
    @commands.is_owner()
    async def get_support_server_tos(self, ctx):
        """Get the current terms of service link for the support server"""
        embed = discord.Embed(title="Useful Links for JoultsBot", color=discord.Color.green())
        if self.support_server_tos and "tos" not in self.hidden_links:
            embed.add_field(name="Terms of Service", value=self.support_server_tos, inline=False)
        if self.privacy_policy and "privacy" not in self.hidden_links:
            embed.add_field(name="Privacy Policy", value=self.privacy_policy, inline=False)
        if self.support_server and "support" not in self.hidden_links:
            embed.add_field(name="Support Server", value=self.support_server, inline=False)
        if self.bot_invite and "invite" not in self.hidden_links:
            embed.add_field(name="Invite JoultsBot", value=self.bot_invite, inline=False)
        if self.vote_link and "vote" not in self.hidden_links:
            embed.add_field(name="Vote for JoultsBot", value=self.vote_link, inline=False)
        if self.support_link and "supportme" not in self.hidden_links:
            embed.add_field(name="Support Me!", value=self.support_link, inline=False)
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
    bot.add_cog(BotInfoEmbed(bot))
