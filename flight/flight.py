import discord
from redbot.core import commands
import random

class Flight(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.aircraft = None
        self.level = None
        self.score = 0
        self.obstacles = []
        self.altitude = 10000
        self.speed = 500
        self.fuel = 100

    @commands.command(name='start')
    async def start_game(self, ctx):
        await ctx.send("Welcome to the Flight game! Choose your aircraft using [p]aircraft.")
        self.aircraft = None
        self.level = None
        self.score = 0
        self.altitude = 10000
        self.speed = 500
        self.fuel = 100

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
            await ctx.send("You did not choose an aircraft in time. Please try again with [p]aircraft.")
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
            await ctx.send(f"You have completed all available levels. Final score: {self.score}")

    @commands.command(name='flighthelp')
    async def help_command(self, ctx):
        message = "Red Flight Command List:\n"
        message += "[p]start - Begin the game\n"
        message += "[p]aircraft - Choose your aircraft\n"
        message += "[p]help - Show the command list\n"
        message += "[p]takeoff - Takeoff the aircraft\n"
        message += "[p]landing - Land the aircraft\n"
        message += "[p]up - Increase altitude\n"
        message += "[p]down - Decrease altitude\n"
        message += "[p]speedup - Increase speed\n"
        message += "[p]slowdown - Decrease speed\n"
        await ctx.send(message)

    async def move(self, ctx):
        message = f"The {self.aircraft} is flying. What is your next move?\n"
        message += "1. Go up\n"
        message += "2. Go down\n"
        message += "3. Go left\n"
        message += "4. Go right\n"
        message += "5. Quit game\n"
        await ctx.send(message)

        def check(m):
            return m.author == ctx.author and m.content.isdigit() and 1 <= int(m.content) <= 5

        try:
            user_choice = await self.bot.wait_for('message', check=check, timeout=30.0)
            if int(user_choice.content) == 5:
                await ctx.send("Game over. Thanks for playing!")
                return
            await self.check_move(user_choice.content, ctx)
        except:
            await ctx.send("You did not make a move in time. Please try again.")
            await self.move(ctx)

    async def move(self, ctx):
    message = f"The {self.aircraft} is flying. What is your next move?\n"
    message += "1. Go up\n"
    message += "2. Go down\n"
    message += "3. Go left\n"
    message += "4. Go right\n"
    message += "5. Quit game\n"
    await ctx.send(message)

    def check(m):
        return m.author == ctx.author and m.content.isdigit() and 1 <= int(m.content) <= 5

    try:
        user_choice = await self.bot.wait_for('message', check=check, timeout=30.0)
        if int(user_choice.content) == 5:
            await ctx.send("Game over. Thanks for playing!")
            return
        await self.check_move(user_choice.content, ctx)
    except:
        await ctx.send("You did not make a move in time. Please try again.")
        await self.move(ctx)

    async def check_move(self, user_choice, ctx):
        obstacle = random.choice(self.obstacles[self.level - 1])
        if user_choice == "1":
            await ctx.send(f"The {self.aircraft} is going up!")
            if obstacle == "Birds":
                await ctx.send("You hit a flock of birds! Game over.")
                return
            await self.end_level(ctx)
        elif user_choice == "2":
            await ctx.send(f"The {self.aircraft} is going down!")
            if obstacle == "Turbulence":
                await ctx.send("You hit a patch of turbulence! Game over.")
                return
            await self.end_level(ctx)
        elif user_choice == "3":
            await ctx.send(f"The {self.aircraft} is going left!")
            if obstacle == "Storm clouds":
                await ctx.send("You flew into a storm cloud! Game over.")
                return
            await self.end_level(ctx)
        elif user_choice == "4":
            await ctx.send(f"The {self.aircraft} is going right!")
            if obstacle == "Ice":
                await ctx.send("You flew into a patch of ice! Game over.")
                return
            await self.end_level(ctx)
        else:
            await ctx.send("Invalid move. Please try again.")
            await self.move(ctx)
           @commands.command(name='takeoff')
async def takeoff(self, ctx):
    await ctx.send("The aircraft is taking off!")
    await self.move(ctx)

@commands.command(name='landing')
async def landing(self, ctx):
    await ctx.send("The aircraft is landing!")
    self.altitude = 0
    await self.end_level(ctx)

@commands.command(name='up')
async def go_up(self, ctx):
    await ctx.send(f"The {self.aircraft} is going up!")
    self.altitude += 1000
    await self.move(ctx)

@commands.command(name='down')
async def go_down(self, ctx):
    await ctx.send(f"The {self.aircraft} is going down!")
    self.altitude -= 1000
    await self.move(ctx)

@commands.command(name='speedup')
async def speed_up(self, ctx):
    await ctx.send(f"The {self.aircraft} is speeding up!")
    self.speed += 100
    await self.move(ctx)

@commands.command(name='slowdown')
async def speed_down(self, ctx):
    await ctx.send(f"The {self.aircraft} is slowing down!")
    self.speed -= 100
    await self.move(ctx)


