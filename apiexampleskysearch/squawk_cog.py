import discord
from redbot.core import commands, Config
import asyncio
import datetime
import logging
from typing import Dict, Optional

log = logging.getLogger("red.squawkexample")

class SquawkCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.squawk_api = None
        self.config = Config.get_conf(self, identifier=492089091320446977)
        self.config.register_global(
            max_history=100,
            enable_logging=True,
            enable_message_updates=True
        )
        self.config.register_guild(
            track_alerts=True,
            update_messages=True,
            alert_history=[],
            command_history=[]
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
            # Register different types of callbacks with enhanced parameters
            self.squawk_api.register_callback(
                self.handle_squawk_alert, 
                cog_name="SquawkExample", 
                priority=10,  # High priority for testing
                timeout=15.0
            )
            self.squawk_api.register_pre_send_callback(
                self.modify_alert_message, 
                cog_name="SquawkExample", 
                priority=5,   # Medium priority for message modification
                timeout=8.0
            )
            self.squawk_api.register_post_send_callback(
                self.after_alert_sent, 
                cog_name="SquawkExample", 
                priority=1,   # Lower priority for post-processing
                timeout=20.0  # Longer timeout for potential message updates
            )
            log.info(f"Successfully connected to SkySearch API - {len(self.squawk_api._callbacks)} callbacks registered")
        else:
            log.warning("SkySearch cog not found or doesn't have squawk_api")
            
        # Also hook into command API if available
        await self._setup_command_api()

    async def _setup_command_api(self):
        """Set up the command API and register callbacks."""
        skysearch_cog = None
        possible_names = ["skysearch", "SkySearch", "Skysearch", "SkySearchCog"]
        
        for name in possible_names:
            cog = self.bot.get_cog(name)
            if cog and hasattr(cog, 'command_api'):
                skysearch_cog = cog
                break
                
        if skysearch_cog and hasattr(skysearch_cog, 'command_api'):
            # Register command callbacks with enhanced parameters
            skysearch_cog.command_api.register_callback(
                self.handle_command_execution,
                cog_name="SquawkExample",
                priority=5,
                timeout=10.0,
                command_filter=["aircraft_icao", "aircraft_callsign", "aircraft_squawk"]  # Only track specific commands
            )
            skysearch_cog.command_api.register_post_execute_callback(
                self.handle_command_complete,
                cog_name="SquawkExample",
                priority=1,
                timeout=5.0,
                command_filter=None  # Track all commands for error logging
            )
            log.info("Successfully connected to SkySearch CommandAPI")
        else:
            log.warning("SkySearch CommandAPI not found")

    async def handle_command_execution(self, ctx, command_name: str, args: list):
        """Handle when a SkySearch command is executed."""
        # Store command usage data silently
        guild_config = self.config.guild(ctx.guild)
        if await guild_config.track_alerts():  # Reuse the tracking setting
            command_data = {
                'timestamp': datetime.datetime.utcnow().isoformat(),
                'guild_id': ctx.guild.id,
                'guild_name': ctx.guild.name,
                'user_id': ctx.author.id,
                'user_name': ctx.author.name,
                'command_name': command_name,
                'args': args,
                'channel_id': ctx.channel.id,
                'channel_name': ctx.channel.name
            }
            
            # Store command in history
            await self._add_command_to_history(ctx.guild, command_data)

    async def handle_command_complete(self, ctx, command_name: str, args: list, result: any, execution_time: float):
        """Handle when a SkySearch command completes."""
        success = not isinstance(result, Exception)
        
        # You could add logic here to:
        # - Track command performance
        # - Log errors (only if there are errors)
        # - Send notifications for slow commands
        # - Update usage statistics
        
        # Only log errors, not successful commands
        if not success:
            log.error(f"COMMAND ERROR: {command_name} failed - {result}")

    async def reconnect_to_skysearch(self):
        """Manually reconnect to the SkySearch API."""
        await self._setup_squawk_api()
        return self.squawk_api is not None

    async def handle_squawk_alert(self, guild, aircraft_info, squawk_code):
        """Enhanced callback that gets called when a squawk alert is detected."""
        hex_code = aircraft_info.get('hex', 'Unknown')
        callsign = aircraft_info.get('flight', 'Unknown')
        
        # Log the alert
        log.info(f"🚨 ALERT DETECTED in {guild.name}: Squawk {squawk_code} for aircraft {hex_code} ({callsign})")
        
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
            
            await self._add_to_history(guild, alert_data)
            
        # Additional custom processing
        await self._process_custom_alert(guild, aircraft_info, squawk_code)

    async def _add_to_history(self, guild, alert_data):
        """Add alert to history with size management."""
        guild_config = self.config.guild(guild)
        history = await guild_config.alert_history()
        max_history = await self.config.max_history()
        
        history.append(alert_data)
        
        # Keep only the most recent alerts
        if len(history) > max_history:
            history = history[-max_history:]
            
        await guild_config.alert_history.set(history)

    async def _add_command_to_history(self, guild, command_data):
        """Add command to history with size management."""
        guild_config = self.config.guild(guild)
        history = await guild_config.command_history()
        max_history = await self.config.max_history()
        
        history.append(command_data)
        
        # Keep only the most recent commands
        if len(history) > max_history:
            history = history[-max_history:]
            
        await guild_config.command_history.set(history)

    async def _process_custom_alert(self, guild, aircraft_info, squawk_code):
        """Custom processing for different types of alerts."""
        hex_code = aircraft_info.get('hex', 'Unknown')
        
        # Different handling based on squawk code
        if squawk_code == '7700':  # General emergency
            log.info(f"🚨 GENERAL EMERGENCY detected: {hex_code}")
        elif squawk_code == '7600':  # Radio failure
            log.info(f"📻 RADIO FAILURE detected: {hex_code}")
        elif squawk_code == '7500':  # Hijacking
            log.info(f"🔒 HIJACKING ALERT detected: {hex_code}")
        
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
        enhancement_text = f"🔔 **Enhanced by SquawkExample** | Detected at {timestamp}"
        
        # Example: Add custom content to the message (only if not already added)
        if message_data.get('content'):
            if enhancement_text not in message_data['content']:
                message_data['content'] += f"\n{enhancement_text}"
        else:
            message_data['content'] = enhancement_text
        
        # Example: Modify the embed (only if not already modified)
        if message_data.get('embed'):
            embed = message_data['embed']
            
            # Check if we've already added our field
            existing_field_names = [field.name for field in embed.fields]
            if "📡 Enhanced Monitoring" not in existing_field_names:
                embed.add_field(
                    name="📡 Enhanced Monitoring", 
                    value=f"This alert is being tracked by SquawkExample cog\nDetection time: {timestamp}", 
                    inline=False
                )
            
            # Add custom footer (only if not already set)
            footer_text = f"Enhanced by SquawkExample | Original SkySearch Alert"
            if not embed.footer or embed.footer.text != footer_text:
                embed.set_footer(text=footer_text)
        
        hex_code = aircraft_info.get('hex', 'Unknown')
        log.debug(f"Modified alert message for {hex_code}")
        return message_data

    async def after_alert_sent(self, guild, aircraft_info, squawk_code, sent_message):
        """Post-send callback that runs after the alert message is sent."""
        hex_code = aircraft_info.get('hex', 'Unknown')
        log.info(f"Alert message sent in {guild.name} for aircraft {hex_code}")
        
        # Store message reference for potential updates
        alert_key = f"{guild.id}_{hex_code}_{squawk_code}"
        
        # Only schedule update if we haven't already stored this message (prevents duplicate tasks)
        if alert_key not in self.alert_messages:
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
                    log.warning("Could not add reactions - missing permissions")
                except Exception as e:
                    log.error(f"Error adding reactions: {e}")
                
                # Schedule a message update after 30 seconds (only once per alert)
                asyncio.create_task(self._schedule_message_update(sent_message, aircraft_info, squawk_code))
        else:
            log.debug(f"Skipping duplicate callback for {hex_code} - already processed")

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
                log.debug(f"Updated alert message for {aircraft_info.get('hex', 'Unknown')}")
        except discord.errors.NotFound:
            log.debug("Could not update message - message was deleted")
        except Exception as e:
            log.error(f"Error updating message: {e}")

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
                value="`history` - View recent alert history\n`stats` - View alert statistics\n`status` - Check cog status\n`clear` - Clear alert history\n`commands` - View command usage history",
                inline=False
            )
            embed.add_field(
                name="⚙️ Configuration",
                value="`toggle tracking` - Toggle alert tracking\n`toggle updates` - Toggle message updates",
                inline=False
            )
            await ctx.send(embed=embed)

    @squawk_example.command(name="commands")
    async def view_commands(self, ctx, limit: int = 10):
        """View recent SkySearch command usage history."""
        guild_config = self.config.guild(ctx.guild)
        history = await guild_config.command_history()
        
        if not history:
            await ctx.send("No command usage history found.")
            return
            
        # Get recent commands (limited)
        recent_commands = history[-limit:] if len(history) > limit else history
        recent_commands.reverse()  # Show newest first
        
        embed = discord.Embed(
            title=f"Recent Command Usage (Last {len(recent_commands)})",
            color=discord.Color.blue()
        )
        
        for i, cmd in enumerate(recent_commands[:10]):  # Show max 10 in embed
            timestamp = datetime.datetime.fromisoformat(cmd['timestamp'])
            args_str = ' '.join(cmd['args']) if cmd['args'] else 'None'
            embed.add_field(
                name=f"Command #{len(history) - i}",
                value=f"**Command:** {cmd['command_name']}\n"
                      f"**Args:** {args_str}\n"
                      f"**User:** {cmd['user_name']}\n"
                      f"**Channel:** #{cmd['channel_name']}\n"
                      f"**Time:** {timestamp.strftime('%Y-%m-%d %H:%M:%S')} UTC",
                inline=True
            )
            
        await ctx.send(embed=embed)

    @squawk_example.command(name="clear")
    async def clear_history(self, ctx):
        """Clear all alert history for this guild."""
        # Get current history count
        guild_config = self.config.guild(ctx.guild)
        alert_history = await guild_config.alert_history()
        command_history = await guild_config.command_history()
        alert_count = len(alert_history)
        command_count = len(command_history)
        
        if alert_count == 0 and command_count == 0:
            await ctx.send("❌ No history to clear.")
            return
            
        # Clear both histories
        await guild_config.alert_history.set([])
        await guild_config.command_history.set([])
        
        # Also clear active message references for this guild
        guild_keys = [key for key in self.alert_messages.keys() if key.startswith(str(ctx.guild.id))]
        for key in guild_keys:
            del self.alert_messages[key]
            
        total_cleared = alert_count + command_count
        await ctx.send(f"✅ Cleared **{alert_count}** alert(s) and **{command_count}** command(s) from history for this guild (Total: {total_cleared}).")

    @squawk_example.command(name="history")
    async def view_history(self, ctx, limit: int = 10):
        """View recent alert history."""
        history = await self.config.guild(ctx.guild).alert_history()
        
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
        """View alert and command usage statistics."""
        guild_config = self.config.guild(ctx.guild)
        alert_history = await guild_config.alert_history()
        command_history = await guild_config.command_history()
        
        if not alert_history and not command_history:
            await ctx.send("No data available for statistics.")
            return
            
        embed = discord.Embed(
            title="Usage Statistics",
            description=f"**Total alerts tracked:** {len(alert_history)}\n**Total commands tracked:** {len(command_history)}",
            color=discord.Color.green()
        )
        
        # Alert statistics
        if alert_history:
            squawk_counts = {}
            guild_counts = {}
            
            for alert in alert_history:
                squawk = alert['squawk_code']
                guild = alert['guild_name']
                
                squawk_counts[squawk] = squawk_counts.get(squawk, 0) + 1
                guild_counts[guild] = guild_counts.get(guild, 0) + 1
                
            # Top squawk codes
            if squawk_counts:
                top_squawks = sorted(squawk_counts.items(), key=lambda x: x[1], reverse=True)[:5]
                squawk_text = "\n".join([f"{code}: {count}" for code, count in top_squawks])
                embed.add_field(name="🚨 Top Squawk Codes", value=squawk_text, inline=True)
                
        # Command statistics
        if command_history:
            command_counts = {}
            user_counts = {}
            
            for cmd in command_history:
                command = cmd['command_name']
                user = cmd['user_name']
                
                command_counts[command] = command_counts.get(command, 0) + 1
                user_counts[user] = user_counts.get(user, 0) + 1
                
            # Top commands
            if command_counts:
                top_commands = sorted(command_counts.items(), key=lambda x: x[1], reverse=True)[:5]
                command_text = "\n".join([f"{cmd}: {count}" for cmd, count in top_commands])
                embed.add_field(name="🔧 Top Commands", value=command_text, inline=True)
                
            # Top users
            if user_counts:
                top_users = sorted(user_counts.items(), key=lambda x: x[1], reverse=True)[:5]
                user_text = "\n".join([f"{user}: {count}" for user, count in top_users])
                embed.add_field(name="👤 Top Users", value=user_text, inline=True)
            
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
        guild_config = self.config.guild(ctx.guild)
        alert_history = await guild_config.alert_history()
        command_history = await guild_config.command_history()
        embed.add_field(
            name="Statistics",
            value=f"Alert History: {len(alert_history)}\n"
                  f"Command History: {len(command_history)}\n"
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
    async def test_squawk_api(self, ctx, squawk_code: str = "7700"):
        """Test command to manually trigger the squawk API callbacks.
        
        Usage: *testsquawk [squawk_code]
        Examples:
        - *testsquawk        (defaults to 7700)
        - *testsquawk 7600   (test radio failure)
        - *testsquawk 7500   (test hijack)
        """
        # Validate squawk code
        valid_squawks = ['7500', '7600', '7700']
        if squawk_code not in valid_squawks:
            await ctx.send(f"❌ Invalid squawk code. Valid codes are: {', '.join(valid_squawks)}")
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
        await self.handle_squawk_alert(ctx.guild, fake_aircraft, squawk_code)
        
        # Test pre-send callback
        squawk_descriptions = {
            '7500': 'Hijack Emergency',
            '7600': 'Radio Failure Emergency', 
            '7700': 'General Emergency'
        }
        
        test_message_data = {
            'content': f'Test alert message for {squawk_code}',
            'embed': discord.Embed(
                title=f"Test {squawk_descriptions[squawk_code]}", 
                description=f"This is a test of squawk code {squawk_code}",
                color=0xff4545
            ),
            'view': None
        }
        
        modified_data = await self.modify_alert_message(ctx.guild, fake_aircraft, squawk_code, test_message_data)
        
        # Send the test message to see the modifications
        sent_message = await ctx.send(
            content=modified_data.get('content'),
            embed=modified_data.get('embed')
        )
        
        # Test post-send callback
        await self.after_alert_sent(ctx.guild, fake_aircraft, squawk_code, sent_message)
        
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
        """Enhanced debug information about SkySearch API connection and performance (owner only)."""
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
        
        embed = discord.Embed(title="🔧 SquawkExample Enhanced Debug Info", color=discord.Color.blue())
        
        if skysearch_cog:
            embed.add_field(name="SkySearch Cog", value=f"✅ Found as '{found_name}'", inline=True)
            
            if hasattr(skysearch_cog, 'squawk_api'):
                api = skysearch_cog.squawk_api
                embed.add_field(name="SquawkAPI", value="✅ Available (Enhanced)", inline=True)
                
                # Get enhanced statistics
                if hasattr(api, 'get_stats'):
                    stats = api.get_stats()
                    
                    # Basic callback info
                    embed.add_field(
                        name="📊 Callback Statistics", 
                        value=f"Total: {stats['total_callbacks']}\n"
                              f"Basic: {stats['basic_callbacks']}\n"
                              f"Pre-send: {stats['pre_send_callbacks']}\n"
                              f"Post-send: {stats['post_send_callbacks']}\n"
                              f"Enabled: {stats['enabled_callbacks']}", 
                        inline=True
                    )
                    
                    # Performance metrics
                    metrics = stats['metrics']
                    embed.add_field(
                        name="📈 Performance Metrics",
                        value=f"Total calls: {metrics['total_calls']}\n"
                              f"Successful: {metrics['successful_calls']}\n"
                              f"Failed: {metrics['failed_calls']}\n"
                              f"Alerts tracked: {stats['recent_alerts_tracked']}",
                        inline=True
                    )
                    
                    # Our callback details
                    our_callbacks = [cb for cb in stats['callback_details'] if cb['cog_name'] == 'SquawkExample']
                    if our_callbacks:
                        cb_info = []
                        for cb in our_callbacks:
                            status = "✅" if cb['enabled'] else "❌"
                            failures = f" ({cb['failure_count']} fails)" if cb['failure_count'] > 0 else ""
                            cb_info.append(f"{status} Priority {cb['priority']}{failures}")
                        
                        embed.add_field(
                            name="🎯 Our Callbacks Status",
                            value="\n".join(cb_info),
                            inline=False
                        )
                    
                    # Performance stats for our cog
                    our_stats = metrics['callback_stats'].get('SquawkExample', {})
                    if our_stats.get('calls', 0) > 0:
                        avg_time = our_stats['total_time'] / our_stats['calls'] * 1000  # Convert to ms
                        embed.add_field(
                            name="⚡ Our Performance",
                            value=f"Calls: {our_stats['calls']}\n"
                                  f"Failures: {our_stats['failures']}\n"
                                  f"Avg time: {avg_time:.1f}ms",
                            inline=True
                        )
                else:
                    # Fallback for older API
                    embed.add_field(name="Registered Callbacks", 
                                   value=f"Basic: {len(api._callbacks)}\nPre-send: {len(api._pre_send_callbacks)}\nPost-send: {len(api._post_send_callbacks)}", 
                                   inline=False)
                
                # Check background task status
                if hasattr(skysearch_cog, 'check_emergency_squawks'):
                    task = skysearch_cog.check_emergency_squawks
                    task_status = "✅ Running" if task.is_running() else "❌ Stopped"
                    embed.add_field(name="Background Task", value=task_status, inline=True)
                
            else:
                embed.add_field(name="SquawkAPI", value="❌ Not found", inline=True)
                
            # Enhanced CommandAPI connection info
            if hasattr(skysearch_cog, 'command_api'):
                cmd_api = skysearch_cog.command_api
                embed.add_field(name="CommandAPI", value="✅ Available (Enhanced)", inline=True)
                
                # Get enhanced command statistics
                if hasattr(cmd_api, 'get_stats'):
                    cmd_stats = cmd_api.get_stats()
                    
                    embed.add_field(
                        name="📊 Command Callback Stats", 
                        value=f"Total: {cmd_stats['total_callbacks']}\n"
                              f"Basic: {cmd_stats['basic_callbacks']}\n"
                              f"Pre-execute: {cmd_stats['pre_execute_callbacks']}\n"
                              f"Post-execute: {cmd_stats['post_execute_callbacks']}\n"
                              f"Active commands: {cmd_stats['active_commands']}", 
                        inline=True
                    )
                    
                    # Command performance
                    cmd_metrics = cmd_stats['metrics']
                    embed.add_field(
                        name="📈 Command Performance",
                        value=f"Total: {cmd_metrics['total_commands']}\n"
                              f"Successful: {cmd_metrics['successful_commands']}\n"
                              f"Failed: {cmd_metrics['failed_commands']}\n"
                              f"Cancelled: {cmd_metrics['cancelled_commands']}",
                        inline=True
                    )
                else:
                    # Fallback for older API
                    embed.add_field(name="Command Callbacks", 
                                   value=f"Basic: {len(cmd_api._callbacks)}\nPre-execute: {len(cmd_api._pre_execute_callbacks)}\nPost-execute: {len(cmd_api._post_execute_callbacks)}", 
                                   inline=False)
            else:
                embed.add_field(name="CommandAPI", value="❌ Not found", inline=True)
        else:
            embed.add_field(name="SkySearch Cog", value="❌ Not found", inline=True)
            
        embed.set_footer(text="Enhanced API provides detailed metrics, circuit breakers, and priority handling")
        await ctx.send(embed=embed)

    @squawk_example.command(name="apistats")
    @commands.is_owner()
    async def api_statistics(self, ctx):
        """Show detailed API performance statistics (owner only)."""
        skysearch_cog = self._get_skysearch_cog()
        if not skysearch_cog:
            await ctx.send("❌ SkySearch cog not found")
            return
            
        embeds = []
        
        # SquawkAPI Statistics
        if hasattr(skysearch_cog, 'squawk_api') and hasattr(skysearch_cog.squawk_api, 'get_stats'):
            stats = skysearch_cog.squawk_api.get_stats()
            
            embed = discord.Embed(title="🚨 SquawkAPI Performance Statistics", color=discord.Color.orange())
            
            # Overall metrics
            metrics = stats['metrics']
            success_rate = (metrics['successful_calls'] / max(metrics['total_calls'], 1)) * 100
            
            embed.add_field(
                name="📊 Overall Performance",
                value=f"Total API calls: {metrics['total_calls']}\n"
                      f"Success rate: {success_rate:.1f}%\n"
                      f"Failed calls: {metrics['failed_calls']}\n"
                      f"Active alerts: {stats['recent_alerts_tracked']}",
                inline=True
            )
            
            # Callback performance breakdown
            callback_stats = metrics['callback_stats']
            if callback_stats:
                performance_info = []
                for cog_name, cog_stats in callback_stats.items():
                    if cog_stats['calls'] > 0:
                        avg_time = (cog_stats['total_time'] / cog_stats['calls']) * 1000
                        failure_rate = (cog_stats['failures'] / cog_stats['calls']) * 100
                        performance_info.append(f"**{cog_name}:**\n  Calls: {cog_stats['calls']}\n  Avg: {avg_time:.1f}ms\n  Fails: {failure_rate:.1f}%")
                
                if performance_info:
                    embed.add_field(
                        name="🎯 Per-Cog Performance",
                        value="\n\n".join(performance_info[:3]),  # Limit to prevent overflow
                        inline=True
                    )
            
            embeds.append(embed)
        
        # CommandAPI Statistics
        if hasattr(skysearch_cog, 'command_api') and hasattr(skysearch_cog.command_api, 'get_stats'):
            cmd_stats = skysearch_cog.command_api.get_stats()
            
            embed = discord.Embed(title="⚙️ CommandAPI Performance Statistics", color=discord.Color.green())
            
            # Command metrics
            cmd_metrics = cmd_stats['metrics']
            total_commands = cmd_metrics['total_commands']
            
            if total_commands > 0:
                success_rate = (cmd_metrics['successful_commands'] / total_commands) * 100
                
                embed.add_field(
                    name="📈 Command Execution",
                    value=f"Total commands: {total_commands}\n"
                          f"Success rate: {success_rate:.1f}%\n"
                          f"Failed: {cmd_metrics['failed_commands']}\n"
                          f"Cancelled: {cmd_metrics['cancelled_commands']}\n"
                          f"Active now: {cmd_stats['active_commands']}",
                    inline=True
                )
                
                # Command performance breakdown
                command_stats = cmd_metrics['command_stats']
                if command_stats:
                    perf_info = []
                    for cmd_name, cmd_data in list(command_stats.items())[:5]:  # Top 5 commands
                        failure_rate = (cmd_data['failures'] / max(cmd_data['count'], 1)) * 100
                        perf_info.append(f"**{cmd_name}:**\n  Runs: {cmd_data['count']}\n  Avg: {cmd_data['avg_time']:.2f}s\n  Fails: {failure_rate:.1f}%")
                    
                    if perf_info:
                        embed.add_field(
                            name="🏃 Top Commands",
                            value="\n\n".join(perf_info),
                            inline=True
                        )
            else:
                embed.add_field(name="📈 Command Execution", value="No commands executed yet", inline=False)
            
            embeds.append(embed)
        
        # Send embeds
        if embeds:
            for embed in embeds:
                await ctx.send(embed=embed)
        else:
            await ctx.send("❌ No enhanced API statistics available. APIs may be using older versions.")

    @squawk_example.command(name="enablecallbacks")
    @commands.is_owner()
    async def enable_callbacks(self, ctx):
        """Re-enable any disabled callbacks for this cog (owner only)."""
        skysearch_cog = self._get_skysearch_cog()
        if not skysearch_cog:
            await ctx.send("❌ SkySearch cog not found")
            return
            
        enabled_count = 0
        
        # Re-enable SquawkAPI callbacks
        if hasattr(skysearch_cog, 'squawk_api') and hasattr(skysearch_cog.squawk_api, 'enable_callback'):
            if skysearch_cog.squawk_api.enable_callback('SquawkExample'):
                enabled_count += 1
                
        # Re-enable CommandAPI callbacks  
        if hasattr(skysearch_cog, 'command_api') and hasattr(skysearch_cog.command_api, 'enable_callback'):
            if skysearch_cog.command_api.enable_callback('SquawkExample'):
                enabled_count += 1
        
        if enabled_count > 0:
            await ctx.send(f"✅ Re-enabled callbacks for SquawkExample cog in {enabled_count} API(s)")
        else:
            await ctx.send("ℹ️ No disabled callbacks found or APIs don't support re-enabling")

# Setup function to add the cog to the bot
async def setup(bot):
    await bot.add_cog(SquawkCog(bot))

