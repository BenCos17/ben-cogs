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
async def easter(self, ctx, year: int):
    """Get the date of Easter for a given year."""
    easter_date = self.calculate_easter(year)
    await ctx.send(f"Easter in {year} is on {easter_date.strftime('%A, %B %d, %Y')}.")


    @commands.command()
    async def lent(self, ctx):
        """Start of Lent message."""
        await ctx.send("🙏 Lent has begun! Time for fasting, prayer, and almsgiving. What are you giving up this year?")

    @commands.command()
    async def easter(self, ctx):
        """Celebrate Easter!"""
        await ctx.send("🐣🌸 He is risen! Happy Easter! 🎉✨")

    @commands.command()
    async def catholic_today(self, ctx):
        """Check if today is a special Christian holiday."""
        today = datetime.date.today()
        year = today.year

        # Calculate key Christian dates
        easter = self.calculate_easter(year)
        ash_wednesday = easter - datetime.timedelta(days=46)
        pancake_tuesday = ash_wednesday - datetime.timedelta(days=1)

        if today == pancake_tuesday:
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

async def setup(bot):
    await bot.add_cog(Seasons(bot))
