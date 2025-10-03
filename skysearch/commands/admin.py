"""
Admin commands for SkySearch cog
"""

import discord
import asyncio
import datetime
import aiohttp
from discord.ext import commands
from redbot.core.i18n import Translator, cog_i18n
from ..utils.stats import build_stats_embed, build_stats_charts, build_stats_config_embed

_ = Translator("Skysearch", __file__)


@cog_i18n(_)
class AdminCommands:
    """Admin-related commands for SkySearch."""
    
    def __init__(self, cog):
        self.cog = cog
    
    async def set_alert_channel(self, ctx, channel: discord.TextChannel = None):
        """Set or clear a channel to send emergency squawk alerts to. Clear with no channel."""
        if channel:
            try:
                await self.cog.config.guild(ctx.guild).alert_channel.set(channel.id)
                embed = discord.Embed(description=_("Alert channel set to {channel}").format(channel=channel.mention), color=0xfffffe)
                await ctx.send(embed=embed)
            except Exception as e:
                embed = discord.Embed(description=f"Error setting alert channel: {e}", color=0xff4545)
                await ctx.send(embed=embed)
        else:
            try:
                await self.cog.config.guild(ctx.guild).alert_channel.clear()
                embed = discord.Embed(description=_("Alert channel cleared. No more alerts will be sent."), color=0xfffffe)
                await ctx.send(embed=embed)
            except Exception as e:
                embed = discord.Embed(description=f"Error clearing alert channel: {e}", color=0xff4545)
                await ctx.send(embed=embed)
    
    async def set_alert_role(self, ctx, role: discord.Role = None):
        """Set or clear a role to mention when new emergency squawks occur. Clear with no role."""
        if role:
            try:
                await self.cog.config.guild(ctx.guild).alert_role.set(role.id)
                embed = discord.Embed(description=_("Alert role set to {role}").format(role=role.mention), color=0xfffffe)
                await ctx.send(embed=embed)
            except Exception as e:
                embed = discord.Embed(description=f"Error setting alert role: {e}", color=0xff4545)
                await ctx.send(embed=embed)
        else:
            try:
                await self.cog.config.guild(ctx.guild).alert_role.clear()
                embed = discord.Embed(description=_("Alert role cleared. No more role mentions will be made."), color=0xfffffe)
                await ctx.send(embed=embed)
            except Exception as e:
                embed = discord.Embed(description=f"Error clearing alert role: {e}", color=0xff4545)
                await ctx.send(embed=embed)

    async def set_alert_cooldown(self, ctx, duration: str = None):
        """Set or show the cooldown for emergency squawk alerts.
        
        Parameters:
        -----------
        duration: str, optional
            The duration to set for the cooldown.
            Can be in minutes (e.g. "5") or seconds (e.g. "30s")
            If not provided, shows the current cooldown setting.
            Default is 5 minutes.
        """
        if duration is not None:
            try:
                if duration.endswith('s'):
                    # Convert seconds to minutes
                    seconds = int(duration[:-1])
                    minutes = seconds / 60
                elif duration.endswith('m'):
                    minutes = int(duration[:-1])
                else:
                    minutes = int(duration)
                
                if minutes < 0:
                    await ctx.send(_("Cooldown must be a positive number."))
                    return
                
                await self.cog.config.guild(ctx.guild).emergency_cooldown.set(minutes)
                if minutes < 1:
                    await ctx.send(_("Emergency alert cooldown set to {seconds} seconds.").format(seconds=int(minutes * 60)))
                else:
                    await ctx.send(_("Emergency alert cooldown set to {minutes} minutes.").format(minutes=int(minutes)))
            except ValueError:
                await ctx.send(_("Invalid duration format. Use a number (e.g. '5'), minutes ('5m'), or seconds ('30s')"))
        else:
            cooldown = await self.cog.config.guild(ctx.guild).emergency_cooldown()
            if cooldown < 1:
                await ctx.send(_("Current emergency alert cooldown is {seconds} seconds.").format(seconds=int(cooldown * 60)))
            else:
                await ctx.send(_("Current emergency alert cooldown is {minutes} minutes.").format(minutes=int(cooldown)))

    async def autoicao(self, ctx, state: bool = None):
        """Enable or disable automatic ICAO lookup."""
        if state is None:
            auto_icao_state = await self.cog.config.guild(ctx.guild).auto_icao()
            auto_delete_state = await self.cog.config.guild(ctx.guild).auto_delete_not_found()
            
            embed = discord.Embed(title=_("Auto Settings Status"), color=0x2BBD8E)
            
            if auto_icao_state:
                embed.add_field(name=_("ICAO Lookup"), value=_("✅ **Enabled** - Automatic ICAO lookup is active"), inline=False)
            else:
                embed.add_field(name="ICAO Lookup", value="❌ **Disabled** - Automatic ICAO lookup is inactive", inline=False)
                
            if auto_delete_state:
                embed.add_field(name="Auto-Delete", value="✅ **Enabled** - 'Not found' messages will be deleted after 5 seconds", inline=False)
            else:
                embed.add_field(name="Auto-Delete", value="❌ **Disabled** - 'Not found' messages will remain visible", inline=False)
                
            await ctx.send(embed=embed)
        else:
            await self.cog.config.guild(ctx.guild).auto_icao.set(state)
            if state:
                embed = discord.Embed(title="ICAO Lookup Status", description="Automatic ICAO lookup has been enabled.", color=0x2BBD8E)
                await ctx.send(embed=embed)
            else:
                embed = discord.Embed(title="ICAO Lookup Status", description="Automatic ICAO lookup has been disabled.", color=0xff4545)
                await ctx.send(embed=embed)

    async def autodelete(self, ctx, state: bool = None):
        """Enable or disable automatic deletion of 'not found' messages."""
        if state is None:
            state = await self.cog.config.guild(ctx.guild).auto_delete_not_found()
            if state:
                embed = discord.Embed(title="Auto-Delete Status", description="Automatic deletion of 'not found' messages is currently enabled.", color=0x2BBD8E)
                embed.add_field(name="Behavior", value="Messages will be automatically deleted after 5 seconds when no aircraft is found.", inline=False)
                await ctx.send(embed=embed)
            else:
                embed = discord.Embed(title="Auto-Delete Status", description="Automatic deletion of 'not found' messages is currently disabled.", color=0xff4545)
                embed.add_field(name="Behavior", value="Messages will remain visible when no aircraft is found.", inline=False)
                await ctx.send(embed=embed)
        else:
            await self.cog.config.guild(ctx.guild).auto_delete_not_found.set(state)
            if state:
                embed = discord.Embed(title="Auto-Delete Status", description="Automatic deletion of 'not found' messages has been enabled.", color=0x2BBD8E)
                embed.add_field(name="Behavior", value="Messages will be automatically deleted after 5 seconds when no aircraft is found.", inline=False)
                await ctx.send(embed=embed)
            else:
                embed = discord.Embed(title="Auto-Delete Status", description="Automatic deletion of 'not found' messages has been disabled.", color=0xff4545)
                embed.add_field(name="Behavior", value="Messages will remain visible when no aircraft is found.", inline=False)
                await ctx.send(embed=embed)

    async def list_alert_channels(self, ctx):
        """Show alert channel status and task information."""
        guild = ctx.guild
        embed = discord.Embed(title=f"Squawk alerts for {guild.name}", color=0xfffffe)
        alert_channel_id = await self.cog.config.guild(guild).alert_channel()
        if alert_channel_id:
            alert_channel = self.cog.bot.get_channel(alert_channel_id)
            if alert_channel:
                next_iteration = self.cog.check_emergency_squawks.next_iteration
                now = datetime.datetime.now(datetime.timezone.utc)
                if next_iteration:
                    time_remaining = (next_iteration - now).total_seconds()
                    if time_remaining > 0: 
                        time_remaining_formatted = f"<t:{int(now.timestamp() + time_remaining)}:R>"
                    else:
                        time_remaining_formatted = "Now"
                else:
                    time_remaining = self.cog.check_emergency_squawks.seconds
                    if time_remaining > 0:
                        time_remaining_formatted = f"<t:{int(now.timestamp() + time_remaining)}:R>"
                    else:
                        time_remaining_formatted = "Now"
                if self.cog.check_emergency_squawks.is_running():
                    last_check_status = f":white_check_mark: **Checked successfully, next checking {time_remaining_formatted}**"
                else:
                    last_check_status = f":x: **Last check failed, retrying {time_remaining_formatted}**"
                embed.add_field(name="Status", value=f"Channel: {alert_channel.mention}\nLast check: {last_check_status}", inline=False)
                
                last_emergency_squawk_time = await self.cog.config.guild(guild).last_emergency_squawk_time()
                if last_emergency_squawk_time:
                    last_emergency_squawk_time_formatted = f"<t:{int(last_emergency_squawk_time)}:F>"
                    embed.add_field(name="Last Emergency Squawk", value=f"Time: {last_emergency_squawk_time_formatted}", inline=False)
                else:
                    embed.add_field(name="Last Emergency Squawk", value="No emergency squawks yet.", inline=False)
            else:
                embed.add_field(name="Status", value="No alert channel set.", inline=False)
        else:
            embed.add_field(name="Status", value="No alert channel set.", inline=False)
        await ctx.send(embed=embed)

    async def set_api_key(self, ctx, api_key: str):
        """Set the airplanes.live API key."""
        await self.cog.config.airplanesliveapi.set(api_key)
        embed = discord.Embed(title="API Key Updated", description="The airplanes.live API key has been set successfully.", color=0x2BBD8E)
        embed.add_field(name="Status", value="✅ API key configured", inline=True)
        embed.add_field(name="Header", value="`auth: [your-api-key]`", inline=True)
        await ctx.send(embed=embed)

    async def check_api_key(self, ctx):
        """Check API key status."""
        api_key = await self.cog.config.airplanesliveapi()
        if api_key:
            embed = discord.Embed(title="API Key Status", description="✅ API key is configured", color=0x2BBD8E)
            embed.add_field(name="Status", value="Configured", inline=True)
            embed.add_field(name="Key Preview", value=f"`{api_key[:8]}...`", inline=True)
            embed.add_field(name="Header Format", value="`auth: [your-api-key]`", inline=True)
        else:
            embed = discord.Embed(title="API Key Status", description="❌ No API key configured", color=0xff4545)
            embed.add_field(name="Status", value="Not configured", inline=True)
            embed.add_field(name="Usage", value="Use `setapikey <your-api-key>` to configure", inline=True)
            embed.add_field(name="Note", value="Some features may be limited without an API key", inline=True)
        await ctx.send(embed=embed)

    async def clear_api_key(self, ctx):
        """Clear the airplanes.live API key."""
        await self.cog.config.airplanesliveapi.clear()
        embed = discord.Embed(title="API Key Cleared", description="The airplanes.live API key has been cleared.", color=0xff4545)
        embed.add_field(name="Status", value="❌ API key removed", inline=True)
        embed.add_field(name="Note", value="Some features may be limited without an API key", inline=True)
        await ctx.send(embed=embed)

    async def debug_api(self, ctx):
        """Debug API key and connection issues - sends detailed info via DM."""
        try:
            # Check if we can DM the user
            try:
                await ctx.author.send("🔧 **airplanes.live API Debug Test**\n\nStarting comprehensive API diagnostics...")
            except discord.Forbidden:
                await ctx.send("❌ **Error:** I cannot send you a DM. Please enable DMs from server members and try again.")
                return

            # Get API key status
            api_key = await self.cog.config.airplanesliveapi()
            api_mode = await self.cog.config.api_mode()
            debug_info = f"**API Key Status:**\n"
            if api_key:
                debug_info += f"✅ **Configured:** `{api_key[:8]}...`\n"
                debug_info += f"📏 **Length:** {len(api_key)} characters\n"
            else:
                debug_info += f"❌ **Not configured**\n"
            
            debug_info += f"\n**Headers being sent:**\n"
            headers = await self.cog.api.get_headers(api_mode=api_mode)
            debug_info += f"```{headers}```\n"

            # Get the base URL for testing
            base_url = self.cog.api.get_primary_api_url() if api_mode == "primary" else self.cog.api.get_fallback_api_url()
            
            # Test basic connectivity
            debug_info += f"**Testing basic connectivity...**\n"
            try:
                # Ensure HTTP client is initialized
                if not self.cog.api._http_client:
                    self.cog.api._http_client = aiohttp.ClientSession()
                
                # Test without API key first
                test_url = f"{base_url}/?all_with_pos"
                debug_info += f"🔗 **Test URL:** `{test_url}`\n"
                
                async with self.cog.api._http_client.get(test_url) as response:
                    debug_info += f"📡 **Response Status:** {response.status}\n"
                    debug_info += f"📋 **Response Headers:** `{dict(response.headers)}`\n"
                    
                    if response.status == 200:
                        debug_info += f"✅ **Basic connectivity:** Working\n"
                    else:
                        debug_info += f"❌ **Basic connectivity:** Failed (Status {response.status})\n"
                        
            except Exception as e:
                debug_info += f"❌ **Connectivity Error:** {str(e)}\n"

            # Test with API key if available
            if api_key:
                debug_info += f"\n**Testing with API key...**\n"
                try:
                    test_url_with_key = f"{base_url}/?all_with_pos"
                    import time
                    start = time.monotonic()
                    async with self.cog.api._http_client.get(test_url_with_key, headers=headers) as response:
                        elapsed = time.monotonic() - start
                        debug_info += f"📡 **Authenticated Status:** {response.status}\n"
                        debug_info += f"⏱️ **API Latency:** {elapsed:.2f} seconds\n"
                        if response.status == 200:
                            debug_info += f"✅ **Authentication:** Working\n"
                            try:
                                data = await response.json()
                                debug_info += f"📊 **Response Keys:** `{list(data.keys())}`\n"
                                if 'aircraft' in data:
                                    debug_info += f"✈️ **Aircraft Count:** {len(data['aircraft'])} aircraft\n"
                                # Removed requests remaining/rate limit info
                            except Exception as e:
                                debug_info += f"❌ **JSON Parse Error:** {str(e)}\n"
                        elif response.status == 401:
                            debug_info += f"❌ **Authentication:** Failed - Invalid API key\n"
                        elif response.status == 403:
                            debug_info += f"❌ **Authentication:** Failed - Insufficient permissions\n"
                        elif response.status == 429:
                            debug_info += f"❌ **Rate Limit:** Exceeded\n"
                        else:
                            debug_info += f"❌ **Authentication:** Failed - Status {response.status}\n"
                            
                except Exception as e:
                    debug_info += f"❌ **API Test Error:** {str(e)}\n"

            # Test specific endpoints
            debug_info += f"\n**Testing specific endpoints...**\n"
            test_endpoints = [
                ("Military aircraft", f"{base_url}/?all_with_pos&filter_mil"),
                ("LADD aircraft", f"{base_url}/?all_with_pos&filter_ladd"),
                ("PIA aircraft", f"{base_url}/?all_with_pos&filter_pia"),
                ("Emergency squawk 7700", f"{base_url}/?all_with_pos&filter_squawk=7700")
            ]
            
            for endpoint_name, endpoint_url in test_endpoints:
                try:
                    async with self.cog.api._http_client.get(endpoint_url, headers=headers) as response:
                        debug_info += f"🔗 **{endpoint_name}:** Status {response.status}\n"
                        if response.status == 200:
                            try:
                                data = await response.json()
                                if 'aircraft' in data:
                                    debug_info += f"   ✈️ Found {len(data['aircraft'])} aircraft\n"
                            except:
                                pass
                except Exception as e:
                    debug_info += f"❌ **{endpoint_name}:** Error - {str(e)}\n"

            # Test both API modes with comprehensive endpoints
            debug_info += f"\n**Testing both API modes...**\n"
            
            # Test Primary API
            debug_info += f"\n**🔗 Primary API Testing:**\n"
            primary_url = f"{self.cog.api.get_primary_api_url()}/?all_with_pos"
            debug_info += f"🔗 **Primary Test URL:** `{primary_url}`\n"
            try:
                import time
                start = time.monotonic()
                async with self.cog.api._http_client.get(primary_url, headers=headers) as response:
                    elapsed = time.monotonic() - start
                    debug_info += f"📡 **Primary Status:** {response.status}\n"
                    debug_info += f"⏱️ **Primary API Latency:** {elapsed:.2f} seconds\n"
                    if response.status == 200:
                        try:
                            data = await response.json()
                            debug_info += f"📊 **Primary Response Keys:** `{list(data.keys())}`\n"
                            if 'aircraft' in data:
                                debug_info += f"✈️ **Primary Aircraft Count:** {len(data['aircraft'])} aircraft\n"
                        except Exception as e:
                            debug_info += f"❌ **Primary JSON Parse Error:** {str(e)}\n"
                    else:
                        debug_info += f"❌ **Primary failed:** Status {response.status}\n"
            except Exception as e:
                debug_info += f"❌ **Primary Test Error:** {str(e)}\n"
            
            # Test Fallback API with multiple endpoints
            debug_info += f"\n**🔗 Fallback API Testing:**\n"
            fallback_endpoints = [
                ("Military aircraft", f"{self.cog.api.get_fallback_api_url()}/v2/mil"),
                ("LADD aircraft", f"{self.cog.api.get_fallback_api_url()}/v2/ladd"),
                ("PIA aircraft", f"{self.cog.api.get_fallback_api_url()}/v2/pia"),
                ("Emergency squawk 7700", f"{self.cog.api.get_fallback_api_url()}/v2/squawk/7700"),
                ("All aircraft with positions", f"{self.cog.api.get_fallback_api_url()}/v2/all")
            ]
            
            for endpoint_name, test_url in fallback_endpoints:
                debug_info += f"🔗 **Fallback Test URL:** `{test_url}`\n"
                try:
                    import time
                    start = time.monotonic()
                    # Note: Fallback API doesn't use API key in headers
                    fallback_headers = {}  # No API key for fallback
                    async with self.cog.api._http_client.get(test_url, headers=fallback_headers) as response:
                        elapsed = time.monotonic() - start
                        debug_info += f"📡 **Fallback Status:** {response.status}\n"
                        debug_info += f"⏱️ **Fallback API Latency:** {elapsed:.2f} seconds\n"
                        if response.status == 200:
                            try:
                                data = await response.json()
                                debug_info += f"📊 **Fallback Response Keys:** `{list(data.keys())}`\n"
                                # Handle different response structures
                                aircraft_count = 0
                                if 'aircraft' in data:
                                    aircraft_count = len(data['aircraft'])
                                elif 'ac' in data:
                                    aircraft_count = len(data['ac'])
                                elif isinstance(data, list):
                                    aircraft_count = len(data)
                                
                                if aircraft_count > 0:
                                    debug_info += f"✈️ **Fallback Aircraft Count:** {aircraft_count} aircraft\n"
                                else:
                                    debug_info += f"✈️ **Fallback Aircraft Count:** 0 aircraft (endpoint may be empty)\n"
                            except Exception as e:
                                debug_info += f"❌ **Fallback JSON Parse Error:** {str(e)}\n"
                        else:
                            debug_info += f"❌ **Fallback failed:** Status {response.status}\n"
                except Exception as e:
                    debug_info += f"❌ **Fallback Test Error:** {str(e)}\n"

            # Final summary
            debug_info += f"\n**📋 Summary:**\n"
            debug_info += f"• **API Base URL (primary):** `{self.cog.api.get_primary_api_url()}`\n"
            debug_info += f"• **API Base URL (fallback):** `{self.cog.api.get_fallback_api_url()}`\n"
            debug_info += f"• **Current Mode:** `{await self.cog.config.api_mode()}`\n"
            debug_info += f"• **API Key:** {'✅ Configured' if api_key else '❌ Not configured'}\n"
            debug_info += f"• **Session:** {'✅ Active' if hasattr(self.cog, '_http_client') else '❌ Not initialized'}\n"
            debug_info += f"\n**🔍 Fallback API Notes:**\n"
            debug_info += f"• Fallback API uses different endpoint structure (`/v2/` paths)\n"
            debug_info += f"• Fallback API does not require API key authentication\n"
            debug_info += f"• Fallback API has different response format (may use 'ac' instead of 'aircraft')\n"
            debug_info += f"• Some fallback endpoints may return empty results depending on current aircraft activity\n"
            
            # Send the debug info in chunks if it's too long
            if len(debug_info) > 2000:
                # Use 1900 as chunk size to stay under Discord's 2000 char limit and avoid errors
                chunks = [debug_info[i:i+1900] for i in range(0, len(debug_info), 1900)]
                for i, chunk in enumerate(chunks):
                    await ctx.author.send(f"**Debug Info (Part {i+1}/{len(chunks)}):**\n```{chunk}```")
            else:
                await ctx.author.send(f"**Debug Info:**\n```{debug_info}```")

            await ctx.send("✅ **Debug complete!** Check your DMs for detailed information.")

        except Exception as e:
            try:
                await ctx.author.send(f"❌ **Debug Error:** {str(e)}")
            except:
                await ctx.send(f"❌ **Debug Error:** {str(e)}")
            await ctx.send("❌ **Debug failed!** Check your DMs for error details.") 

    async def set_owm_key(self, ctx, api_key: str):
        """Set the OpenWeatherMap API key."""
        await self.cog.config.openweathermap_api.set(api_key)
        embed = discord.Embed(title="OpenWeatherMap API Key Updated", description="The OpenWeatherMap API key has been set successfully.", color=0x2BBD8E)
        embed.add_field(name="Status", value="✅ OWM API key configured", inline=True)
        await ctx.send(embed=embed)

    async def check_owm_key(self, ctx):
        """Show the current OpenWeatherMap API key (partially masked)."""
        key = await self.cog.config.openweathermap_api()
        if key:
            masked = f"{key[:4]}{'*' * (len(key) - 8)}{key[-4:]}" if len(key) > 8 else key
            await ctx.send(f"OpenWeatherMap API key: `{masked}`")
        else:
            await ctx.send("No OpenWeatherMap API key set.")

    async def clear_owm_key(self, ctx):
        """Clear the OpenWeatherMap API key."""
        await self.cog.config.openweathermap_api.set(None)
        await ctx.send("OpenWeatherMap API key cleared.") 

    async def apistats(self, ctx):
        """Show comprehensive API request statistics and charts."""
        await self.cog.api.wait_for_stats_initialization()
        api_stats = self.cog.api.get_request_stats()
        embed = build_stats_embed(api_stats, _)
        await ctx.send(embed=embed)
        chart_embeds = build_stats_charts(api_stats, _)
        if chart_embeds:
            try:
                await ctx.send(embeds=chart_embeds)
            except Exception:
                for e in chart_embeds:
                    try:
                        await ctx.send(embed=e)
                    except Exception:
                        continue

    async def apistats_reset(self, ctx):
        """Reset API request statistics."""
        self.cog.api.reset_request_stats()
        embed = discord.Embed(
            title="🔄 API Statistics Reset",
            description="All API request statistics have been reset to zero.",
            color=0xffaa00
        )
        await ctx.send(embed=embed)

    async def apistats_save(self, ctx):
        """Manually save API statistics to config."""
        try:
            await self.cog.api.wait_for_stats_initialization()
            await self.cog.api._save_stats_to_config()
            embed = discord.Embed(
                title="💾 API Statistics Saved",
                description="API request statistics have been manually saved to config.",
                color=0x00ff00
            )
            await ctx.send(embed=embed)
        except Exception as e:
            embed = discord.Embed(
                title="❌ Save Error",
                description=f"Error saving API statistics: {str(e)}",
                color=0xff0000
            )
            await ctx.send(embed=embed)

    async def apistats_config(self, ctx):
        """View API statistics auto-save configuration and current status."""
        try:
            await self.cog.api.wait_for_stats_initialization()
            save_config = self.cog.api.get_save_config()
            embed = build_stats_config_embed(save_config, _)
            await ctx.send(embed=embed)
        except Exception as e:
            embed = discord.Embed(
                title="❌ Config Error",
                description=f"Error viewing save configuration: {str(e)}",
                color=0xff0000
            )
            await ctx.send(embed=embed)

    async def apistats_debug(self, ctx):
        """Debug API statistics data structure (owner only)."""
        try:
            await self.cog.api.wait_for_stats_initialization()
            api_stats = self.cog.api.get_request_stats()
            
            # Get time-based data
            hourly = api_stats.get("hourly_requests", {})
            daily = api_stats.get("daily_requests", {})
            
            # Count non-zero entries
            hourly_count = len([h for h in hourly.values() if h > 0])
            daily_count = len([d for d in daily.values() if d > 0])
            
            # Get date ranges
            if hourly:
                hourly_hours = sorted([int(h) for h in hourly.keys() if hourly.get(h, 0) > 0])
                if hourly_hours:
                    oldest_hour = datetime.datetime.fromtimestamp(hourly_hours[0] * 3600).strftime("%Y-%m-%d %H:%M")
                    newest_hour = datetime.datetime.fromtimestamp(hourly_hours[-1] * 3600).strftime("%Y-%m-%d %H:%M")
                else:
                    oldest_hour = newest_hour = "No data"
            else:
                oldest_hour = newest_hour = "No data"
            
            if daily:
                daily_days = sorted([int(d) for d in daily.keys() if daily.get(d, 0) > 0])
                if daily_days:
                    oldest_day = datetime.datetime.fromtimestamp(daily_days[0] * 86400).strftime("%Y-%m-%d")
                    newest_day = datetime.datetime.fromtimestamp(daily_days[-1] * 86400).strftime("%Y-%m-%d")
                else:
                    oldest_day = newest_day = "No data"
            else:
                oldest_day = newest_day = "No data"
            
            embed = discord.Embed(
                title="🔍 API Statistics Debug Info",
                description="Detailed breakdown of time-based data structures",
                color=0x00AAFF
            )
            
            embed.add_field(
                name="📊 Data Summary",
                value=(
                    f"**Total Requests:** {api_stats.get('total_requests', 0):,}\n"
                    f"**Hourly Entries:** {hourly_count} (with data > 0)\n"
                    f"**Daily Entries:** {daily_count} (with data > 0)\n"
                    f"**Last Request:** {api_stats.get('last_request_time_formatted', 'Never')}"
                ),
                inline=False
            )
            
            embed.add_field(
                name="⏰ Hourly Data Range",
                value=(
                    f"**Oldest:** {oldest_hour}\n"
                    f"**Newest:** {newest_hour}\n"
                    f"**Total Hours:** {len(hourly_hours) if hourly_hours else 0}"
                ),
                inline=True
            )
            
            embed.add_field(
                name="📅 Daily Data Range",
                value=(
                    f"**Oldest:** {oldest_day}\n"
                    f"**Newest:** {newest_day}\n"
                    f"**Total Days:** {len(daily_days) if daily_days else 0}"
                ),
                inline=True
            )
            
            # Show sample data
            if hourly_hours:
                sample_hours = hourly_hours[-5:]  # Last 5 hours with data
                sample_data = []
                for h in sample_hours:
                    count = hourly.get(h, 0)
                    timestamp = datetime.datetime.fromtimestamp(h * 3600).strftime("%m/%d %H:%M")
                    sample_data.append(f"{timestamp}: {count:,}")
                embed.add_field(
                    name="📈 Recent Hourly Data (last 5)",
                    value="\n".join(sample_data) if sample_data else "No data",
                    inline=False
                )
            
            await ctx.send(embed=embed)
            
        except Exception as e:
            embed = discord.Embed(
                title="❌ Debug Error",
                description=f"Error getting debug info: {str(e)}",
                color=0xff0000
            )
            await ctx.send(embed=embed)