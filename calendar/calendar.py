import discord
import kuroutils
from redbot.core import commands
from redbot.core.bot import Red
from redbot.core.utils.chat_formatting import box
from calendar import monthcalendar  # Importing monthcalendar directly

class Calendar(kuroutils.Cog):
    """See the calendar on Discord!"""

    __author__ = ["Kuro"]
    __version__ = "0.0.1"

    def __init__(self, bot: Red):
        super().__init__(bot)
        self.events = []

    @commands.command(name="calendar")
    async def _calendar(
        self,
        ctx: commands.Context,
        month: int = None,
        year: int = None,
    ):
        """View the calendar!"""
        month = month or discord.utils.utcnow().month
        year = year or discord.utils.utcnow().year
        if not (0 < month < 13 and 0 < year < 10000):
            await ctx.send("Invalid month or year provided.")
            return
        w = 4 if isinstance(ctx.author, discord.Member) and ctx.author.is_on_mobile() else 5
        cal = "\n".join(str(w) for w in monthcalendar(year, month))  # Using monthcalendar directly
        if await ctx.embed_requested():
            embed = discord.Embed(
                description=box(cal, lang="prolog"), color=await ctx.embed_color()
            )
            await ctx.send(embed=embed)
            return
        await ctx.send(box(cal, lang="prolog"))

    @commands.command()
    async def add_event(self, ctx, event_name, event_date):
        # Add event to the calendar
        self.events.append((event_name, event_date))
        await ctx.send(f"Event '{event_name}' added on {event_date}.")

    @commands.command()
    async def view_events(self, ctx):
        # View all events in the calendar
        if self.events:
            events_list = "\n".join([f"{event[0]} on {event[1]}" for event in self.events])
            await ctx.send(f"List of upcoming events:\n{events_list}")
        else:
            await ctx.send("No upcoming events.")

    @commands.command()
    async def remove_event(self, ctx, event_name):
        # Remove event from the calendar
        for event in self.events:
            if event[0] == event_name:
                self.events.remove(event)
                await ctx.send(f"Event '{event_name}' removed.")
                return
        await ctx.send(f"Event '{event_name}' not found in the calendar.")

def setup(bot):
    bot.add_cog(Calendar(bot))
