from redbot.core import commands
import discord
import datetime
from typing import Optional

class SeasonsSlash(commands.Cog):
    """Slash commands for Christian seasons and holidays."""

    def __init__(self, bot):
        self.bot = bot

    @commands.slash_command(name="holiday", description="Get information about Christian holidays")
    async def holiday_slash(
        self,
        ctx,
        holiday: str = discord.Option(
            description="Choose a holiday",
            choices=[
                "Ash Wednesday",
                "Easter",
                "Pentecost",
                "Christmas",
                "Epiphany",
                "Assumption of Mary",
                "All Saints' Day",
                "All Souls' Day",
                "Corpus Christi",
                "Ascension",
                "Palm Sunday",
                "Good Friday",
                "Holy Thursday"
            ]
        ),
        year: Optional[int] = discord.Option(description="Year (optional)", required=False)
    ):
        """Slash command to get information about any Christian holiday."""
        # Get the main cog instance
        seasons_cog = self.bot.get_cog("Seasons")
        if not seasons_cog:
            await ctx.respond("❌ The Seasons cog is not loaded.", ephemeral=True)
            return

        # Map the choice to our internal keys
        holiday_map = {
            "Ash Wednesday": "ash_wednesday",
            "Easter": "easter",
            "Pentecost": "pentecost",
            "Christmas": "christmas",
            "Epiphany": "epiphany",
            "Assumption of Mary": "assumption_of_mary",
            "All Saints' Day": "all_saints_day",
            "All Souls' Day": "all_souls_day",
            "Corpus Christi": "corpus_christi",
            "Ascension": "ascension",
            "Palm Sunday": "palm_sunday",
            "Good Friday": "good_friday",
            "Holy Thursday": "holy_thursday"
        }

        try:
            if year is None:
                year = datetime.date.today().year

            holiday_key = holiday_map[holiday]
            
            if holiday == "Easter":
                # Special handling for Easter since it's the base calculation
                easter_date = seasons_cog.calculate_easter(year)
                today = datetime.date.today()
                
                if today == easter_date:
                    await ctx.respond("🐣🌸 He is risen! Happy Easter! 🎉✨")
                else:
                    await ctx.respond(f"Easter in {year} is on {easter_date.strftime('%A, %B %d, %Y')}.")
            else:
                # Use the base holiday command for all other holidays
                dates = await seasons_cog.get_season_dates(year)
                holiday_date = dates[holiday_key]
                
                # Map the holiday key to the appropriate message format
                message_map = {
                    "ash_wednesday": (
                        "✝️ Remember, you are dust, and to dust you shall return. Have a blessed Ash Wednesday.",
                        "✝️ Ash Wednesday is on {}. Remember, you are dust, and to dust you shall return."
                    ),
                    "pentecost": (
                        "🕊️ Today is Pentecost, celebrating the descent of the Holy Spirit upon the Apostles.",
                        "🕊️ Pentecost is on {}, celebrating the descent of the Holy Spirit upon the Apostles."
                    ),
                    "christmas": (
                        "🎄✨ Glory to God in the highest! Merry Christmas! Celebrating the birth of our Savior Jesus Christ. 👶⭐",
                        "🎄 Christmas is on {}. Glory to God in the highest! Celebrating the birth of our Savior Jesus Christ. 👶⭐"
                    ),
                    "epiphany": (
                        "✨ Today is Epiphany, celebrating the visit of the Magi to Jesus.",
                        "✨ Epiphany is on {}, celebrating the visit of the Magi to Jesus."
                    ),
                    "assumption_of_mary": (
                        "🕊️ Today is the Assumption of Mary, celebrating Mary's ascension into heaven.",
                        "🕊️ The Assumption of Mary is on {}, celebrating Mary's ascension into heaven."
                    ),
                    "all_saints_day": (
                        "✝️ Today is All Saints' Day, honoring all Christian saints and martyrs.",
                        "✝️ All Saints' Day is on {}, honoring all Christian saints and martyrs."
                    ),
                    "all_souls_day": (
                        "🕯️ Today is All Souls' Day, remembering and honoring the deceased.",
                        "🕯️ All Souls' Day is on {}, remembering and honoring the deceased."
                    ),
                    "corpus_christi": (
                        "🍞 Today is Corpus Christi, celebrating the Body of Christ.",
                        "🍞 Corpus Christi is on {}, celebrating the Body of Christ."
                    ),
                    "ascension": (
                        "✝️ Today is Ascension Thursday, commemorating Jesus's ascension into heaven.",
                        "✝️ Ascension Thursday is on {}, commemorating Jesus's ascension into heaven."
                    ),
                    "palm_sunday": (
                        "🌿 Today is Palm Sunday, marking Jesus's triumphant entry into Jerusalem.",
                        "🌿 Palm Sunday is on {}, marking Jesus's triumphant entry into Jerusalem."
                    ),
                    "good_friday": (
                        "✝️ Today is Good Friday, commemorating Christ's crucifixion.",
                        "✝️ Good Friday is on {}, commemorating Christ's crucifixion."
                    ),
                    "holy_thursday": (
                        "🍷🍞 Today is Holy Thursday, commemorating the Last Supper.",
                        "🍷🍞 Holy Thursday is on {}, commemorating the Last Supper."
                    )
                }

                today_message, future_message = message_map[holiday_key]
                
                if datetime.date.today() == holiday_date:
                    await ctx.respond(today_message)
                else:
                    await ctx.respond(future_message.format(holiday_date.strftime('%A, %B %d, %Y')))

        except Exception as e:
            await ctx.respond(f"❌ An error occurred while calculating the date: {str(e)}", ephemeral=True) 