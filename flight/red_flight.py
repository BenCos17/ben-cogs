import discord
from redbot.core import commands

class RedFlight(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.aircraft = None
        self.level = None
        self.score = 0

    @commands.command(name='start')
    async def start_game(self, ctx):
        await ctx.send("Welcome to Red Flight! Choose your aircraft using !aircraft.")
        self.aircraft = None
        self.level = None
        self.score = 0

    @commands.command(name='aircraft')
    async def choose_aircraft(self, ctx):
        aircraft_options = ['F-22', 'F-35', 'Su-57']
        message = "Choose your aircraft:\n"
        for i, aircraft in enumerate(aircraft_options):
            message += f"{i + 1}. {aircraft}\n"
        await ctx.send(message)

        def check(m):
            return m.author == ctx.author and m.content.isdigit() and 1 <= int(m.content) <= len(aircraft_options)

        try:
            user_choice = await self.bot.wait_for('message', check=check, timeout=30.0)
            self.aircraft = aircraft_options[int(user_choice.content) - 1]
            await ctx.send(f"You have chosen the {self.aircraft} aircraft.")
        except:
            await ctx.send("You did not choose an aircraft in time. Please try again with !aircraft.")

    @commands.command(name='help')
    async def help_command(self, ctx):
        message = "Red Flight Command List:\n"
        message += "!start - Begin the game\n"
        message += "!aircraft - Choose your aircraft\n"
        message += "!help - Show the command list\n"
        await ctx.send(message)

def setup(bot):
    bot.add_cog(RedFlight(bot))
