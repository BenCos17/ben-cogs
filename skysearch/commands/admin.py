"""
Admin commands for SkySearch cog
"""

import discord
import asyncio
import datetime
import aiohttp
from discord.ext import commands
from redbot.core import commands as red_commands


class AdminCommands:
    """Admin-related commands for SkySearch."""
    
    def __init__(self, cog):
        self.cog = cog
    
    @red_commands.guild_only()
    @red_commands.admin_or_permissions()
    @red_commands.group(name='aircraft', help='Command center for aircraft related commands')
    async def aircraft_group(self, ctx):
        """Command center for aircraft related commands"""
        # This will be handled by the main cog

    @red_commands.guild_only()
    @red_commands.admin_or_permissions()
    @aircraft_group.command(name='alertchannel', help='Set or clear a channel to send emergency squawk alerts to. Clear with no channel.')
    async def set_alert_channel(self, ctx, channel: discord.TextChannel = None):
        """Set or clear the alert channel for emergency squawks."""
        if channel:
            try:
                await self.cog.config.guild(ctx.guild).alert_channel.set(channel.id)
                embed = discord.Embed(description=f"Alert channel set to {channel.mention}", color=0xfffffe)
                await ctx.send(embed=embed)
            except Exception as e:
                embed = discord.Embed(description=f"Error setting alert channel: {e}", color=0xff4545)
                await ctx.send(embed=embed)
        else:
            try:
                await self.cog.config.guild(ctx.guild).alert_channel.clear()
                embed = discord.Embed(description="Alert channel cleared. No more alerts will be sent.", color=0xfffffe)
                await ctx.send(embed=embed)
            except Exception as e:
                embed = discord.Embed(description=f"Error clearing alert channel: {e}", color=0xff4545)
                await ctx.send(embed=embed)
    
    @red_commands.guild_only()
    @red_commands.admin_or_permissions()
    @aircraft_group.command(name='alertrole', help='Set or clear a role to mention when new emergency squawks occur. Clear with no role.')
    async def set_alert_role(self, ctx, role: discord.Role = None):
        """Set or clear the alert role for emergency squawks."""
        if role:
            try:
                await self.cog.config.guild(ctx.guild).alert_role.set(role.id)
                embed = discord.Embed(description=f"Alert role set to {role.mention}", color=0xfffffe)
                await ctx.send(embed=embed)
            except Exception as e:
                embed = discord.Embed(description=f"Error setting alert role: {e}", color=0xff4545)
                await ctx.send(embed=embed)
        else:
            try:
                await self.cog.config.guild(ctx.guild).alert_role.clear()
                embed = discord.Embed(description="Alert role cleared. No more role mentions will be made.", color=0xfffffe)
                await ctx.send(embed=embed)
            except Exception as e:
                embed = discord.Embed(description=f"Error clearing alert role: {e}", color=0xff4545)
                await ctx.send(embed=embed)

    @red_commands.guild_only()
    @red_commands.has_permissions(manage_guild=True)
    @aircraft_group.command(name='autoicao')
    async def autoicao(self, ctx, state: bool = None):
        """Enable or disable automatic ICAO lookup."""
        if state is None:
            auto_icao_state = await self.cog.config.guild(ctx.guild).auto_icao()
            auto_delete_state = await self.cog.config.guild(ctx.guild).auto_delete_not_found()
            
            embed = discord.Embed(title="Auto Settings Status", color=0x2BBD8E)
            
            if auto_icao_state:
                embed.add_field(name="ICAO Lookup", value="✅ **Enabled** - Automatic ICAO lookup is active", inline=False)
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

    @red_commands.guild_only()
    @red_commands.has_permissions(manage_guild=True)
    @aircraft_group.command(name='autodelete', aliases=['autodel'], help='Enable or disable automatic deletion of "not found" messages.')
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

    @red_commands.guild_only()
    @aircraft_group.command(name='showalertchannel', help='Show alert task status and output if set')
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

    @red_commands.is_owner()
    @red_commands.command(name='setapikey', help='Set the API key for Skysearch.')
    async def set_api_key(self, ctx, api_key: str):
        """Set the airplanes.live API key."""
        await self.cog.config.airplanesliveapi.set(api_key)
        embed = discord.Embed(title="API Key Updated", description="The airplanes.live API key has been set successfully.", color=0x2BBD8E)
        embed.add_field(name="Status", value="✅ API key configured", inline=True)
        embed.add_field(name="Header", value="`auth: [your-api-key]`", inline=True)
        await ctx.send(embed=embed)

    @red_commands.is_owner()
    @red_commands.command(name='apikey', help='Check the status of the API key configuration.')
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

    @red_commands.is_owner()
    @red_commands.command(name='clearapikey', help='Clear the API key configuration.')
    async def clear_api_key(self, ctx):
        """Clear the airplanes.live API key."""
        await self.cog.config.airplanesliveapi.clear()
        embed = discord.Embed(title="API Key Cleared", description="The airplanes.live API key has been cleared.", color=0xff4545)
        embed.add_field(name="Status", value="❌ API key removed", inline=True)
        embed.add_field(name="Note", value="Some features may be limited without an API key", inline=True)
        await ctx.send(embed=embed)

    @red_commands.is_owner()
    @red_commands.command(name='debugapi', help='Debug API key and connection issues (DM only)')
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
            debug_info = f"**API Key Status:**\n"
            if api_key:
                debug_info += f"✅ **Configured:** `{api_key[:8]}...`\n"
                debug_info += f"📏 **Length:** {len(api_key)} characters\n"
            else:
                debug_info += f"❌ **Not configured**\n"
            
            debug_info += f"\n**Headers being sent:**\n"
            headers = await self.cog.api.get_headers()
            debug_info += f"```{headers}```\n"

            # Test basic connectivity
            debug_info += f"**Testing basic connectivity...**\n"
            try:
                if not hasattr(self.cog, '_http_client'):
                    self.cog._http_client = aiohttp.ClientSession()
                
                # Test without API key first
                test_url = f"{self.cog.api.api_url}/?all_with_pos"
                debug_info += f"🔗 **Test URL:** `{test_url}`\n"
                
                async with self.cog._http_client.get(test_url) as response:
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
                    test_url_with_key = f"{self.cog.api.api_url}/?all_with_pos"
                    async with self.cog._http_client.get(test_url_with_key, headers=headers) as response:
                        debug_info += f"📡 **Authenticated Status:** {response.status}\n"
                        
                        if response.status == 200:
                            debug_info += f"✅ **Authentication:** Working\n"
                            try:
                                data = await response.json()
                                debug_info += f"📊 **Response Keys:** `{list(data.keys())}`\n"
                                if 'aircraft' in data:
                                    debug_info += f"✈️ **Aircraft Count:** {len(data['aircraft'])} aircraft\n"
                                debug_info += f"⏱️ **Response Time:** {response.headers.get('X-RateLimit-Remaining', 'Unknown')} requests remaining\n"
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
                ("Military aircraft", f"{self.cog.api.api_url}/?all_with_pos&filter_mil"),
                ("LADD aircraft", f"{self.cog.api.api_url}/?all_with_pos&filter_ladd"),
                ("PIA aircraft", f"{self.cog.api.api_url}/?all_with_pos&filter_pia"),
                ("Emergency squawk 7700", f"{self.cog.api.api_url}/?all_with_pos&filter_squawk=7700")
            ]
            
            for endpoint_name, endpoint_url in test_endpoints:
                try:
                    async with self.cog._http_client.get(endpoint_url, headers=headers) as response:
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

            # Final summary
            debug_info += f"\n**📋 Summary:**\n"
            debug_info += f"• **API Base URL:** `{self.cog.api.api_url}`\n"
            debug_info += f"• **API Key:** {'✅ Configured' if api_key else '❌ Not configured'}\n"
            debug_info += f"• **Session:** {'✅ Active' if hasattr(self.cog, '_http_client') else '❌ Not initialized'}\n"
            
            # Send the debug info in chunks if it's too long
            if len(debug_info) > 2000:
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