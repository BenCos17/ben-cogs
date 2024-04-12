from redbot.core import commands
from typing import Optional
from redbot.core import checks
from redbot.core import Config

class Court(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.config = Config.get_conf(self, identifier=1234567890)
        default_guild_settings = {"court_cases": {}}
        self.config.register_guild(**default_guild_settings)

    async def get_court_cases(self, ctx):
        return await self.config.guild(ctx.guild).court_cases()

    @commands.command()
    @commands.guild_only()
    async def add_case(self, ctx, case_number: str, *, case_details: str):
        """Add a new court case."""
        court_cases = await self.get_court_cases(ctx)
        court_cases[case_number] = case_details
        await self.config.guild(ctx.guild).court_cases.set(court_cases)
        await ctx.send(f"Case {case_number} has been added.")

    @commands.command()
    @commands.guild_only()
    async def remove_case(self, ctx, case_number: str):
        """Remove a court case."""
        court_cases = await self.get_court_cases(ctx)
        if case_number in court_cases:
            del court_cases[case_number]
            await self.config.guild(ctx.guild).court_cases.set(court_cases)
            await ctx.send(f"Case {case_number} has been removed.")
        else:
            await ctx.send(f"Case {case_number} not found.")

    @commands.command()
    @commands.guild_only()
    async def list_cases(self, ctx):
        """List all court cases."""
        court_cases = await self.get_court_cases(ctx)
        if court_cases:
            cases_list = "\n".join([f"Case Number: {case_number} - Details: {case_details}" 
                                    for case_number, case_details in court_cases.items()])
            await ctx.send("List of Court Cases:\n" + cases_list)
        else:
            await ctx.send("No court cases available.")

    @commands.command()
    async def court_help(self, ctx):
        """Display help for court commands."""
        help_message = ("```\n"
                        "!add_case [case_number] [case_details]: Add a new court case.\n"
                        "!remove_case [case_number]: Remove a court case.\n"
                        "!list_cases: List all court cases.\n"
                        "```")
        await ctx.send(help_message)

    @commands.group(name="courtsettings", aliases=["courtset"], invoke_without_command=True)
    @checks.admin_or_permissions(manage_guild=True)
    async def court_settings(self, ctx):
        """Manage court settings."""
        await ctx.send_help(self.court_settings)

    @court_settings.command(name="reset")
    async def court_reset(self, ctx):
        """Reset court settings."""
        await self.config.guild(ctx.guild).clear()
        await ctx.send("Court settings have been reset.")

def setup(bot):
    bot.add_cog(Court(bot))
