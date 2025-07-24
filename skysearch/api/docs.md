# SkySearch Enhanced API Documentation

This document provides comprehensive documentation for the **enhanced** SkySearch API system, which allows other cogs to integrate with and extend SkySearch functionality with advanced features like performance monitoring, circuit breakers, and priority handling.

## 📋 Table of Contents

1. [Overview](#overview)
2. [Enhanced SquawkAlertAPI](#enhanced-squawkalertapi)
3. [Enhanced CommandAPI](#enhanced-commandapi)
4. [Integration Examples](#integration-examples)
5. [Performance Monitoring](#performance-monitoring)
6. [Best Practices](#best-practices)
7. [Troubleshooting](#troubleshooting)
8. [Migration Guide](#migration-guide)

---

## 🔍 Overview

The SkySearch cog provides two main **enhanced** APIs for integration:

- **SquawkAlertAPI**: Hook into aircraft emergency alerts with deduplication, circuit breakers, and performance metrics
- **CommandAPI**: Monitor and interact with SkySearch command execution with filtering and analytics

Both APIs feature:
- 🛡️ **Circuit Breaker Protection** - Auto-disable failing callbacks
- 📊 **Performance Metrics** - Track execution times and success rates
- 🎯 **Priority System** - Control callback execution order
- ⏱️ **Timeout Protection** - Prevent hanging callbacks
- 🔄 **Deduplication** - Prevent spam (SquawkAlertAPI)
- 📈 **Real-time Analytics** - Monitor API health and usage

---

## 🚨 Enhanced SquawkAlertAPI

The SquawkAlertAPI allows other cogs to respond to aircraft emergency alerts with advanced reliability and monitoring features.

### 📍 Location
```
skysearch/api/squawk_api.py
```

### 🎯 Purpose
- Monitor aircraft emergency squawk codes (7500, 7600, 7700)
- Modify alert messages before they're sent
- React to alert messages after they're sent
- Add custom processing with circuit breaker protection
- Track performance metrics and callback health

### 🔧 Enhanced Callback Types

#### 1. Basic Callbacks (Enhanced)
Called when an emergency alert is detected, with deduplication and error handling.

**Enhanced Signature:**
```python
# Registration with metadata
api.register_callback(
    callback_function,
    cog_name="MyCog",           # For debugging and metrics
    priority=10,                # Higher = runs first (0-10)
    timeout=15.0               # Max execution time in seconds
)

# Callback function signature (unchanged)
async def callback(guild, aircraft_info, squawk_code):
    # Your code here
    pass
```

**New Features:**
- ✅ **Deduplication**: Prevents duplicate alerts within 30 seconds
- ✅ **Circuit Breaker**: Auto-disables after 5 failures
- ✅ **Performance Tracking**: Measures execution time and success rate
- ✅ **Priority Ordering**: Higher priority callbacks run first

#### 2. Pre-Send Callbacks (Enhanced)
Called before an alert message is sent, allows message modification.

**Enhanced Signature:**
```python
# Registration with metadata
api.register_pre_send_callback(
    callback_function,
    cog_name="MyCog",
    priority=5,                 # Medium priority for message modification
    timeout=8.0                # Shorter timeout for message processing
)

# Callback function signature (unchanged)
async def callback(guild, aircraft_info, squawk_code, message_data):
    # Modify message_data
    message_data['content'] += "\nCustom addition!"
    return message_data  # or return None for no changes
```

#### 3. Post-Send Callbacks (Enhanced)
Called after an alert message is sent.

**Enhanced Signature:**
```python
# Registration with metadata
api.register_post_send_callback(
    callback_function,
    cog_name="MyCog",
    priority=1,                 # Lower priority for post-processing
    timeout=20.0               # Longer timeout for complex operations
)

# Callback function signature (unchanged)
async def callback(guild, aircraft_info, squawk_code, sent_message):
    # React to the sent message
    await sent_message.add_reaction("🚨")
```

### 🆕 New Methods

#### Callback Management
```python
# Unregister callbacks
success = api.unregister_callback(callback_function, "all")  # or "basic", "pre_send", "post_send"

# Re-enable disabled callbacks for a cog
success = api.enable_callback("MyCogName")

# Configure deduplication window
api.set_dedup_window(30.0)  # seconds (1-300)
```

#### Performance Monitoring
```python
# Get comprehensive statistics
stats = api.get_stats()
# Returns:
# {
#     'total_callbacks': 6,
#     'basic_callbacks': 2,
#     'pre_send_callbacks': 2,
#     'post_send_callbacks': 2,
#     'enabled_callbacks': 5,
#     'recent_alerts_tracked': 3,
#     'metrics': {
#         'total_calls': 25,
#         'successful_calls': 23,
#         'failed_calls': 2,
#         'callback_stats': {
#             'MyCog': {
#                 'calls': 10,
#                 'failures': 1,
#                 'total_time': 0.5
#             }
#         }
#     },
#     'callback_details': [...]
# }
```

### 📊 Enhanced Aircraft Info Structure

The `aircraft_info` dictionary contains the same data as before:

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

### 🔌 Enhanced Connection Example

```python
from redbot.core import commands
import logging

log = logging.getLogger("red.mycog")

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
        """Register callbacks with enhanced SkySearch API."""
        skysearch_cog = self._get_skysearch_cog()
        if skysearch_cog:
            # Register with enhanced parameters
            success = skysearch_cog.squawk_api.register_callback(
                self.handle_alert,
                cog_name="MyCog",
                priority=10,        # High priority
                timeout=15.0
            )
            
            success = skysearch_cog.squawk_api.register_pre_send_callback(
                self.modify_message,
                cog_name="MyCog", 
                priority=5,         # Medium priority
                timeout=8.0
            )
            
            success = skysearch_cog.squawk_api.register_post_send_callback(
                self.react_to_message,
                cog_name="MyCog",
                priority=1,         # Lower priority
                timeout=20.0
            )
            
            if success:
                log.info("Successfully registered with enhanced SkySearch API")
            else:
                log.warning("Some callbacks may already be registered")
                
    async def handle_alert(self, guild, aircraft_info, squawk_code):
        """Handle emergency alert detection."""
        # This will be tracked for performance metrics
        log.info(f"Emergency detected: {squawk_code} for {aircraft_info['hex']}")
        
    async def modify_message(self, guild, aircraft_info, squawk_code, message_data):
        """Modify alert message before sending."""
        if message_data.get('embed'):
            embed = message_data['embed']
            # Make modifications idempotent to prevent spam
            field_names = [field.name for field in embed.fields]
            if "Custom Enhancement" not in field_names:
                embed.add_field(name="Custom Enhancement", value="Added by MyCog", inline=False)
        return message_data
        
    async def react_to_message(self, guild, aircraft_info, squawk_code, sent_message):
        """React to sent alert message."""
        try:
            await sent_message.add_reaction("👀")
        except Exception as e:
            log.error(f"Failed to add reaction: {e}")
```

---

## 🔧 Enhanced CommandAPI

The CommandAPI allows other cogs to monitor SkySearch command execution with filtering, performance tracking, and advanced error handling.

### 📍 Location
```
skysearch/api/command_api.py
```

### 🎯 Purpose
- Monitor when SkySearch commands are executed
- Track command usage and performance with detailed metrics
- Implement custom logging or analytics with filtering
- Add pre/post command processing with circuit breaker protection
- Filter callbacks to specific commands only

### 🔧 Enhanced Callback Types

#### 1. Basic Callbacks (Enhanced)
Called when a SkySearch command is executed.

**Enhanced Signature:**
```python
# Registration with metadata and filtering
api.register_callback(
    callback_function,
    cog_name="MyCog",
    priority=5,
    timeout=10.0,
    command_filter=["aircraft_icao", "aircraft_callsign"]  # Only these commands
)

# Callback function signature (unchanged)
async def callback(ctx, command_name, args):
    # Your code here
    pass
```

#### 2. Pre-Execute Callbacks (Enhanced)
Called before a command executes, can cancel execution.

**Enhanced Signature:**
```python
# Registration with filtering
api.register_pre_execute_callback(
    callback_function,
    cog_name="MyCog",
    priority=10,        # High priority to run early
    timeout=5.0,        # Quick decision making
    command_filter=["aircraft_squawk"]  # Only monitor squawk commands
)

# Callback function signature (unchanged)
async def callback(ctx, command_name, args):
    # Return False to cancel command execution
    if should_cancel_command():
        return False
    return True  # or None to continue normally
```

#### 3. Post-Execute Callbacks (Enhanced)
Called after a command completes.

**Enhanced Signature:**
```python
# Registration with comprehensive monitoring
api.register_post_execute_callback(
    callback_function,
    cog_name="MyCog",
    priority=1,         # Lower priority for cleanup
    timeout=15.0,
    command_filter=None  # Monitor all commands
)

# Callback function signature (unchanged)
async def callback(ctx, command_name, args, result, execution_time):
    # Process command completion
    if isinstance(result, Exception):
        log.error(f"Command {command_name} failed: {result}")
    else:
        log.info(f"Command {command_name} completed in {execution_time:.2f}s")
```

### 🆕 New Methods

#### Callback Management
```python
# Unregister callbacks with type filtering
success = api.unregister_callback(callback_function, "post_execute")

# Re-enable disabled callbacks
success = api.enable_callback("MyCogName")
```

#### Performance Monitoring
```python
# Get comprehensive statistics
stats = api.get_stats()
# Returns detailed metrics including per-command performance

# Get command-specific performance
performance = api.get_command_performance("aircraft_icao")
# Returns: {'count': 50, 'avg_time': 2.1, 'failures': 2}

# Get all command performance
all_performance = api.get_command_performance()

# Get currently executing commands
active = api.get_active_commands()
# Returns commands currently running with duration
```

### 🎯 Enhanced Tracked Commands

These SkySearch commands trigger CommandAPI callbacks:

- `aircraft icao <hex>` - ICAO code lookup
- `aircraft callsign <callsign>` - Callsign lookup
- `aircraft squawk <code>` - Squawk code lookup

**Command Names in Callbacks:**
- `aircraft_icao`
- `aircraft_callsign` 
- `aircraft_squawk`

### 🔌 Enhanced Connection Example

```python
from redbot.core import commands
import datetime
import logging

log = logging.getLogger("red.mycog")

class YourCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.command_stats = {}
        
    async def cog_load(self):
        """Called when your cog loads."""
        await self._setup_command_api()
        
    async def _setup_command_api(self):
        """Register callbacks with enhanced SkySearch CommandAPI."""
        skysearch_cog = self._get_skysearch_cog()
        if skysearch_cog and hasattr(skysearch_cog, 'command_api'):
            # Register with enhanced parameters and filtering
            skysearch_cog.command_api.register_callback(
                self.track_command,
                cog_name="MyCog",
                priority=5,
                timeout=10.0,
                command_filter=["aircraft_icao", "aircraft_callsign"]  # Only track these
            )
            
            skysearch_cog.command_api.register_post_execute_callback(
                self.log_performance,
                cog_name="MyCog",
                priority=1,
                timeout=5.0,
                command_filter=None  # Track all commands for errors
            )
            
            log.info("Successfully registered with enhanced CommandAPI")
            
    async def track_command(self, ctx, command_name, args):
        """Track command usage with enhanced filtering."""
        # This only runs for aircraft_icao and aircraft_callsign commands
        key = f"{ctx.guild.id}_{command_name}"
        if key not in self.command_stats:
            self.command_stats[key] = 0
        self.command_stats[key] += 1
        
    async def log_performance(self, ctx, command_name, args, result, execution_time):
        """Log command performance for all commands."""
        success = not isinstance(result, Exception)
        status = "SUCCESS" if success else "ERROR"
        
        # Only log slow commands or errors
        if execution_time > 2.0 or not success:
            log.warning(f"[Performance] {command_name}: {status} ({execution_time:.2f}s)")
```

---

## 🎨 Integration Examples

### Example 1: Enhanced Alert Logger with Circuit Breaker

```python
import discord
from redbot.core import commands
import datetime
import json
import logging

log = logging.getLogger("red.alertlogger")

class EnhancedAlertLogger(commands.Cog):
    """Log all emergency alerts with enhanced reliability."""
    
    def __init__(self, bot):
        self.bot = bot
        self.log_file = "emergency_alerts.json"
        self.failed_writes = 0
        
    async def cog_load(self):
        skysearch_cog = self.bot.get_cog("skysearch")
        if skysearch_cog:
            # Register with circuit breaker protection
            skysearch_cog.squawk_api.register_callback(
                self.log_alert,
                cog_name="AlertLogger",
                priority=8,        # High priority for logging
                timeout=5.0        # Quick file operations
            )
            
    async def log_alert(self, guild, aircraft_info, squawk_code):
        """Log emergency alert to file with error handling."""
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
        
        # This will automatically trigger circuit breaker if it fails repeatedly
        try:
            with open(self.log_file, 'a') as f:
                f.write(json.dumps(alert_data) + '\n')
            self.failed_writes = 0  # Reset counter on success
        except Exception as e:
            self.failed_writes += 1
            log.error(f"Failed to log alert (attempt {self.failed_writes}): {e}")
            raise  # Re-raise to trigger circuit breaker
            
    @commands.command()
    async def alertlogger_status(self, ctx):
        """Check the status of alert logging."""
        skysearch_cog = self.bot.get_cog("skysearch")
        if not skysearch_cog:
            await ctx.send("❌ SkySearch not found")
            return
            
        stats = skysearch_cog.squawk_api.get_stats()
        our_stats = stats['metrics']['callback_stats'].get('AlertLogger', {})
        
        embed = discord.Embed(title="Alert Logger Status", color=discord.Color.green())
        
        if our_stats:
            success_rate = ((our_stats['calls'] - our_stats['failures']) / our_stats['calls']) * 100
            avg_time = (our_stats['total_time'] / our_stats['calls']) * 1000
            
            embed.add_field(
                name="Performance",
                value=f"Alerts logged: {our_stats['calls']}\n"
                      f"Success rate: {success_rate:.1f}%\n"
                      f"Avg time: {avg_time:.1f}ms",
                inline=True
            )
        
        # Check if callback is enabled
        callback_details = [cb for cb in stats['callback_details'] if cb['cog_name'] == 'AlertLogger']
        if callback_details:
            cb = callback_details[0]
            status = "✅ Enabled" if cb['enabled'] else f"❌ Disabled ({cb['failure_count']} failures)"
            embed.add_field(name="Status", value=status, inline=True)
        
        await ctx.send(embed=embed)
```

### Example 2: Command Usage Analytics with Filtering

```python
import discord
from redbot.core import commands
from collections import defaultdict
import datetime
import logging

log = logging.getLogger("red.analytics")

class EnhancedUsageAnalytics(commands.Cog):
    """Track and analyze SkySearch command usage with advanced filtering."""
    
    def __init__(self, bot):
        self.bot = bot
        self.daily_stats = defaultdict(lambda: defaultdict(int))
        self.user_stats = defaultdict(lambda: defaultdict(int))
        
    async def cog_load(self):
        skysearch_cog = self.bot.get_cog("skysearch")
        if skysearch_cog:
            # Only track specific high-value commands
            skysearch_cog.command_api.register_callback(
                self.track_usage,
                cog_name="Analytics",
                priority=3,
                timeout=2.0,
                command_filter=["aircraft_icao", "aircraft_callsign", "aircraft_squawk"]
            )
            
            # Track all command performance for optimization
            skysearch_cog.command_api.register_post_execute_callback(
                self.track_performance,
                cog_name="Analytics",
                priority=1,
                timeout=1.0,
                command_filter=None  # All commands
            )
            
    async def track_usage(self, ctx, command_name, args):
        """Track daily command usage for filtered commands only."""
        today = datetime.date.today().isoformat()
        self.daily_stats[today][command_name] += 1
        self.user_stats[ctx.author.id][command_name] += 1
        
    async def track_performance(self, ctx, command_name, args, result, execution_time):
        """Track performance for all commands."""
        # Only log if slow or failed
        if execution_time > 3.0:
            log.warning(f"Slow command: {command_name} took {execution_time:.2f}s")
        elif isinstance(result, Exception):
            log.error(f"Failed command: {command_name} - {result}")
            
    @commands.command()
    async def usage_analytics(self, ctx):
        """Show enhanced command usage analytics."""
        today = datetime.date.today().isoformat()
        stats = self.daily_stats[today]
        
        if not stats:
            await ctx.send("No command usage today.")
            return
            
        embed = discord.Embed(title="📊 Enhanced SkySearch Analytics", color=discord.Color.blue())
        
        # Daily usage
        usage_text = []
        for command, count in sorted(stats.items(), key=lambda x: x[1], reverse=True):
            usage_text.append(f"**{command}**: {count} uses")
        
        embed.add_field(
            name="📈 Today's Usage",
            value="\n".join(usage_text[:10]),
            inline=True
        )
        
        # Get API performance stats
        skysearch_cog = self.bot.get_cog("skysearch")
        if skysearch_cog and hasattr(skysearch_cog.command_api, 'get_stats'):
            api_stats = skysearch_cog.command_api.get_stats()
            cmd_metrics = api_stats['metrics']
            
            total = cmd_metrics['total_commands']
            if total > 0:
                success_rate = (cmd_metrics['successful_commands'] / total) * 100
                embed.add_field(
                    name="⚡ API Performance",
                    value=f"Total commands: {total}\n"
                          f"Success rate: {success_rate:.1f}%\n"
                          f"Active now: {api_stats['active_commands']}",
                    inline=True
                )
        
        await ctx.send(embed=embed)
```

---

## 📊 Performance Monitoring

### Real-time Statistics

Both APIs provide comprehensive performance monitoring:

```python
# Get SquawkAlertAPI statistics
squawk_stats = skysearch_cog.squawk_api.get_stats()

# Get CommandAPI statistics  
command_stats = skysearch_cog.command_api.get_stats()
```

### Key Metrics Tracked

**SquawkAlertAPI Metrics:**
- Total callback invocations
- Success/failure rates per cog
- Average execution times
- Circuit breaker status
- Deduplication effectiveness
- Active alert tracking

**CommandAPI Metrics:**
- Command execution counts
- Success/failure rates per command
- Average command execution times
- Currently active commands
- Callback filtering effectiveness
- Per-cog performance breakdown

### Debug Commands for Monitoring

Add these commands to your cogs for monitoring:

```python
@commands.command()
@commands.is_owner()
async def api_health(self, ctx):
    """Check API health and performance."""
    skysearch_cog = self.bot.get_cog("skysearch")
    if not skysearch_cog:
        await ctx.send("❌ SkySearch not found")
        return
    
    # Check SquawkAlertAPI
    if hasattr(skysearch_cog, 'squawk_api'):
        stats = skysearch_cog.squawk_api.get_stats()
        disabled_callbacks = [
            cb for cb in stats['callback_details'] 
            if not cb['enabled']
        ]
        
        if disabled_callbacks:
            await ctx.send(f"⚠️ {len(disabled_callbacks)} disabled SquawkAPI callbacks")
        
    # Check CommandAPI
    if hasattr(skysearch_cog, 'command_api'):
        cmd_stats = skysearch_cog.command_api.get_stats()
        active_commands = cmd_stats['active_commands']
        
        if active_commands > 5:
            await ctx.send(f"⚠️ {active_commands} commands currently executing")
```

---

## ✅ Best Practices

### 1. Enhanced Error Handling
Always use proper error handling and let the circuit breaker work:

```python
async def your_callback(self, *args):
    try:
        # Your code here
        result = await some_operation()
        return result
    except SpecificException as e:
        # Handle specific errors you can recover from
        log.warning(f"Recoverable error: {e}")
        return None
    except Exception as e:
        # Re-raise unexpected errors to trigger circuit breaker
        log.error(f"Unexpected error in callback: {e}")
        raise  # Important: let circuit breaker handle this
```

### 2. Optimal Registration Parameters

**Priority Guidelines:**
- `10`: Critical operations (logging, alerts)
- `5-7`: Message modifications, enhancements  
- `1-3`: Reactions, cosmetic updates
- `0`: Default/non-critical operations

**Timeout Guidelines:**
- `1-5s`: Quick operations (logging, simple processing)
- `5-10s`: Message modifications, API calls
- `10-20s`: Complex operations, file I/O
- `20s+`: Heavy processing (use sparingly)

### 3. Idempotent Message Modifications

Prevent spam by making modifications idempotent:

```python
async def modify_message(self, guild, aircraft_info, squawk_code, message_data):
    """Idempotent message modification."""
    if message_data.get('embed'):
        embed = message_data['embed']
        
        # Check if already modified
        existing_fields = [field.name for field in embed.fields]
        if "My Enhancement" not in existing_fields:
            embed.add_field(name="My Enhancement", value="Added once", inline=False)
            
        # Check content modifications
        enhancement_text = "🔔 Enhanced by MyCog"
        if enhancement_text not in message_data.get('content', ''):
            message_data['content'] = (message_data.get('content', '') + f"\n{enhancement_text}").strip()
            
    return message_data
```

### 4. Command Filtering Best Practices

Use filtering to improve performance:

```python
# Good: Only monitor commands you care about
api.register_callback(
    callback,
    command_filter=["aircraft_icao", "aircraft_callsign"]
)

# Bad: Monitor all commands when you only need specific ones
api.register_callback(callback, command_filter=None)  # Less efficient
```

### 5. Performance Monitoring Integration

Regular health checks:

```python
async def periodic_health_check(self):
    """Check API health periodically."""
    stats = api.get_stats()
    
    # Check for disabled callbacks
    disabled = [cb for cb in stats['callback_details'] if not cb['enabled']]
    if disabled:
        log.warning(f"{len(disabled)} callbacks disabled due to failures")
        
    # Check performance
    our_stats = stats['metrics']['callback_stats'].get('MyCog', {})
    if our_stats.get('calls', 0) > 0:
        failure_rate = (our_stats['failures'] / our_stats['calls']) * 100
        if failure_rate > 5.0:  # More than 5% failure rate
            log.warning(f"High failure rate: {failure_rate:.1f}%")
```

---

## 🔧 Troubleshooting

### Common Issues

#### 1. "Callback disabled by circuit breaker"
**Cause:** Your callback failed 5+ times consecutively.

**Solution:**
```python
# Check what's failing
stats = api.get_stats()
our_callbacks = [cb for cb in stats['callback_details'] if cb['cog_name'] == 'MyCog']
disabled = [cb for cb in our_callbacks if not cb['enabled']]

# Fix the underlying issue, then re-enable
success = api.enable_callback('MyCog')
```

#### 2. "Callback timeout"  
**Cause:** Your callback took longer than the configured timeout.

**Solution:**
```python
# Option 1: Increase timeout during registration
api.register_callback(
    callback,
    timeout=30.0  # Increase from default 10s
)

# Option 2: Optimize your callback code
async def optimized_callback(self, *args):
    # Use asyncio for I/O operations
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            data = await response.json()
```

#### 3. "Duplicate alert skipped"
**Cause:** The deduplication system prevented a duplicate alert.

**This is normal behavior!** But if you need to adjust:
```python
# Increase deduplication window
api.set_dedup_window(60.0)  # 60 seconds instead of 30

# Or check if it's expected
results = await api.call_callbacks(guild, aircraft_info, squawk_code)
if results.get('skipped'):
    log.debug(f"Alert skipped: {results['reason']}")
```

#### 4. "Command callbacks not running"
**Cause:** Command filtering or callback not registered for the command.

**Solution:**
```python
# Check what commands are being filtered
stats = api.get_stats()
callback_details = [cb for cb in stats['callback_details'] if cb['cog_name'] == 'MyCog']
for cb in callback_details:
    print(f"Filter: {cb['command_filter']}")

# Update filter if needed
api.unregister_callback(old_callback)
api.register_callback(
    new_callback,
    command_filter=["aircraft_icao", "aircraft_callsign", "aircraft_squawk"]
)
```

### Enhanced Debug Commands

Add these to your cogs for better troubleshooting:

```python
@commands.command()
@commands.is_owner()
async def debug_api_detailed(self, ctx):
    """Detailed API debugging information."""
    skysearch_cog = self.bot.get_cog("skysearch")
    if not skysearch_cog:
        await ctx.send("❌ SkySearch not found")
        return
        
    embeds = []
    
    # SquawkAlertAPI Debug
    if hasattr(skysearch_cog, 'squawk_api'):
        stats = skysearch_cog.squawk_api.get_stats()
        embed = discord.Embed(title="🚨 SquawkAlertAPI Debug", color=discord.Color.orange())
        
        # Overall health
        total_callbacks = stats['total_callbacks']
        enabled_callbacks = stats['enabled_callbacks']
        health_status = "✅ Healthy" if enabled_callbacks == total_callbacks else f"⚠️ {total_callbacks - enabled_callbacks} disabled"
        
        embed.add_field(
            name="🏥 Health Status",
            value=f"{health_status}\n"
                  f"Total: {total_callbacks}\n"
                  f"Enabled: {enabled_callbacks}\n"
                  f"Recent alerts: {stats['recent_alerts_tracked']}",
            inline=True
        )
        
        # Performance metrics
        metrics = stats['metrics']
        if metrics['total_calls'] > 0:
            success_rate = (metrics['successful_calls'] / metrics['total_calls']) * 100
            embed.add_field(
                name="📊 Performance",
                value=f"Total calls: {metrics['total_calls']}\n"
                      f"Success rate: {success_rate:.1f}%\n"
                      f"Failed calls: {metrics['failed_calls']}",
                inline=True
            )
        
        # Callback details
        our_callbacks = [cb for cb in stats['callback_details'] if cb['cog_name'] == 'MyCog']
        if our_callbacks:
            cb_info = []
            for cb in our_callbacks:
                status = "✅" if cb['enabled'] else f"❌ ({cb['failure_count']} fails)"
                cb_info.append(f"Priority {cb['priority']}: {status}")
            
            embed.add_field(
                name="🎯 Our Callbacks",
                value="\n".join(cb_info),
                inline=False
            )
        
        embeds.append(embed)
    
    # CommandAPI Debug
    if hasattr(skysearch_cog, 'command_api'):
        cmd_stats = skysearch_cog.command_api.get_stats()
        embed = discord.Embed(title="⚙️ CommandAPI Debug", color=discord.Color.green())
        
        # Command execution stats
        cmd_metrics = cmd_stats['metrics']
        total_commands = cmd_metrics['total_commands']
        
        if total_commands > 0:
            success_rate = (cmd_metrics['successful_commands'] / total_commands) * 100
            embed.add_field(
                name="📈 Execution Stats",
                value=f"Total: {total_commands}\n"
                      f"Success: {success_rate:.1f}%\n"
                      f"Failed: {cmd_metrics['failed_commands']}\n"
                      f"Cancelled: {cmd_metrics['cancelled_commands']}\n"
                      f"Active: {cmd_stats['active_commands']}",
                inline=True
            )
        
        # Top performing commands
        command_stats = cmd_metrics['command_stats']
        if command_stats:
            top_commands = sorted(command_stats.items(), key=lambda x: x[1]['count'], reverse=True)[:3]
            cmd_info = []
            for cmd_name, cmd_data in top_commands:
                failure_rate = (cmd_data['failures'] / max(cmd_data['count'], 1)) * 100
                cmd_info.append(f"**{cmd_name}**: {cmd_data['count']} runs, {failure_rate:.1f}% fails")
            
            embed.add_field(
                name="🏃 Top Commands",
                value="\n".join(cmd_info),
                inline=True
            )
        
        embeds.append(embed)
    
    # Send all embeds
    for embed in embeds:
        await ctx.send(embed=embed)
```

---

## 🔄 Migration Guide

### From Basic API to Enhanced API

If you're upgrading from the basic API, here's how to migrate:

#### Old Registration (Still Works)
```python
# Basic registration - still supported
api.register_callback(self.my_callback)
api.register_pre_send_callback(self.modify_message)
api.register_post_send_callback(self.react_to_message)
```

#### New Enhanced Registration (Recommended)
```python
# Enhanced registration with metadata
api.register_callback(
    self.my_callback,
    cog_name="MyCog",      # NEW: For tracking and debugging
    priority=5,            # NEW: Execution order
    timeout=10.0          # NEW: Timeout protection
)

api.register_pre_send_callback(
    self.modify_message,
    cog_name="MyCog",
    priority=7,           # Higher priority for message mods
    timeout=5.0          # Shorter timeout for quick operations
)

api.register_post_send_callback(
    self.react_to_message,
    cog_name="MyCog", 
    priority=1,          # Lower priority for reactions
    timeout=15.0        # Longer timeout for complex operations
)
```

#### New Features Available
```python
# Performance monitoring
stats = api.get_stats()
our_performance = stats['metrics']['callback_stats']['MyCog']

# Callback management
api.enable_callback('MyCog')  # Re-enable if circuit breaker triggered
api.unregister_callback(self.my_callback, "basic")  # Granular unregistration

# Configuration
api.set_dedup_window(45.0)  # Adjust deduplication window
```

#### CommandAPI Enhancements
```python
# Old way - monitor all commands
command_api.register_callback(self.track_all_commands)

# New way - filter to specific commands (more efficient)
command_api.register_callback(
    self.track_specific_commands,
    cog_name="MyCog",
    command_filter=["aircraft_icao", "aircraft_callsign"]  # Only these commands
)

# New performance monitoring
performance = command_api.get_command_performance("aircraft_icao")
active_commands = command_api.get_active_commands()
```

---

## 📚 Additional Resources

- **Enhanced Example Implementation**: Check `example/squawk_cog.py` for a complete example using all enhanced features
- **Performance Commands**: Use `*squawkexample debug` and `*squawkexample apistats` to see the enhanced APIs in action
- **Discord.py Documentation**: https://discordpy.readthedocs.io/
- **Red-DiscordBot Documentation**: https://docs.discord.red/

---

## 🤝 Contributing

If you find issues with the enhanced APIs or have suggestions for improvements:

1. Check existing GitHub issues
2. Create a new issue with detailed description
3. Include performance metrics and error logs
4. Consider submitting a pull request

---

*This documentation covers SkySearch Enhanced API v2.0. Last updated: 2025-01-24*

**Key Changes in v2.0:**
- ✅ Circuit breaker protection for all callbacks
- ✅ Performance metrics and monitoring
- ✅ Priority-based callback execution
- ✅ Timeout protection with configurable limits
- ✅ Deduplication system for alerts
- ✅ Command filtering for efficiency
- ✅ Comprehensive callback management
- ✅ Real-time performance analytics
- ✅ Enhanced debugging and troubleshooting tools 
