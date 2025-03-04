from redbot.core import commands, Config, bank
import random
import datetime
import discord
from discord import ui, ButtonStyle, Embed
from typing import List, Tuple

class Seasons(commands.Cog):
    """A cog for Christian seasons and holidays like Lent, Easter, and more!"""

    def __init__(self, bot):
        self.bot = bot
        self.config = Config.get_conf(self, identifier=492089091320446976)
        default_member = {
            "total_flips": 0,
            "successful_flips": 0,
            "perfect_flips": 0,
            "failed_flips": 0,
            "total_earnings": 0,
            "best_flip": None,
            "worst_flip": None
        }
        self.config.register_member(**default_member)

    @commands.command()
    async def pancake(self, ctx):
        """Flip a pancake! Win currency and track your flipping stats!"""
        # Rare easter egg (1% chance)
        if random.random() < 0.01:  # 1% chance
            outcome_text = "✨ [2;33mMIRACULOUS! Your pancake transformed into a golden, glowing masterpiece![0m"
            credits = 1000  # Special high reward
            result = "perfect"
        else:
            base_outcomes = [
                ("🥞 You flipped the pancake perfectly! Golden brown and delicious!", (75, 150), "perfect"),
                ("😅 Oops! The pancake stuck to the ceiling... better luck next time!", (-75, -25), "fail"),
                ("🔥 Oh no! The pancake caught fire! Quick, grab the extinguisher!", (-100, -50), "fail"),
                ("🤹 Fancy! You did a triple flip and landed it like a pro!", (125, 200), "perfect"),
                ("🐶 Uh-oh... the dog stole your pancake mid-air!", (-50, -10), "fail"),
                ("🌟 INCREDIBLE! You juggled multiple pancakes like a master chef!", (150, 250), "perfect"),
                ("🎭 Your pancake landed making a perfect smiley face!", (100, 175), "success"),
                ("💫 You did a backflip while flipping the pancake! Spectacular!", (125, 225), "success"),
                ("😱 The pancake somehow turned into a waffle mid-flip...", (-40, -20), "fail"),
                ("🌪️ A sudden gust of wind carried your pancake away!", (-60, -30), "fail")
            ]
            outcome_text, credit_range, result = random.choice(base_outcomes)
            credits = random.randint(credit_range[0], credit_range[1])

        currency_name = await bank.get_currency_name(ctx.guild)
        
        # Update user's stats first
        async with self.config.member(ctx.author).all() as user_data:
            user_data["total_flips"] += 1
            
            if outcome_text.startswith("🌈✨ MIRACULOUS!"):  # Easter egg flip
                user_data["perfect_flips"] += 1
                user_data["successful_flips"] += 1
                user_data["best_flip"] = f"✝️ {outcome_text} ({datetime.datetime.now().strftime('%Y-%m-%d')})"
            elif result == "perfect":
                user_data["perfect_flips"] += 1
                user_data["successful_flips"] += 1
                if not user_data["best_flip"] or outcome_text not in user_data["best_flip"]:
                    user_data["best_flip"] = f"{outcome_text} ({datetime.datetime.now().strftime('%Y-%m-%d')})"
            
            elif result == "success":
                user_data["successful_flips"] += 1
            
            elif result == "fail":
                user_data["failed_flips"] += 1
                if not user_data["worst_flip"] or outcome_text not in user_data["worst_flip"]:
                    user_data["worst_flip"] = f"{outcome_text} ({datetime.datetime.now().strftime('%Y-%m-%d')})"

        # Handle currency rewards
        try:
            if credits > 0:
                await bank.deposit_credits(ctx.author, credits)
                new_balance = await bank.get_balance(ctx.author)
                await ctx.send(f"{outcome_text}\nYou earned {credits} {currency_name} for your flipping skills! 🎉\n"
                             f"Your new balance is: {new_balance} {currency_name}")
                
                async with self.config.member(ctx.author).all() as user_data:
                    user_data["total_earnings"] += credits
            else:
                await bank.withdraw_credits(ctx.author, abs(credits))
                new_balance = await bank.get_balance(ctx.author)
                await ctx.send(f"{outcome_text}\nOh no! You lost {abs(credits)} {currency_name}! 😅\n"
                             f"Your new balance is: {new_balance} {currency_name}")
                
                async with self.config.member(ctx.author).all() as user_data:
                    user_data["total_earnings"] -= abs(credits)
        except ValueError:
            await ctx.send(f"{outcome_text}\nBut you don't have enough {currency_name} to pay for the mishap!")

    @commands.command()
    async def pancake_stats(self, ctx, user: discord.Member = None):
        """Check your pancake flipping statistics."""
        if user is None:
            user = ctx.author

        data = await self.config.member(user).all()
        total = data["total_flips"]
        if total == 0:
            await ctx.send(f"{user.display_name} hasn't flipped any pancakes yet! 🥞")
            return

        success_rate = (data["successful_flips"] / total) * 100 if total > 0 else 0
        currency_name = await bank.get_currency_name(ctx.guild)
        
        msg = f"🥞 **{user.display_name}'s Pancake Flipping Stats**\n\n"
        msg += f"Total Flips: {total}\n"
        msg += f"Perfect Flips: {data['perfect_flips']}\n"
        msg += f"Successful Flips: {data['successful_flips']}\n"
        msg += f"Failed Flips: {data['failed_flips']}\n"
        msg += f"Success Rate: {success_rate:.1f}%\n"
        msg += f"Total Earnings: {data['total_earnings']} {currency_name}\n"
        
        if data["best_flip"]:
            msg += f"\nBest Flip: {data['best_flip']}"
        if data["worst_flip"]:
            msg += f"\nWorst Flip: {data['worst_flip']}"

        await ctx.send(msg)

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

    class StatsView(ui.View):
        def __init__(self, stats_pages: List[Embed]):
            super().__init__(timeout=60)
            self.current_page = 0
            self.pages = stats_pages

        @ui.button(label="◀️", style=ButtonStyle.gray)
        async def previous_button(self, interaction, button):
            self.current_page = (self.current_page - 1) % len(self.pages)
            await interaction.response.edit_message(embed=self.pages[self.current_page], view=self)

        @ui.button(label="▶️", style=ButtonStyle.gray)
        async def next_button(self, interaction, button):
            self.current_page = (self.current_page + 1) % len(self.pages)
            await interaction.response.edit_message(embed=self.pages[self.current_page], view=self)

        async def on_timeout(self):
            # Disable all buttons when the view times out
            for item in self.children:
                item.disabled = True
            await self.message.edit(view=self)

    @commands.command()
    async def pancake_leaders(self, ctx, top: int = 5):
        """Show detailed pancake leaderboards with multiple categories."""
        all_members = await self.config.all_members(ctx.guild)
        if not all_members:
            await ctx.send("No one has flipped any pancakes yet!")
            return

        # Prepare stats for each category
        categories = {
            "Success Rate 🎯": [],
            "Perfect Flips ✨": [],
            "Total Flips 🥞": [],
            "Total Earnings 💰": [],
        }

        currency_name = await bank.get_currency_name(ctx.guild)

        for member_id, data in all_members.items():
            member = ctx.guild.get_member(member_id)
            if member and data["total_flips"] > 0:
                success_rate = (data["successful_flips"] / data["total_flips"]) * 100
                
                categories["Success Rate 🎯"].append((member, success_rate, f"{success_rate:.1f}%"))
                categories["Perfect Flips ✨"].append((member, data["perfect_flips"], str(data["perfect_flips"])))
                categories["Total Flips 🥞"].append((member, data["total_flips"], str(data["total_flips"])))
                categories["Total Earnings 💰"].append((member, data["total_earnings"], f"{data['total_earnings']} {currency_name}"))

        # Sort each category and create embeds
        embeds = []
        for category, stats in categories.items():
            embed = Embed(title=f"Pancake Leaderboard - {category}", color=0xFFD700)
            embed.set_footer(text=f"Use the buttons to view different categories • Page {len(embeds) + 1}/{len(categories)}")
            
            # Sort and get top entries
            stats.sort(key=lambda x: x[1], reverse=True)
            top_entries = stats[:top]

            # Add fields to embed
            for pos, (member, value, display_value) in enumerate(top_entries, start=1):
                medal = {1: "🥇", 2: "🥈", 3: "🥉"}.get(pos, f"{pos}.")
                embed.add_field(
                    name=f"{medal} {member.display_name}",
                    value=display_value,
                    inline=False
                )

            embeds.append(embed)

        # Create and send view with embeds
        view = self.StatsView(embeds)
        view.message = await ctx.send(embed=embeds[0], view=view)

    @commands.command()
    async def balance(self, ctx, user: discord.Member = None):
        """Check your balance or someone else's."""
        if user is None:
            user = ctx.author
            
        bal = await bank.get_balance(user)
        currency_name = await bank.get_currency_name(ctx.guild)
        await ctx.send(f"{user.display_name}'s balance: {bal} {currency_name}")







    @bank.cost(10)  # Entry fee of 10 credits
    @commands.command()
    async def competitive_pancake(self, ctx):
        """Like pancake, but with an entry fee for bigger stakes!"""
        # Similar to regular pancake but with higher rewards
        base_outcomes = [
            ("🥞 Perfect flip! Championship material!", (100, 200), "perfect"),
            ("🏆 Tournament-winning flip!", (150, 300), "perfect"),
            ("💫 Legendary performance!", (200, 400), "perfect"),
            ("😅 Not your best showing...", (-150, -50), "fail"),
            ("💔 That's going to hurt the rankings!", (-200, -100), "fail")
        ]
        
        outcome_text, credit_range, result = random.choice(base_outcomes)
        credits = random.randint(credit_range[0], credit_range[1])
        currency_name = await bank.get_currency_name(ctx.guild)
        
        # Update user's stats first
        async with self.config.member(ctx.author).all() as user_data:
            user_data["total_flips"] += 1
            
            if result == "perfect":
                user_data["perfect_flips"] += 1
                user_data["successful_flips"] += 1
                if not user_data["best_flip"] or outcome_text not in user_data["best_flip"]:
                    user_data["best_flip"] = f"{outcome_text} ({datetime.datetime.now().strftime('%Y-%m-%d')})"
            elif result == "fail":
                user_data["failed_flips"] += 1
                if not user_data["worst_flip"] or outcome_text not in user_data["worst_flip"]:
                    user_data["worst_flip"] = f"{outcome_text} ({datetime.datetime.now().strftime('%Y-%m-%d')})"

        # Handle currency rewards
        try:
            if credits > 0:
                await bank.deposit_credits(ctx.author, credits)
                new_balance = await bank.get_balance(ctx.author)
                await ctx.send(f"{outcome_text}\nYou earned {credits} {currency_name} for your flipping skills! 🎉\n"
                             f"Your new balance is: {new_balance} {currency_name}")
                
                async with self.config.member(ctx.author).all() as user_data:
                    user_data["total_earnings"] += credits
            else:
                await bank.withdraw_credits(ctx.author, abs(credits))
                new_balance = await bank.get_balance(ctx.author)
                await ctx.send(f"{outcome_text}\nOh no! You lost {abs(credits)} {currency_name}! 😅\n"
                             f"Your new balance is: {new_balance} {currency_name}")
                
                async with self.config.member(ctx.author).all() as user_data:
                    user_data["total_earnings"] -= abs(credits)
        except ValueError:
            await ctx.send(f"{outcome_text}\nBut you don't have enough {currency_name} to pay for the mishap!")


