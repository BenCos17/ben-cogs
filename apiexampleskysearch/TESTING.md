# Testing the SquawkAlertAPI

This guide explains how to test the SquawkAlertAPI integration using the example cog.

## Overview

The SquawkAlertAPI allows other cogs to register callbacks that get triggered when the main SkySearch cog detects emergency squawk codes (7500, 7600, 7700). The API supports three types of callbacks:

1. **Regular callbacks** - Called when an alert is detected
2. **Pre-send callbacks** - Called before the alert message is sent (can modify the message)
3. **Post-send callbacks** - Called after the alert message is sent

## Setup for Testing

### 1. Load the Example Cog

First, make sure both the main SkySearch cog and this example cog are loaded:

```
[p]load skysearch
[p]load squawkexample
```

### 2. Configure Alert Channel

Set up an alert channel in your server where emergency squawk alerts will be sent:

```
[p]aircraft alertchannel #your-alert-channel
```

Optionally, set an alert role to be mentioned:

```
[p]aircraft alertrole @emergency-alerts
```

## Testing Methods

### Method 1: Manual Testing Command

The example cog includes a test command that you can use to manually trigger the API callbacks:

```
[p]testsquawk
```

**What this does:**
- Creates fake aircraft data
- Triggers all three types of callbacks
- Shows you how the message gets modified
- Prints debug output to the console

**Expected output:**
- Console will show debug messages from each callback
- You'll see a test message with modifications from the pre-send callback
- The message will have reactions added by the post-send callback

### Method 2: Wait for Real Emergency Squawks

The SkySearch cog runs a background task every 2 minutes that checks for real emergency squawk codes. When found:

1. **Regular callback** will print to console: `[SquawkExample] Alert detected in ServerName: 7700 for aircraft ABC123`
2. **Pre-send callback** will modify the alert message to add custom content and embed fields
3. **Post-send callback** will add 👀 and ✈️ reactions to the alert message

### Method 3: Monitor Console Output

Watch your bot's console/logs for output like:

```
[SquawkExample] Alert detected in YourServer: 7700 for aircraft A1B2C3
[SquawkExample] Modified alert message for A1B2C3  
[SquawkExample] Alert message sent in YourServer for aircraft A1B2C3
```

## What Each Callback Does

### Regular Callback (`handle_squawk_alert`)
- **Purpose**: Basic notification when an alert is detected
- **Use cases**: Logging, external API calls, custom analysis
- **Example output**: `[SquawkExample] Alert detected in ServerName: 7700 for aircraft ABC123`

### Pre-send Callback (`modify_alert_message`)
- **Purpose**: Modify the alert message before it's sent to Discord
- **Use cases**: Add custom content, modify embeds, change formatting
- **What it does**: 
  - Adds "🔔 **SquawkExample detected this alert!**" to the message
  - Adds a custom embed field showing the cog processed the alert

### Post-send Callback (`after_alert_sent`)
- **Purpose**: React to the message after it's been sent
- **Use cases**: Add reactions, send follow-up messages, update databases
- **What it does**: Adds 👀 and ✈️ reactions to the alert message

## Integration with Main SkySearch Cog

The example cog doesn't need to connect to the main SkySearch cog directly. Instead:

1. **Main SkySearch cog** creates a `SquawkAlertAPI` instance
2. **Your example cog** creates its own `SquawkAlertAPI` instance
3. **When emergency squawks are detected**, the main cog calls `squawk_api.run_pre_send()` and `squawk_api.run_post_send()`
4. **These methods iterate through all registered callbacks** from all cogs

## Troubleshooting

### No callbacks being triggered?
- Make sure both cogs are loaded
- Check that an alert channel is configured
- Verify emergency squawks are actually being detected (check `[p]aircraft squawk 7700` manually)

### Callbacks not modifying messages?
- The main SkySearch cog must call the API methods for modifications to work
- Check that you're returning the modified `message_data` from pre-send callbacks

### Console output not showing?
- Make sure your bot is configured to show console output
- Check that the print statements aren't being filtered by your logging configuration

## Extending the Example

You can extend this example by:

1. **Adding database logging**:
```python
async def handle_squawk_alert(self, guild, aircraft_info, squawk_code):
    # Log to database
    await self.log_emergency_to_db(guild.id, aircraft_info, squawk_code)
```

2. **Sending to external APIs**:
```python
async def handle_squawk_alert(self, guild, aircraft_info, squawk_code):
    # Send to external monitoring system
    await self.notify_external_system(aircraft_info, squawk_code)
```

3. **Custom message formatting**:
```python
async def modify_alert_message(self, guild, aircraft_info, squawk_code, message_data):
    # Add custom styling, additional fields, etc.
    embed = message_data.get('embed')
    if embed:
        embed.color = discord.Color.red()  # Make it more urgent
    return message_data
```

## API Reference

### SquawkAlertAPI Methods

- `register_callback(callback)` - Register a basic callback
- `register_pre_send_callback(callback)` - Register a pre-send callback  
- `register_post_send_callback(callback)` - Register a post-send callback
- `call_callbacks(guild, aircraft_info, squawk_code)` - Trigger basic callbacks
- `run_pre_send(guild, aircraft_info, squawk_code, message_data)` - Run pre-send callbacks
- `run_post_send(guild, aircraft_info, squawk_code, sent_message)` - Run post-send callbacks

### Callback Signatures

```python
# Basic callback
async def handle_squawk_alert(guild, aircraft_info, squawk_code):
    pass

# Pre-send callback (can modify message)
async def modify_alert_message(guild, aircraft_info, squawk_code, message_data) -> dict:
    return message_data  # Return modified message_data

# Post-send callback
async def after_alert_sent(guild, aircraft_info, squawk_code, sent_message):
    pass
``` 