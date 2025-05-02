from redbot.core import commands, Config, bank
import random
import datetime
import discord
from discord import ui, ButtonStyle, Embed
from typing import List, Tuple, Dict, Optional, Union
from functools import lru_cache

class Seasons(commands.Cog):
    """A cog for Christian seasons and holidays like Lent, Easter, and more!"""

    def __init__(self, bot):
        self.bot = bot
        self.config = Config.get_conf(self, identifier=492089091320446976)
        
        # Register default member config
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

    # Constants for days before/after Easter
    DAYS_BEFORE_EASTER = {
        "ash_wednesday": 46,
        "pancake_tuesday": 47,
        "good_friday": 2,
        "palm_sunday": 7,
        "holy_thursday": 3,
        "pentecost": 49,
        "ascension": 39,
        "corpus_christi": 60
    }

    @lru_cache(maxsize=128)
    def calculate_easter(self, year: int) -> datetime.date:
        """Computes the date of Easter Sunday for a given year using the Gregorian calendar."""
        try:
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
        except (ValueError, TypeError) as e:
            raise commands.BadArgument(f"Invalid year for Easter calculation: {year}") from e

    async def get_season_dates(self, year: int) -> Dict[str, datetime.date]:
        """Calculate all important dates for a given year."""
        easter = self.calculate_easter(year)
        
        return {
            "easter": easter,
            "ash_wednesday": easter - datetime.timedelta(days=self.DAYS_BEFORE_EASTER["ash_wednesday"]),
            "pancake_tuesday": easter - datetime.timedelta(days=self.DAYS_BEFORE_EASTER["pancake_tuesday"]),
            "good_friday": easter - datetime.timedelta(days=self.DAYS_BEFORE_EASTER["good_friday"]),
            "palm_sunday": easter - datetime.timedelta(days=self.DAYS_BEFORE_EASTER["palm_sunday"]),
            "holy_thursday": easter - datetime.timedelta(days=self.DAYS_BEFORE_EASTER["holy_thursday"]),
            "pentecost": easter + datetime.timedelta(days=self.DAYS_BEFORE_EASTER["pentecost"]),
            "ascension": easter + datetime.timedelta(days=self.DAYS_BEFORE_EASTER["ascension"]),
            "corpus_christi": easter + datetime.timedelta(days=self.DAYS_BEFORE_EASTER["corpus_christi"]),
            "epiphany": datetime.date(year, 1, 6),
            "assumption_of_mary": datetime.date(year, 8, 15),
            "all_saints_day": datetime.date(year, 11, 1),
            "all_souls_day": datetime.date(year, 11, 2),
            "christmas": datetime.date(year, 12, 25),
            "advent_start": datetime.date(year, 12, 25) - datetime.timedelta(days=22)
        }

    async def _holiday_command(self, ctx, holiday_key: str, today_message: str, future_message: str) -> None:
        """Base method for holiday commands.
        
        Args:
            ctx: The command context
            holiday_key: The key in get_season_dates for this holiday
            today_message: Message to send if today is the holiday
            future_message: Message to send if today is not the holiday
        """
        today = datetime.date.today()
        year = today.year
        
        try:
            dates = await self.get_season_dates(year)
            holiday_date = dates[holiday_key]
            
            if today == holiday_date:
                await ctx.send(today_message)
            else:
                await ctx.send(future_message.format(holiday_date.strftime('%A, %B %d, %Y')))
        except Exception as e:
            await ctx.send(f"❌ An error occurred while calculating the date: {str(e)}")

    @commands.command()
    async def ashwednesday(self, ctx):
        """Ash Wednesday reminder."""
        await self._holiday_command(
            ctx,
            "ash_wednesday",
            "✝️ Remember, you are dust, and to dust you shall return. Have a blessed Ash Wednesday.",
            "✝️ Ash Wednesday is on {}. Remember, you are dust, and to dust you shall return."
        )

    @commands.command()
    async def easter(self, ctx, year: int = None):
        """Get the date of Easter or celebrate Easter!
        If year is provided, shows Easter date for that year."""
        if year is None:
            year = datetime.date.today().year
        try:
            easter_date = self.calculate_easter(year)
            today = datetime.date.today()
            
            if today == easter_date:
                await ctx.send("🐣🌸 He is risen! Happy Easter! 🎉✨")
            else:
                await ctx.send(f"Easter in {year} is on {easter_date.strftime('%A, %B %d, %Y')}.")
        except Exception as e:
            await ctx.send(f"❌ An error occurred while calculating the date: {str(e)}")

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
    async def lent(self, ctx):
        """Start of Lent message."""
        today = datetime.date.today()
        year = today.year
        
        try:
            # Get this year's dates
            this_year_dates = await self.get_season_dates(year)
            this_easter = this_year_dates["easter"]
            this_ash_wednesday = this_year_dates["ash_wednesday"]
            
            # Get next year's dates
            next_year_dates = await self.get_season_dates(year + 1)
            next_easter = next_year_dates["easter"]
            next_ash_wednesday = next_year_dates["ash_wednesday"]
            
            # Determine which year's dates to show
            if today > this_easter:
                ash_wednesday = next_ash_wednesday
                easter = next_easter
            else:
                ash_wednesday = this_ash_wednesday
                easter = this_easter
            
            await ctx.send(f"🙏 Lent begins on {ash_wednesday.strftime('%A, %B %d, %Y')} and ends on {easter.strftime('%A, %B %d, %Y')}.\n"
                          "A time for fasting, prayer, and almsgiving. What are you giving up this year?")
        except Exception as e:
            await ctx.send(f"❌ An error occurred while calculating the Lenten dates: {str(e)}")

    @commands.command()
    async def catholic_today(self, ctx):
        """Check if today is a special Christian holiday."""
        today = datetime.date.today()
        year = today.year

        try:
            # Get all dates for the year
            dates = await self.get_season_dates(year)
            
            # Define messages for each date
            special_dates = {
                dates["christmas"]: "🎄 Merry Christmas! Glory to God in the highest!",
                dates["good_friday"]: "✝️ Today is Good Friday, commemorating Christ's crucifixion.",
                dates["palm_sunday"]: "🌿 Today is Palm Sunday, marking Jesus's triumphant entry into Jerusalem.",
                dates["holy_thursday"]: "🍷🍞 Today is Holy Thursday, commemorating the Last Supper.",
                dates["pancake_tuesday"]: "🥞 It's Pancake Tuesday! Time to flip some pancakes! Use the pancake command to celebrate!",
                dates["ash_wednesday"]: self.ashwednesday,
                dates["easter"]: self.easter,
                dates["epiphany"]: "✨ Today is Epiphany, celebrating the visit of the Magi to Jesus.",
                dates["ascension"]: "✝️ Today is Ascension Thursday, commemorating Jesus's ascension into heaven.",
                dates["corpus_christi"]: "🍞 Today is Corpus Christi, celebrating the Body of Christ.",
                dates["assumption_of_mary"]: "🕊️ Today is the Assumption of Mary, celebrating Mary's ascension into heaven.",
                dates["all_saints_day"]: "✝️ Today is All Saints' Day, honoring all Christian saints and martyrs.",
                dates["all_souls_day"]: "🕯️ Today is All Souls' Day, remembering and honoring the deceased."
            }

            # Check if today matches any dates
            for date, message in special_dates.items():
                if today == date:
                    if callable(message):
                        await message(ctx)
                    else:
                        await ctx.send(message)
                    return

            # Check if we're in Lent
            if today == dates["ash_wednesday"]:
                await self.lent(ctx)
                return

            # Generic message if no special date
            await ctx.send("📅 No major Christian event today, but every day is a good day for reflection and prayer.")
            
        except Exception as e:
            await ctx.send(f"❌ An error occurred while checking today's events: {str(e)}")

    @commands.command()
    async def advent(self, ctx):
        """Information about Advent season."""
        today = datetime.date.today()
        year = today.year
        
        try:
            # Get this year's dates
            this_year_dates = await self.get_season_dates(year)
            this_advent_start = this_year_dates["advent_start"]
            this_christmas = this_year_dates["christmas"]
            
            # Get next year's dates
            next_year_dates = await self.get_season_dates(year + 1)
            next_advent_start = next_year_dates["advent_start"]
            next_christmas = next_year_dates["christmas"]
            
            # Determine which year's Advent to show
            if today > this_advent_start:
                advent_start = next_advent_start
                christmas = next_christmas
            else:
                advent_start = this_advent_start
                christmas = this_christmas
            
            await ctx.send(f"🕯️ Advent begins on {advent_start.strftime('%A, %B %d, %Y')} and ends on {christmas.strftime('%A, %B %d, %Y')}.\n"
                          "A time of waiting and preparation for the celebration of Jesus's birth. "
                          "Each candle on the Advent wreath represents: Hope, Peace, Joy, and Love.")
        except Exception as e:
            await ctx.send(f"❌ An error occurred while calculating the Advent dates: {str(e)}")

    @commands.command()
    async def christmas(self, ctx):
        """Celebrate Christmas!"""
        await self._holiday_command(
            ctx,
            "christmas",
            "🎄✨ Glory to God in the highest! Merry Christmas! Celebrating the birth of our Savior Jesus Christ. 👶⭐",
            "🎄 Christmas is on {}. Glory to God in the highest! Celebrating the birth of our Savior Jesus Christ. 👶⭐"
        )

    @commands.command()
    async def pentecost(self, ctx, year: int = None):
        """Get the date of Pentecost (50 days after Easter)."""
        if year is None:
            year = datetime.date.today().year
        try:
            dates = await self.get_season_dates(year)
            pentecost_date = dates["pentecost"]
            await ctx.send(f"🕊️ Pentecost in {year} is on {pentecost_date.strftime('%A, %B %d, %Y')}.")
        except Exception as e:
            await ctx.send(f"❌ An error occurred while calculating the date: {str(e)}")

    @commands.command()
    async def pancaketuesday(self, ctx):
        """Get the date of Pancake Tuesday."""
        today = datetime.date.today()
        year = today.year
        
        try:
            dates = await self.get_season_dates(year)
            pancake_tuesday = dates["pancake_tuesday"]
            
            if today == pancake_tuesday:
                await ctx.send("🥞 It's Pancake Tuesday! Time to flip some pancakes! Use the pancake command to celebrate!")
            else:
                await ctx.send(f"🥞 Pancake Tuesday is on {pancake_tuesday.strftime('%A, %B %d, %Y')}. Time to flip some pancakes!")
        except Exception as e:
            await ctx.send(f"❌ An error occurred while calculating the date: {str(e)}")

    @commands.command()
    async def epiphany(self, ctx):
        """Get the date of Epiphany."""
        today = datetime.date.today()
        year = today.year
        
        try:
            dates = await self.get_season_dates(year)
            epiphany = dates["epiphany"]
            
            if today == epiphany:
                await ctx.send("✨ Today is Epiphany, celebrating the visit of the Magi to Jesus.")
            else:
                await ctx.send(f"✨ Epiphany is on {epiphany.strftime('%A, %B %d, %Y')}, celebrating the visit of the Magi to Jesus.")
        except Exception as e:
            await ctx.send(f"❌ An error occurred while calculating the date: {str(e)}")

    @commands.command()
    async def assumption(self, ctx):
        """Get the date of the Assumption of Mary."""
        today = datetime.date.today()
        year = today.year
        
        try:
            dates = await self.get_season_dates(year)
            assumption = dates["assumption_of_mary"]
            
            if today == assumption:
                await ctx.send("🕊️ Today is the Assumption of Mary, celebrating Mary's ascension into heaven.")
            else:
                await ctx.send(f"🕊️ The Assumption of Mary is on {assumption.strftime('%A, %B %d, %Y')}, celebrating Mary's ascension into heaven.")
        except Exception as e:
            await ctx.send(f"❌ An error occurred while calculating the date: {str(e)}")

    @commands.command()
    async def allsaints(self, ctx):
        """Get the date of All Saints' Day."""
        today = datetime.date.today()
        year = today.year
        
        try:
            dates = await self.get_season_dates(year)
            all_saints = dates["all_saints_day"]
            
            if today == all_saints:
                await ctx.send("✝️ Today is All Saints' Day, honoring all Christian saints and martyrs.")
            else:
                await ctx.send(f"✝️ All Saints' Day is on {all_saints.strftime('%A, %B %d, %Y')}, honoring all Christian saints and martyrs.")
        except Exception as e:
            await ctx.send(f"❌ An error occurred while calculating the date: {str(e)}")

    @commands.command()
    async def allsouls(self, ctx):
        """Get the date of All Souls' Day."""
        today = datetime.date.today()
        year = today.year
        
        try:
            dates = await self.get_season_dates(year)
            all_souls = dates["all_souls_day"]
            
            if today == all_souls:
                await ctx.send("🕯️ Today is All Souls' Day, remembering and honoring the deceased.")
            else:
                await ctx.send(f"🕯️ All Souls' Day is on {all_souls.strftime('%A, %B %d, %Y')}, remembering and honoring the deceased.")
        except Exception as e:
            await ctx.send(f"❌ An error occurred while calculating the date: {str(e)}")

    @commands.command()
    async def corpuschristi(self, ctx):
        """Get the date of Corpus Christi."""
        today = datetime.date.today()
        year = today.year
        
        try:
            dates = await self.get_season_dates(year)
            corpus_christi = dates["corpus_christi"]
            
            if today == corpus_christi:
                await ctx.send("🍞 Today is Corpus Christi, celebrating the Body of Christ.")
            else:
                await ctx.send(f"🍞 Corpus Christi is on {corpus_christi.strftime('%A, %B %d, %Y')}, celebrating the Body of Christ.")
        except Exception as e:
            await ctx.send(f"❌ An error occurred while calculating the date: {str(e)}")

    @commands.command()
    async def ascension(self, ctx):
        """Get the date of Ascension Thursday."""
        today = datetime.date.today()
        year = today.year
        
        try:
            dates = await self.get_season_dates(year)
            ascension = dates["ascension"]
            
            if today == ascension:
                await ctx.send("✝️ Today is Ascension Thursday, commemorating Jesus's ascension into heaven.")
            else:
                await ctx.send(f"✝️ Ascension Thursday is on {ascension.strftime('%A, %B %d, %Y')}, commemorating Jesus's ascension into heaven.")
        except Exception as e:
            await ctx.send(f"❌ An error occurred while calculating the date: {str(e)}")

    @commands.command()
    async def palmsunday(self, ctx):
        """Get the date of Palm Sunday."""
        today = datetime.date.today()
        year = today.year
        
        try:
            dates = await self.get_season_dates(year)
            palm_sunday = dates["palm_sunday"]
            
            if today == palm_sunday:
                await ctx.send("🌿 Today is Palm Sunday, marking Jesus's triumphant entry into Jerusalem.")
            else:
                await ctx.send(f"🌿 Palm Sunday is on {palm_sunday.strftime('%A, %B %d, %Y')}, marking Jesus's triumphant entry into Jerusalem.")
        except Exception as e:
            await ctx.send(f"❌ An error occurred while calculating the date: {str(e)}")

    @commands.command()
    async def goodfriday(self, ctx):
        """Get the date of Good Friday."""
        today = datetime.date.today()
        year = today.year
        
        try:
            dates = await self.get_season_dates(year)
            good_friday = dates["good_friday"]
            
            if today == good_friday:
                await ctx.send("✝️ Today is Good Friday, commemorating Christ's crucifixion.")
            else:
                await ctx.send(f"✝️ Good Friday is on {good_friday.strftime('%A, %B %d, %Y')}, commemorating Christ's crucifixion.")
        except Exception as e:
            await ctx.send(f"❌ An error occurred while calculating the date: {str(e)}")

    @commands.command()
    async def holythursday(self, ctx):
        """Get the date of Holy Thursday."""
        today = datetime.date.today()
        year = today.year
        
        try:
            dates = await self.get_season_dates(year)
            holy_thursday = dates["holy_thursday"]
            
            if today == holy_thursday:
                await ctx.send("🍷🍞 Today is Holy Thursday, commemorating the Last Supper.")
            else:
                await ctx.send(f"🍷🍞 Holy Thursday is on {holy_thursday.strftime('%A, %B %d, %Y')}, commemorating the Last Supper.")
        except Exception as e:
            await ctx.send(f"❌ An error occurred while calculating the date: {str(e)}")

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

    @commands.command()
    async def is_lent(self, ctx):
        """Check if we are currently in the Lenten season."""
        today = datetime.date.today()
        year = today.year
        easter = self.calculate_easter(year)
        ash_wednesday = easter - datetime.timedelta(days=46)
        
        if today >= ash_wednesday and today <= easter:
            await ctx.send("🙏 Yes, we are in the Lenten season! A time for fasting, prayer, and almsgiving.")
        else:
            await ctx.send("No, we are not currently in the Lenten season.")


