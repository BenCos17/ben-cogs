# SkySearch API Documentation

This document provides comprehensive documentation for the SkySearch API system, which allows other cogs to integrate with and extend SkySearch functionality.

## 📋 Table of Contents

1. [Overview](#overview)
2. [SquawkAlertAPI](#squawkalertapi)
3. [CommandAPI](#commandapi)
4. [Integration Examples](#integration-examples)
5. [Best Practices](#best-practices)
6. [Troubleshooting](#troubleshooting)

---

## 🔍 Overview

The SkySearch cog provides two main APIs for integration:

- **SquawkAlertAPI**: Hook into aircraft emergency alerts (7500, 7600, 7700 squawk codes)
- **CommandAPI**: Monitor and interact with SkySearch command execution

Both APIs use a callback-based system that allows other cogs to register functions to be called when specific events occur.

---

## 🚨 SquawkAlertAPI

The SquawkAlertAPI allows other cogs to respond to aircraft emergency alerts detected by SkySearch's background monitoring system.

### 📍 Location
```
skysearch/api/squawk_api.py
```

### 🎯 Purpose
- Monitor aircraft emergency squawk codes (7500, 7600, 7700)
- Modify alert messages before they're sent
- React to alert messages after they're sent
- Add custom processing for emergency situations

### 🔧 Available Callback Types

#### 1. Basic Callbacks
Called when an emergency alert is detected.

**Signature:**
```python
async def callback(guild, aircraft_info, squawk_code):
    # Your code here
    pass
```

**Parameters:**
- `guild` (discord.Guild): The Discord guild where the alert occurred
- `aircraft_info` (dict): Aircraft data from the API
- `squawk_code` (str): The emergency squawk code ('7500', '7600', or '7700')

#### 2. Pre-Send Callbacks
Called before an alert message is sent, allows message modification.

**Signature:**
```python
async def callback(guild, aircraft_info, squawk_code, message_data):
    # Modify message_data
    message_data['content'] += "\nCustom addition!"
    return message_data  # or return None for no changes
```

**Parameters:**
- `guild` (discord.Guild): The Discord guild
- `aircraft_info` (dict): Aircraft data
- `squawk_code` (str): Emergency squawk code
- `message_data` (dict): Message data with keys:
  - `content` (str): Message text content
  - `embed` (discord.Embed): Message embed
  - `view` (discord.ui.View): Message view/buttons

#### 3. Post-Send Callbacks
Called after an alert message is sent.

**Signature:**
```python
async def callback(guild, aircraft_info, squawk_code, sent_message):
    # React to the sent message
    await sent_message.add_reaction("🚨")
```

**Parameters:**
- `guild` (discord.Guild): The Discord guild
- `aircraft_info` (dict): Aircraft data
- `squawk_code` (str): Emergency squawk code
- `sent_message` (discord.Message): The sent alert message

### 📊 Aircraft Info Structure

The `aircraft_info` dictionary contains:

```python
{
    'hex': 'A12345',           # ICAO hex code
    'flight': 'UAL123',        # Flight callsign
    'lat': 40.7128,            # Latitude
    'lon': -74.0060,           # Longitude
    'altitude': 35000,         # Altitude in feet
    'ground_speed': 450,       # Ground speed in knots
    'track': 180,              # Track/heading
    'squawk': '7700',          # Squawk code
    # ... additional fields may be present
}
```

### 🔌 How to Connect

```python
from redbot.core import commands

class YourCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        
    async def cog_load(self):
        """Called when your cog loads."""
        await self._setup_skysearch_api()
        
    def _get_skysearch_cog(self):
        """Find the SkySearch cog."""
        possible_names = ["skysearch", "SkySearch", "Skysearch"]
        for name in possible_names:
            cog = self.bot.get_cog(name)
            if cog and hasattr(cog, 'squawk_api'):
                return cog
        return None
        
    async def _setup_skysearch_api(self):
        """Register callbacks with SkySearch."""
        skysearch_cog = self._get_skysearch_cog()
        if skysearch_cog:
            # Register your callbacks
            skysearch_cog.squawk_api.register_callback(self.handle_alert)
            skysearch_cog.squawk_api.register_pre_send_callback(self.modify_message)
            skysearch_cog.squawk_api.register_post_send_callback(self.react_to_message)
            
    async def handle_alert(self, guild, aircraft_info, squawk_code):
        """Handle emergency alert detection."""
        print(f"Emergency detected: {squawk_code} for {aircraft_info['hex']}")
        
    async def modify_message(self, guild, aircraft_info, squawk_code, message_data):
        """Modify alert message before sending."""
        if message_data.get('embed'):
            embed = message_data['embed']
            embed.add_field(name="Custom Field", value="Added by YourCog", inline=False)
        return message_data
        
    async def react_to_message(self, guild, aircraft_info, squawk_code, sent_message):
        """React to sent alert message."""
        await sent_message.add_reaction("👀")
```

---

## 🔧 CommandAPI

The CommandAPI allows other cogs to monitor SkySearch command execution and gather usage analytics.

### 📍 Location
```
skysearch/api/command_api.py
```

### 🎯 Purpose
- Monitor when SkySearch commands are executed
- Track command usage and performance
- Implement custom logging or analytics
- Add pre/post command processing

### 🔧 Available Callback Types

#### 1. Basic Callbacks
Called when a SkySearch command is executed.

**Signature:**
```python
async def callback(ctx, command_name, args):
    # Your code here
    pass
```

**Parameters:**
- `ctx` (commands.Context): Discord command context
- `command_name` (str): Name of the executed command (e.g., 'aircraft_icao')
- `args` (list): Command arguments

#### 2. Pre-Execute Callbacks
Called before a command executes, can cancel execution.

**Signature:**
```python
async def callback(ctx, command_name, args):
    # Return False to cancel command execution
    if should_cancel_command():
        return False
    return True  # or None to continue normally
```

**Parameters:**
- `ctx` (commands.Context): Discord command context
- `command_name` (str): Command name
- `args` (list): Command arguments

**Return Values:**
- `False`: Cancel command execution
- `True` or `None`: Continue execution

#### 3. Post-Execute Callbacks
Called after a command completes.

**Signature:**
```python
async def callback(ctx, command_name, args, result, execution_time):
    # Process command completion
    if isinstance(result, Exception):
        print(f"Command {command_name} failed: {result}")
    else:
        print(f"Command {command_name} completed in {execution_time:.2f}s")
```

**Parameters:**
- `ctx` (commands.Context): Discord command context
- `command_name` (str): Command name
- `args` (list): Command arguments
- `result` (any): Command result or Exception if failed
- `execution_time` (float): Execution time in seconds

### 🎯 Tracked Commands

Currently, these SkySearch commands trigger CommandAPI callbacks:

- `aircraft icao <hex>`
- `aircraft callsign <callsign>`
- `aircraft squawk <code>`

### 🔌 How to Connect

```python
from redbot.core import commands
import datetime

class YourCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.command_stats = {}
        
    async def cog_load(self):
        """Called when your cog loads."""
        await self._setup_command_api()
        
    def _get_skysearch_cog(self):
        """Find the SkySearch cog."""
        possible_names = ["skysearch", "SkySearch", "Skysearch"]
        for name in possible_names:
            cog = self.bot.get_cog(name)
            if cog and hasattr(cog, 'command_api'):
                return cog
        return None
        
    async def _setup_command_api(self):
        """Register callbacks with SkySearch CommandAPI."""
        skysearch_cog = self._get_skysearch_cog()
        if skysearch_cog:
            # Register your callbacks
            skysearch_cog.command_api.register_callback(self.track_command)
            skysearch_cog.command_api.register_post_execute_callback(self.log_performance)
            
    async def track_command(self, ctx, command_name, args):
        """Track command usage."""
        # Store usage data
        key = f"{ctx.guild.id}_{command_name}"
        if key not in self.command_stats:
            self.command_stats[key] = 0
        self.command_stats[key] += 1
        
    async def log_performance(self, ctx, command_name, args, result, execution_time):
        """Log command performance."""
        success = not isinstance(result, Exception)
        status = "SUCCESS" if success else "ERROR"
        
        # Only log slow commands or errors
        if execution_time > 2.0 or not success:
            print(f"[Performance] {command_name}: {status} ({execution_time:.2f}s)")
```

---

## 🎨 Integration Examples

### Example 1: Enhanced Alert Logger

```python
import discord
from redbot.core import commands
import datetime
import json

class AlertLogger(commands.Cog):
    """Log all emergency alerts to a file."""
    
    def __init__(self, bot):
        self.bot = bot
        self.log_file = "emergency_alerts.json"
        
    async def cog_load(self):
        skysearch_cog = self.bot.get_cog("skysearch")
        if skysearch_cog:
            skysearch_cog.squawk_api.register_callback(self.log_alert)
            
    async def log_alert(self, guild, aircraft_info, squawk_code):
        """Log emergency alert to file."""
        alert_data = {
            'timestamp': datetime.datetime.utcnow().isoformat(),
            'guild_name': guild.name,
            'guild_id': guild.id,
            'aircraft_hex': aircraft_info.get('hex'),
            'callsign': aircraft_info.get('flight'),
            'squawk_code': squawk_code,
            'position': {
                'lat': aircraft_info.get('lat'),
                'lon': aircraft_info.get('lon')
            },
            'altitude': aircraft_info.get('altitude'),
            'speed': aircraft_info.get('ground_speed')
        }
        
        # Append to log file
        try:
            with open(self.log_file, 'a') as f:
                f.write(json.dumps(alert_data) + '\n')
        except Exception as e:
            print(f"Failed to log alert: {e}")
```

### Example 2: Command Usage Analytics

```python
import discord
from redbot.core import commands
from collections import defaultdict
import datetime

class UsageAnalytics(commands.Cog):
    """Track and analyze SkySearch command usage."""
    
    def __init__(self, bot):
        self.bot = bot
        self.daily_stats = defaultdict(lambda: defaultdict(int))
        
    async def cog_load(self):
        skysearch_cog = self.bot.get_cog("skysearch")
        if skysearch_cog:
            skysearch_cog.command_api.register_callback(self.track_usage)
            
    async def track_usage(self, ctx, command_name, args):
        """Track daily command usage."""
        today = datetime.date.today().isoformat()
        self.daily_stats[today][command_name] += 1
        
    @commands.command()
    async def usage_stats(self, ctx):
        """Show command usage statistics."""
        today = datetime.date.today().isoformat()
        stats = self.daily_stats[today]
        
        if not stats:
            await ctx.send("No command usage today.")
            return
            
        embed = discord.Embed(title="Today's SkySearch Usage", color=0x00ff00)
        for command, count in sorted(stats.items(), key=lambda x: x[1], reverse=True):
            embed.add_field(name=command, value=f"{count} uses", inline=True)
            
        await ctx.send(embed=embed)
```

### Example 3: Alert Notification System

```python
import discord
from redbot.core import commands
import aiohttp

class AlertNotifier(commands.Cog):
    """Send alerts to external services."""
    
    def __init__(self, bot):
        self.bot = bot
        self.webhook_url = "https://your-webhook-service.com/alerts"
        
    async def cog_load(self):
        skysearch_cog = self.bot.get_cog("skysearch")
        if skysearch_cog:
            skysearch_cog.squawk_api.register_callback(self.send_external_alert)
            
    async def send_external_alert(self, guild, aircraft_info, squawk_code):
        """Send alert to external webhook."""
        # Only send for major emergencies
        if squawk_code in ['7500', '7700']:
            payload = {
                'alert_type': 'aircraft_emergency',
                'squawk_code': squawk_code,
                'aircraft': aircraft_info.get('hex'),
                'callsign': aircraft_info.get('flight'),
                'guild': guild.name,
                'severity': 'high' if squawk_code == '7500' else 'medium'
            }
            
            try:
                async with aiohttp.ClientSession() as session:
                    async with session.post(self.webhook_url, json=payload) as resp:
                        if resp.status == 200:
                            print(f"Alert sent for {aircraft_info.get('hex')}")
            except Exception as e:
                print(f"Failed to send external alert: {e}")
```

---

## ✅ Best Practices

### 1. Error Handling
Always wrap your callback code in try-except blocks:

```python
async def your_callback(self, *args):
    try:
        # Your code here
        pass
    except Exception as e:
        print(f"Error in callback: {e}")
        # Don't re-raise - this could break other callbacks
```

### 2. Cog Discovery
Use multiple possible names when finding the SkySearch cog:

```python
def _get_skysearch_cog(self):
    possible_names = ["skysearch", "SkySearch", "Skysearch", "SkySearchCog"]
    for name in possible_names:
        cog = self.bot.get_cog(name)
        if cog and hasattr(cog, 'squawk_api'):
            return cog
    return None
```

### 3. Graceful Degradation
Handle cases where SkySearch isn't loaded:

```python
async def cog_load(self):
    skysearch_cog = self._get_skysearch_cog()
    if skysearch_cog:
        # Register callbacks
        print("Connected to SkySearch API")
    else:
        print("SkySearch not found - some features disabled")
```

### 4. Reconnection Support
Implement reconnection for when SkySearch is reloaded:

```python
@commands.command()
@commands.is_owner()
async def reconnect_skysearch(self, ctx):
    """Reconnect to SkySearch API."""
    await self._setup_skysearch_api()
    await ctx.send("Reconnected to SkySearch API!")
```

### 5. Performance Considerations
- Keep callbacks lightweight and fast
- Use async operations for I/O
- Don't block the callback execution
- Consider using background tasks for heavy processing

---

## 🔧 Troubleshooting

### Common Issues

#### 1. "SkySearch cog not found"
**Cause:** SkySearch cog isn't loaded or has a different name.

**Solution:**
```python
# Check what cogs are loaded
loaded_cogs = list(bot.cogs.keys())
print("Loaded cogs:", loaded_cogs)

# Look for cogs with 'sky' or 'search' in the name
sky_cogs = [cog for cog in loaded_cogs if 'sky' in cog.lower() or 'search' in cog.lower()]
print("Sky-related cogs:", sky_cogs)
```

#### 2. "Callbacks not being called"
**Cause:** Callbacks registered after events occurred, or SkySearch was reloaded.

**Solution:**
- Reload your cog: `*reload yourcog`
- Check callback registration in debug mode
- Ensure SkySearch alert channel is configured

#### 3. "CommandAPI callbacks not working"
**Cause:** Only specific commands are hooked (icao, callsign, squawk).

**Solution:**
- Check which commands are hooked in the SkySearch cog
- Use the SquawkAlertAPI for emergency-related functionality

#### 4. "Callback errors breaking other callbacks"
**Cause:** Unhandled exceptions in callback code.

**Solution:**
```python
async def your_callback(self, *args):
    try:
        # Your code
        pass
    except Exception as e:
        # Log error but don't re-raise
        print(f"Callback error: {e}")
        import traceback
        traceback.print_exc()
```

### Debug Commands

Add these debug commands to your cog:

```python
@commands.command()
@commands.is_owner()
async def debug_skysearch_api(self, ctx):
    """Debug SkySearch API connection."""
    skysearch_cog = self._get_skysearch_cog()
    
    if not skysearch_cog:
        await ctx.send("❌ SkySearch cog not found")
        return
        
    embed = discord.Embed(title="SkySearch API Debug", color=0x00ff00)
    
    if hasattr(skysearch_cog, 'squawk_api'):
        api = skysearch_cog.squawk_api
        embed.add_field(
            name="SquawkAlertAPI",
            value=f"✅ Available\nCallbacks: {len(api._callbacks)}",
            inline=True
        )
    
    if hasattr(skysearch_cog, 'command_api'):
        api = skysearch_cog.command_api
        embed.add_field(
            name="CommandAPI", 
            value=f"✅ Available\nCallbacks: {len(api._callbacks)}",
            inline=True
        )
        
    await ctx.send(embed=embed)
```

---

## 📚 Additional Resources

- **SkySearch Documentation**: See `skysearch/docs.md` for general usage
- **Example Implementation**: Check `example/squawk_cog.py` for a complete example
- **Discord.py Documentation**: https://discordpy.readthedocs.io/
- **Red-DiscordBot Documentation**: https://docs.discord.red/

---

## 🤝 Contributing

If you find issues with the API or have suggestions for improvements:

1. Check existing GitHub issues
2. Create a new issue with detailed description
3. Include code examples and error logs
4. Consider submitting a pull request

---

*This documentation covers SkySearch API v1.0. Last updated: 2025-01-24* 
