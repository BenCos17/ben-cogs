import discord
from discord.ext import commands
from api.squawk_api import SquawkAlertAPI

class SquawkCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.squawk_api = SquawkAlertAPI()

        # Register different types of callbacks to test the API
        self.squawk_api.register_callback(self.handle_squawk_alert)
        self.squawk_api.register_pre_send_callback(self.modify_alert_message)
        self.squawk_api.register_post_send_callback(self.after_alert_sent)

    async def handle_squawk_alert(self, guild, aircraft_info, squawk_code):
        """Basic callback that gets called when a squawk alert is detected."""
        print(f"[SquawkExample] Alert detected in {guild.name}: {squawk_code} for aircraft {aircraft_info.get('hex', 'Unknown')}")
        
        # You could do additional processing here, like:
        # - Log to a database
        # - Send to external APIs
        # - Perform custom analysis

    async def modify_alert_message(self, guild, aircraft_info, squawk_code, message_data):
        """Pre-send callback to modify the alert message before it's sent."""
        # Example: Add custom content to the message
        if message_data.get('content'):
            message_data['content'] += f"\n🔔 **SquawkExample detected this alert!**"
        else:
            message_data['content'] = f"🔔 **SquawkExample detected this alert!**"
        
        # Example: Modify the embed
        if message_data.get('embed'):
            embed = message_data['embed']
            embed.add_field(
                name="📡 Example Cog Alert", 
                value=f"This alert was processed by the SquawkExample cog!", 
                inline=False
            )
        
        print(f"[SquawkExample] Modified alert message for {aircraft_info.get('hex', 'Unknown')}")
        return message_data

    async def after_alert_sent(self, guild, aircraft_info, squawk_code, sent_message):
        """Post-send callback that runs after the alert message is sent."""
        print(f"[SquawkExample] Alert message sent in {guild.name} for aircraft {aircraft_info.get('hex', 'Unknown')}")
        
        # Example: React to the message
        try:
            await sent_message.add_reaction("👀")
            await sent_message.add_reaction("✈️")
        except discord.errors.Forbidden:
            print("[SquawkExample] Could not add reactions - missing permissions")
        except Exception as e:
            print(f"[SquawkExample] Error adding reactions: {e}")

    @commands.command(name="testsquawk")
    @commands.is_owner()
    async def test_squawk_api(self, ctx):
        """Test command to manually trigger the squawk API callbacks."""
        # Create fake aircraft data for testing
        fake_aircraft = {
            'hex': 'TEST01',
            'flight': 'TEST123',
            'lat': 40.7128,
            'lon': -74.0060,
            'altitude': 35000,
            'ground_speed': 450
        }
        
        # Test the basic callback
        await self.handle_squawk_alert(ctx.guild, fake_aircraft, '7700')
        
        # Test pre-send callback
        test_message_data = {
            'content': 'Test alert message',
            'embed': discord.Embed(title="Test Emergency Alert", description="This is a test"),
            'view': None
        }
        
        modified_data = await self.modify_alert_message(ctx.guild, fake_aircraft, '7700', test_message_data)
        
        # Send the test message to see the modifications
        await ctx.send(
            content=modified_data.get('content'),
            embed=modified_data.get('embed')
        )
        
        await ctx.send("✅ SquawkAPI test completed! Check console for debug output.")

# Setup function to add the cog to the bot
async def setup(bot):
    await bot.add_cog(SquawkCog(bot))

