from redbot.core import commands
import random
import datetime

class Seasons(commands.Cog):
    """A cog for Christian seasons and holidays like Lent, Easter, and more!"""

    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def pancake(self, ctx):
        """Celebrate Pancake Tuesday with a virtual flip!"""
        outcomes = [
            "🥞 You flipped the pancake perfectly! Golden brown and delicious!",
            "😅 Oops! The pancake stuck to the ceiling... better luck next time!",
            "🔥 Oh no! The pancake caught fire! Quick, grab the extinguisher!",
            "🤹 Fancy! You did a triple flip and landed it like a pro!",
            "🐶 Uh-oh... the dog stole your pancake mid-air!"
        ]
        await ctx.send(random.choice(outcomes))

    @commands.command()
    async def ashwednesday(self, ctx):
        """Ash Wednesday reminder."""
        await ctx.send("✝️ Remember, you are dust, and to dust you shall return. Have a blessed Ash Wednesday.")

    @commands.command()
    async def easter(self, ctx, year: int = None):
        """Get the date of Easter or celebrate Easter!
        If year is provided, shows Easter date for that year."""
        if year is None:
            year = datetime.date.today().year
        easter_date = self.calculate_easter(year)
        
        today = datetime.date.today()
        if today == easter_date:
            await ctx.send("🐣🌸 He is risen! Happy Easter! 🎉✨")
        else:
            await ctx.send(f"Easter in {year} is on {easter_date.strftime('%A, %B %d, %Y')}.")


    @commands.command()
    async def lent(self, ctx):
        """Start of Lent message."""
        await ctx.send("🙏 Lent has begun! Time for fasting, prayer, and almsgiving. What are you giving up this year?")

    @commands.command()
    async def catholic_today(self, ctx):
        """Check if today is a special Christian holiday."""
        today = datetime.date.today()
        year = today.year

        # Calculate key Christian dates
        easter = self.calculate_easter(year)
        ash_wednesday = easter - datetime.timedelta(days=46)
        pancake_tuesday = ash_wednesday - datetime.timedelta(days=1)
        pentecost = easter + datetime.timedelta(days=49)
        
        # Calculate Advent (4 Sundays before Christmas)
        christmas = datetime.date(year, 12, 25)
        advent_start = christmas - datetime.timedelta(days=22)  # Approximate

        # Add more special dates
        good_friday = easter - datetime.timedelta(days=2)
        palm_sunday = easter - datetime.timedelta(days=7)
        holy_thursday = easter - datetime.timedelta(days=3)
        
        if today == christmas:
            await ctx.send("🎄 Merry Christmas! Glory to God in the highest!")
        elif today == good_friday:
            await ctx.send("✝️ Today is Good Friday, commemorating Christ's crucifixion.")
        elif today == palm_sunday:
            await ctx.send("🌿 Today is Palm Sunday, marking Jesus's triumphant entry into Jerusalem.")
        elif today == holy_thursday:
            await ctx.send("🍷🍞 Today is Holy Thursday, commemorating the Last Supper.")
        elif today == pancake_tuesday:
            await self.pancake(ctx)
        elif today == ash_wednesday:
            await self.ash(ctx)
        elif today >= ash_wednesday and today < easter:
            await self.lent(ctx)
        elif today == easter:
            await self.easter(ctx)
        else:
            await ctx.send("📅 No major Christian event today, but every day is a good day for reflection and prayer.")

    def calculate_easter(self, year):
        """Computes the date of Easter Sunday for a given year using the Gregorian calendar."""
        a = year % 19
        b = year // 100
        c = year % 100
        d = b // 4
        e = b % 4
        f = (b + 8) // 25
        g = (b - f + 1) // 3
        h = (19 * a + b - d - g + 15) % 30
        i = c // 4
        k = c % 4
        l = (32 + 2 * e + 2 * i - h - k) % 7
        m = (a + 11 * h + 22 * l) // 451
        month = (h + l - 7 * m + 114) // 31
        day = ((h + l - 7 * m + 114) % 31) + 1
        return datetime.date(year, month, day)

    @commands.command()
    async def advent(self, ctx):
        """Information about Advent season."""
        await ctx.send("🕯️ Advent is a time of waiting and preparation for the celebration of Jesus's birth. "
                      "Each candle on the Advent wreath represents: Hope, Peace, Joy, and Love.")

    @commands.command()
    async def christmas(self, ctx):
        """Celebrate Christmas!"""
        await ctx.send("🎄✨ Glory to God in the highest! Merry Christmas! "
                      "Celebrating the birth of our Savior Jesus Christ. 👶⭐")

    @commands.command()
    async def pentecost(self, ctx, year: int = None):
        """Get the date of Pentecost (50 days after Easter)."""
        if year is None:
            year = datetime.date.today().year
        easter_date = self.calculate_easter(year)
        pentecost_date = easter_date + datetime.timedelta(days=49)
        await ctx.send(f"🕊️ Pentecost in {year} is on {pentecost_date.strftime('%A, %B %d, %Y')}.")

async def setup(bot):
    await bot.add_cog(Seasons(bot))
