from .clowndan import Clowndan

async def setup(bot):
    cog = Clowndan(bot)
    bot.add_cog(cog)  # Ensure this line is executed

# Add this check to ensure the setup function is called when the module is loaded
if __name__ == "__main__":
    print("This module is not meant to be run directly.")
