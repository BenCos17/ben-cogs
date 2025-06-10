from .clowndan import Clowndan

__red_end_user_data_statement__ = "This cog does not store any end user data."

async def setup(bot):
    await bot.add_cog(Clowndan(bot))

# Add this check to ensure the setup function is called when the module is loaded
if __name__ == "__main__":
    print("This module is not meant to be run directly.")
