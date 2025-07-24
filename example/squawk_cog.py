import discord
from redbot.core import commands, Config
import asyncio
import datetime
from typing import Dict, Optional

class SquawkCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.squawk_api = None
        self.config = Config.get_conf(self, identifier=492089091320446977)
        self.config.register_global(
            alert_history=[],
            max_history=100,
            enable_logging=True,
            enable_message_updates=True
        )
        self.config.register_guild(
            track_alerts=True,
            update_messages=True
        )
        # Store message references for updating
        self.alert_messages: Dict[str, discord.Message] = {}

    async def cog_load(self):
        """Called when the cog is loaded."""
        await self._setup_squawk_api()

    def _get_squawk_api(self):
        """Get the SquawkAlertAPI from the skysearch cog."""
        # Try the correct name first, then fallbacks
        possible_names = ["skysearch", "SkySearch", "Skysearch", "SkySearchCog"]
        
        for name in possible_names:
            skysearch_cog = self.bot.get_cog(name)
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
            print(f"[SquawkExample] Successfully connected to SkySearch API - {len(self.squawk_api._callbacks)} callbacks registered")
        else:
            print("[SquawkExample] Warning: SkySearch cog not found or doesn't have squawk_api")

    async def reconnect_to_skysearch(self):
        """Manually reconnect to the SkySearch API."""
        await self._setup_squawk_api()
        return self.squawk_api is not None

    async def handle_squawk_alert(self, guild, aircraft_info, squawk_code):
        """Enhanced callback that gets called when a squawk alert is detected."""
        hex_code = aircraft_info.get('hex', 'Unknown')
        callsign = aircraft_info.get('flight', 'Unknown')
        
        # Log the alert
        print(f"[SquawkExample] 🚨 ALERT DETECTED in {guild.name}: Squawk {squawk_code} for aircraft {hex_code} ({callsign})")
        
        # Check if we should track this alert
        guild_config = self.config.guild(guild)
        if await guild_config.track_alerts():
            # Store alert in history
            alert_data = {
                'timestamp': datetime.datetime.utcnow().isoformat(),
                'guild_id': guild.id,
                'guild_name': guild.name,
                'hex': hex_code,
                'callsign': callsign,
                'squawk_code': squawk_code,
                'lat': aircraft_info.get('lat'),
                'lon': aircraft_info.get('lon'),
                'altitude': aircraft_info.get('altitude'),
                'ground_speed': aircraft_info.get('ground_speed')
            }
            
            await self._add_to_history(alert_data)
            
        # Additional custom processing
        await self._process_custom_alert(guild, aircraft_info, squawk_code)

    async def _add_to_history(self, alert_data):
        """Add alert to history with size management."""
        history = await self.config.alert_history()
        max_history = await self.config.max_history()
        
        history.append(alert_data)
        
        # Keep only the most recent alerts
        if len(history) > max_history:
            history = history[-max_history:]
            
        await self.config.alert_history.set(history)

    async def _process_custom_alert(self, guild, aircraft_info, squawk_code):
        """Custom processing for different types of alerts."""
        hex_code = aircraft_info.get('hex', 'Unknown')
        
        # Different handling based on squawk code
        if squawk_code == '7700':  # General emergency
            print(f"[SquawkExample] 🚨 GENERAL EMERGENCY detected: {hex_code}")
        elif squawk_code == '7600':  # Radio failure
            print(f"[SquawkExample] 📻 RADIO FAILURE detected: {hex_code}")
        elif squawk_code == '7500':  # Hijacking
            print(f"[SquawkExample] 🔒 HIJACKING ALERT detected: {hex_code}")
        
        # You could add custom logic here like:
        # - Send notifications to external services
        # - Log to databases
        # - Trigger additional monitoring

    async def modify_alert_message(self, guild, aircraft_info, squawk_code, message_data):
        """Pre-send callback to modify the alert message before it's sent."""
        guild_config = self.config.guild(guild)
        if not await guild_config.update_messages():
            return message_data
            
        # Add timestamp and custom branding
        timestamp = datetime.datetime.utcnow().strftime("%H:%M:%S UTC")
        
        # Example: Add custom content to the message
        if message_data.get('content'):
            message_data['content'] += f"\n🔔 **Enhanced by SquawkExample** | Detected at {timestamp}"
        else:
            message_data['content'] = f"🔔 **Enhanced by SquawkExample** | Detected at {timestamp}"
        
        # Example: Modify the embed
        if message_data.get('embed'):
            embed = message_data['embed']
            embed.add_field(
                name="📡 Enhanced Monitoring", 
                value=f"This alert is being tracked by SquawkExample cog\nDetection time: {timestamp}", 
                inline=False
            )
            
            # Add custom footer
            embed.set_footer(text=f"Enhanced by SquawkExample | Original SkySearch Alert")
        
        hex_code = aircraft_info.get('hex', 'Unknown')
        print(f"[SquawkExample] Modified alert message for {hex_code}")
        return message_data

    async def after_alert_sent(self, guild, aircraft_info, squawk_code, sent_message):
        """Post-send callback that runs after the alert message is sent."""
        hex_code = aircraft_info.get('hex', 'Unknown')
        print(f"[SquawkExample] Alert message sent in {guild.name} for aircraft {hex_code}")
        
        # Store message reference for potential updates
        alert_key = f"{guild.id}_{hex_code}_{squawk_code}"
        self.alert_messages[alert_key] = sent_message
        
        guild_config = self.config.guild(guild)
        if await guild_config.update_messages():
            # Example: React to the message
            try:
                await sent_message.add_reaction("👀")
                await sent_message.add_reaction("✈️")
                if squawk_code == '7700':
                    await sent_message.add_reaction("🚨")
                elif squawk_code == '7600':
                    await sent_message.add_reaction("📻")
                elif squawk_code == '7500':
                    await sent_message.add_reaction("🔒")
            except discord.errors.Forbidden:
                print("[SquawkExample] Could not add reactions - missing permissions")
            except Exception as e:
                print(f"[SquawkExample] Error adding reactions: {e}")
            
            # Schedule a message update after 30 seconds
            asyncio.create_task(self._schedule_message_update(sent_message, aircraft_info, squawk_code))

    async def _schedule_message_update(self, message: discord.Message, aircraft_info: dict, squawk_code: str):
        """Schedule an update to the alert message with additional info."""
        await asyncio.sleep(30)  # Wait 30 seconds
        
        try:
            # Create updated embed with additional tracking info
            if message.embeds:
                embed = message.embeds[0]
                embed.add_field(
                    name="📊 Status Update",
                    value=f"Alert has been active for 30+ seconds\nContinuous monitoring enabled",
                    inline=False
                )
                embed.color = discord.Color.orange()  # Change color to indicate update
                
                await message.edit(embed=embed)
                print(f"[SquawkExample] Updated alert message for {aircraft_info.get('hex', 'Unknown')}")
        except discord.errors.NotFound:
            print(f"[SquawkExample] Could not update message - message was deleted")
        except Exception as e:
            print(f"[SquawkExample] Error updating message: {e}")

    @commands.group(name="squawkexample", aliases=["se"])
    async def squawk_example(self, ctx):
        """SquawkExample commands for managing alert tracking."""
        if ctx.invoked_subcommand is None:
            embed = discord.Embed(
                title="SquawkExample Commands",
                description="Enhanced squawk alert tracking and management",
                color=discord.Color.blue()
            )
            embed.add_field(
                name="📊 Information",
                value="`history` - View recent alert history\n`stats` - View alert statistics\n`status` - Check cog status",
                inline=False
            )
            embed.add_field(
                name="⚙️ Configuration",
                value="`toggle tracking` - Toggle alert tracking\n`toggle updates` - Toggle message updates",
                inline=False
            )
            await ctx.send(embed=embed)

    @squawk_example.command(name="history")
    async def view_history(self, ctx, limit: int = 10):
        """View recent alert history."""
        history = await self.config.alert_history()
        
        if not history:
            await ctx.send("No alert history found.")
            return
            
        # Get recent alerts (limited)
        recent_alerts = history[-limit:] if len(history) > limit else history
        recent_alerts.reverse()  # Show newest first
        
        embed = discord.Embed(
            title=f"Recent Alert History (Last {len(recent_alerts)})",
            color=discord.Color.red()
        )
        
        for i, alert in enumerate(recent_alerts[:10]):  # Show max 10 in embed
            timestamp = datetime.datetime.fromisoformat(alert['timestamp'])
            embed.add_field(
                name=f"Alert #{len(history) - i}",
                value=f"**Aircraft:** {alert['hex']} ({alert['callsign']})\n"
                      f"**Squawk:** {alert['squawk_code']}\n"
                      f"**Guild:** {alert['guild_name']}\n"
                      f"**Time:** {timestamp.strftime('%Y-%m-%d %H:%M:%S')} UTC",
                inline=True
            )
            
        await ctx.send(embed=embed)

    @squawk_example.command(name="stats")
    async def view_stats(self, ctx):
        """View alert statistics."""
        history = await self.config.alert_history()
        
        if not history:
            await ctx.send("No alert data available.")
            return
            
        # Calculate statistics
        total_alerts = len(history)
        squawk_counts = {}
        guild_counts = {}
        
        for alert in history:
            squawk = alert['squawk_code']
            guild = alert['guild_name']
            
            squawk_counts[squawk] = squawk_counts.get(squawk, 0) + 1
            guild_counts[guild] = guild_counts.get(guild, 0) + 1
            
        embed = discord.Embed(
            title="Alert Statistics",
            description=f"Total alerts tracked: **{total_alerts}**",
            color=discord.Color.green()
        )
        
        # Top squawk codes
        if squawk_counts:
            top_squawks = sorted(squawk_counts.items(), key=lambda x: x[1], reverse=True)[:5]
            squawk_text = "\n".join([f"{code}: {count}" for code, count in top_squawks])
            embed.add_field(name="Top Squawk Codes", value=squawk_text, inline=True)
            
        # Top guilds
        if guild_counts:
            top_guilds = sorted(guild_counts.items(), key=lambda x: x[1], reverse=True)[:5]
            guild_text = "\n".join([f"{guild}: {count}" for guild, count in top_guilds])
            embed.add_field(name="Top Guilds", value=guild_text, inline=True)
            
        await ctx.send(embed=embed)

    @squawk_example.command(name="status")
    async def check_status(self, ctx):
        """Check the status of the SquawkExample cog."""
        # Use the same logic as other commands to find the cog
        possible_names = ["skysearch", "SkySearch", "Skysearch", "SkySearchCog"]
        skysearch_cog = None
        
        for name in possible_names:
            cog = self.bot.get_cog(name)
            if cog:
                skysearch_cog = cog
                break
        
        embed = discord.Embed(
            title="SquawkExample Status",
            color=discord.Color.blue()
        )
        
        # Check SkySearch connection
        if skysearch_cog and self.squawk_api:
            embed.add_field(
                name="🟢 SkySearch Connection",
                value="Connected and receiving alerts",
                inline=False
            )
        else:
            embed.add_field(
                name="🔴 SkySearch Connection",
                value="Not connected - SkySearch cog may not be loaded",
                inline=False
            )
            
        # Guild settings
        guild_config = self.config.guild(ctx.guild)
        tracking = await guild_config.track_alerts()
        updates = await guild_config.update_messages()
        
        embed.add_field(
            name="Guild Settings",
            value=f"Alert Tracking: {'✅' if tracking else '❌'}\n"
                  f"Message Updates: {'✅' if updates else '❌'}",
            inline=True
        )
        
        # Alert count
        history = await self.config.alert_history()
        embed.add_field(
            name="Statistics",
            value=f"Total Alerts: {len(history)}\n"
                  f"Active Messages: {len(self.alert_messages)}",
            inline=True
        )
        
        await ctx.send(embed=embed)

    @squawk_example.group(name="toggle")
    async def toggle_settings(self, ctx):
        """Toggle various settings."""
        pass

    @toggle_settings.command(name="tracking")
    async def toggle_tracking(self, ctx):
        """Toggle alert tracking for this guild."""
        guild_config = self.config.guild(ctx.guild)
        current = await guild_config.track_alerts()
        await guild_config.track_alerts.set(not current)
        
        status = "enabled" if not current else "disabled"
        await ctx.send(f"✅ Alert tracking has been **{status}** for this guild.")

    @toggle_settings.command(name="updates")
    async def toggle_updates(self, ctx):
        """Toggle message updates for this guild."""
        guild_config = self.config.guild(ctx.guild)
        current = await guild_config.update_messages()
        await guild_config.update_messages.set(not current)
        
        status = "enabled" if not current else "disabled"
        await ctx.send(f"✅ Message updates have been **{status}** for this guild.")

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
        sent_message = await ctx.send(
            content=modified_data.get('content'),
            embed=modified_data.get('embed')
        )
        
        # Test post-send callback
        await self.after_alert_sent(ctx.guild, fake_aircraft, '7700', sent_message)
        
        await ctx.send("✅ SquawkAPI test completed! Check console for debug output.")

    @squawk_example.command(name="reconnect")
    @commands.is_owner()
    async def reconnect_api(self, ctx):
        """Manually reconnect to the SkySearch API (owner only)."""
        success = await self.reconnect_to_skysearch()
        if success:
            await ctx.send("✅ Successfully reconnected to SkySearch API!")
        else:
            await ctx.send("❌ Failed to reconnect to SkySearch API. Make sure the SkySearch cog is loaded.")

    @squawk_example.command(name="debug")
    @commands.is_owner() 
    async def debug_connection(self, ctx):
        """Debug the connection to SkySearch API (owner only)."""
        # Try the correct name first, then fallbacks
        possible_names = ["skysearch", "SkySearch", "Skysearch", "SkySearchCog"]
        skysearch_cog = None
        found_name = None
        
        for name in possible_names:
            cog = self.bot.get_cog(name)
            if cog:
                skysearch_cog = cog
                found_name = name
                break
        
        embed = discord.Embed(title="SquawkExample Debug Info", color=discord.Color.blue())
        
        if skysearch_cog:
            embed.add_field(name="SkySearch Cog", value=f"✅ Found as '{found_name}'", inline=True)
            
            if hasattr(skysearch_cog, 'squawk_api'):
                embed.add_field(name="SquawkAPI", value="✅ Available", inline=True)
                
                # Check callback counts
                api = skysearch_cog.squawk_api
                embed.add_field(name="Registered Callbacks", 
                               value=f"Basic: {len(api._callbacks)}\nPre-send: {len(api._pre_send_callbacks)}\nPost-send: {len(api._post_send_callbacks)}", 
                               inline=False)
                
                # Check if our callbacks are registered
                our_callback_found = any(cb.__self__ == self for cb in api._callbacks if hasattr(cb, '__self__'))
                embed.add_field(name="Our Callbacks", value="✅ Registered" if our_callback_found else "❌ Not found", inline=True)
                
                # Check background task status
                if hasattr(skysearch_cog, 'check_emergency_squawks'):
                    task = skysearch_cog.check_emergency_squawks
                    task_status = "✅ Running" if task.is_running() else "❌ Stopped"
                    embed.add_field(name="Background Task", value=task_status, inline=True)
                
            else:
                embed.add_field(name="SquawkAPI", value="❌ Not found", inline=True)
        else:
            embed.add_field(name="SkySearch Cog", value="❌ Not found", inline=True)
            
        await ctx.send(embed=embed)

# Setup function to add the cog to the bot
async def setup(bot):
    await bot.add_cog(SquawkCog(bot))

