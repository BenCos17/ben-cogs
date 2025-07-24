from discord.ext import commands
from api.squawk_api import SquawkAlertAPI

class SquawkCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.squawk_api = SquawkAlertAPI()

        # Register a sample callback
        self.squawk_api.register_callback(self.handle_squawk_alert)

    async def handle_squawk_alert(self, guild, aircraft_info, squawk_code):
        # Handle the squawk alert here
        print(f"Squawk alert received: {squawk_code} for aircraft: {aircraft_info}")

# Setup function to add the cog to the bot
def setup(bot):
    bot.add_cog(SquawkCog(bot)) 