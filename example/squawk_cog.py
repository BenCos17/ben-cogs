import discord
from redbot.core import commands
from datetime import datetime

class SquawkCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.squawk_api = None
        self.alert_count = 0
        self.last_alert_time = None

    async def cog_load(self):
        """Called when the cog is loaded."""
        await self._setup_squawk_api()

    def _get_squawk_api(self):
        """Get the SquawkAlertAPI from the skysearch cog."""
        skysearch_cog = self.bot.get_cog("SkySearch")
        if skysearch_cog and hasattr(skysearch_cog, 'squawk_api'):
            return skysearch_cog.squawk_api
        return None

    async def _setup_squawk_api(self):
        """Set up the squawk API and register callbacks."""
        self.squawk_api = self._get_squawk_api()
        if self.squawk_api:
            # Register different types of callbacks to test the API
            self.squawk_api.register_callback(self.handle_squawk_alert)
            self.squawk_api.register_pre_send_callback(self.modify_alert_message)
            self.squawk_api.register_post_send_callback(self.after_alert_sent)
        else:
            print("[SquawkExample] Warning: SkySearch cog not found or doesn't have squawk_api")

    async def handle_squawk_alert(self, guild, aircraft_info, squawk_code):
        """Basic callback that gets called when a squawk alert is detected."""
        self.alert_count += 1
        self.last_alert_time = datetime.now()
        
        print(f"[SquawkExample] Alert #{self.alert_count} detected in {guild.name}: {squawk_code} for aircraft {aircraft_info.get('hex', 'Unknown')}")
        
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
        # Check if squawk API is available
        if not self.squawk_api:
            await self._setup_squawk_api()
            if not self.squawk_api:
                await ctx.send("❌ SkySearch cog is not loaded or doesn't have squawk_api available.")
                return
        
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

    @commands.command(name="squawkstats")
    async def squawk_stats(self, ctx):
        """Show statistics about processed squawk alerts."""
        embed = discord.Embed(title="📊 SquawkExample Statistics", color=0x00ff00)
        embed.add_field(name="Total Alerts Processed", value=str(self.alert_count), inline=True)
        
        if self.last_alert_time:
            embed.add_field(name="Last Alert", value=self.last_alert_time.strftime("%Y-%m-%d %H:%M:%S UTC"), inline=True)
        else:
            embed.add_field(name="Last Alert", value="None", inline=True)
        
        # Check if squawk API is connected
        api_status = "✅ Connected" if self.squawk_api else "❌ Not Connected"
        embed.add_field(name="SkySearch API Status", value=api_status, inline=True)
        
        await ctx.send(embed=embed)

    @commands.command(name="debugskysearch")
    @commands.is_owner()
    async def debug_skysearch(self, ctx):
        """Debug command to see SkySearch cog attributes."""
        skysearch_cog = self.bot.get_cog("SkySearch")
        if skysearch_cog:
            attrs = [attr for attr in dir(skysearch_cog) if not attr.startswith('_')]
            await ctx.send(f"SkySearch cog found! Attributes: {', '.join(attrs[:20])}")  # Show first 20 attributes
            
            # Check for common API attribute names
            potential_apis = ['squawk_api', 'api', 'alert_api', 'squawk_alert_api']
            for api_name in potential_apis:
                if hasattr(skysearch_cog, api_name):
                    api_obj = getattr(skysearch_cog, api_name)
                    await ctx.send(f"✅ Found `{api_name}`: {type(api_obj)}")
                else:
                    await ctx.send(f"❌ No `{api_name}` attribute")
        else:
            await ctx.send("❌ SkySearch cog not found")

# Setup function to add the cog to the bot
async def setup(bot):
    await bot.add_cog(SquawkCog(bot))

