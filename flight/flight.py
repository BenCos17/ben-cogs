import discord
from redbot.core import commands
import random

class RedFlight(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.aircraft = None
        self.level = None
        self.score = 0
        self.obstacles = []

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
            return

        # Generate obstacles for each level
        self.obstacles = [
            ["Clouds", "Turbulence", "Birds"],
            ["Storm clouds", "High winds", "Hail"],
            ["Thunderstorms", "Lightning", "Ice"]
        ]

        # Start at level 1
        self.level = 1
        await self.start_level(ctx)

    async def start_level(self, ctx):
        await ctx.send(f"Starting level {self.level}! Good luck, pilot.")
        await ctx.send("Here are the obstacles for this level:")
        for obstacle in self.obstacles[self.level - 1]:
            await ctx.send(f"- {obstacle}")

    async def end_level(self, ctx):
        await ctx.send("Congratulations! You have completed this level.")
        self.score += 100 * self.level
        if self.level < len(self.obstacles):
            self.level += 1
            await self.start_level(ctx)
        else:
            await ctx.send("You have completed all available levels. Final score: {self.score}")

    @commands.command(name='help')
    async def help_command(self, ctx):
        message = "Red Flight Command List:\n"
        message += "!start - Begin the game\n"
        message += "!aircraft - Choose your aircraft\n"
        message += "!help - Show the command list\n"
        await ctx.send(message)

def setup(bot):
    bot.add_cog(RedFlight(bot))
