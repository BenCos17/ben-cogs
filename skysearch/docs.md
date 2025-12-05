# How to Use SkySearch

## Getting Started

### First Time Setup
1. **Load the cog** in your Red-DiscordBot
2. **Set up API keys** (optional but recommended):
   - For airplanes.live:
     ```
     *aircraft setapikey YOUR_API_KEY_HERE
     ```
   - For OpenWeatherMap (for weather/forecast):
     ```
     *airport setowmkey YOUR_OWM_API_KEY_HERE
     ```

### Basic Commands
- `*skysearch` - Main menu
- `*aircraft` - Aircraft commands
- `*airport` - Airport commands

## Finding Aircraft

### Quick Aircraft Lookup
**By ICAO Code** (most common):
```
*aircraft icao a03b67
```

**By Flight Number**:
```
*aircraft callsign DAL460
```

**By Registration**:
```
*aircraft reg N12345
```

### What You'll See
Each aircraft lookup shows:
- Aircraft type and year
- Current position and altitude
- Speed and heading
- Flight status
- Aircraft photo (if available)
- Links to track live

### Emergency Aircraft
Look for aircraft with emergency squawk codes:
- **7700** = General emergency
- **7600** = Radio failure
- **7500** = Hijacking

## Finding Airports

### Airport Information
```
*airport info KLAX
```
Shows:
- Airport name and location
- Basic details
- Airport photo
- Google Maps link

### Runway Information
```
*airport runway KLAX
```
Shows runway details like length, width, and surface type.

### Weather at Airports
```
*airport forecast KLAX
```
Shows current weather and 3-day forecast.

## Advanced Aircraft Search

### Find Aircraft Near You
```
*aircraft closest 40.7128 -74.0060 100
```
Finds the closest aircraft to your coordinates (latitude, longitude, radius in miles).

### Find Aircraft in an Area
```
*aircraft radius 40.7128 -74.0060 50
```
Shows all aircraft within 50 miles of the coordinates.

### Special Aircraft Types
```
*aircraft military    # Military aircraft
*aircraft ladd        # Restricted aircraft
*aircraft pia         # Private aircraft
```

## Exporting Data

### Export Aircraft Information
```
*aircraft export icao "a03b67 a1ef6a" pdf
*aircraft export callsign DAL460 csv
*aircraft export squawk 7700 html
```

**Formats available**: PDF, CSV, TXT, HTML

## Setting Up Alerts

### Emergency Squawk Alerts
1. **Set alert channel**:
   ```
   *aircraft alertchannel #alerts
   ```

2. **Set alert role** (optional):
   ```
   *aircraft alertrole @AircraftAlerts
   ```

3. **Check status**:
   ```
   *aircraft showalertchannel
   ```

### What Happens During Emergencies
- Bot mentions the alert role
- Shows aircraft information
- Notifies when aircraft lands
- Runs automatically every 2 minutes

### Custom Alerts (New)
Custom alerts let you watch for specific aircraft criteria and receive styled alerts like emergencies.

Supported types:
- `icao` — specific ICAO hex
- `callsign` — flight callsign
- `squawk` — squawk code (e.g., 7700)
- `type` — aircraft type code
- `reg` — registration

Commands:
```
*aircraft addalert <type> <value> [cooldown_minutes] [#channel]
*aircraft listalerts
*aircraft removealert <alert_id>
*aircraft clearalerts
```

Owner testing command:
```
*aircraft forcealert <alert_id>
```

Behavior:
- Runs automatically every 2 minutes (full-aircraft feed scan)
- Uses the same embed, buttons, and pre/post hooks as emergency alerts
- Sends to the alert channel by default, or to a per-alert custom channel if set

### Alert Cooldown
You can set a cooldown to prevent the bot from spamming alerts for the same aircraft.

**Set Cooldown**
```
*aircraft alertcooldown 15
```
This sets a 15-minute cooldown.

**Check Cooldown**
```
*aircraft alertcooldown
```
This shows the current cooldown.

## API Monitoring

### View API Statistics
```
*skysearch apistats
```
Shows comprehensive statistics about API usage:
- Total requests and success rates
- Performance metrics and response times
- API mode usage (primary vs fallback)
- Endpoint-specific usage patterns
- Error tracking and rate limits

### Dashboard Access
Visit `/dashboard/apistats` in your web browser to view API statistics in a web interface.

### Owner-Only Commands
- `*skysearch apistats_config` - View auto-save configuration
- `*skysearch apistats_reset` - Reset all statistics
- `*skysearch apistats_save` - Manually save statistics

## Aircraft Watchlist

### Personal Watchlist
Create your own personal watchlist of aircraft to monitor. You'll receive notifications when watched aircraft come online.

### Adding Aircraft to Watchlist
```
*aircraft watchlist add A03B67
```
Adds the aircraft with ICAO code `A03B67` to your watchlist.

**Note:** If the aircraft is already online when you add it, you'll immediately see its current status (callsign, altitude, speed, position) instead of waiting for the next notification.

### Viewing Your Watchlist
```
*aircraft watchlist list
```
Shows all aircraft in your watchlist with their current online/offline status.

### Detailed Status
```
*aircraft watchlist status
```
Shows detailed information about all watched aircraft including:
- Callsign
- Altitude
- Speed
- Position
- Online/offline status

### Removing Aircraft
```
*aircraft watchlist remove A03B67
```
Removes the aircraft from your watchlist.

### Clearing Watchlist
```
*aircraft watchlist clear
```
Removes all aircraft from your watchlist.

### Configuring Notification Cooldown
```
*aircraft watchlist cooldown          # Check current cooldown
*aircraft watchlist cooldown 5        # Set to 5 minutes
*aircraft watchlist cooldown 30       # Set to 30 minutes
*aircraft watchlist cooldown 1440     # Set to 24 hours (maximum)
```

**Cooldown Settings:**
- **Default:** 10 minutes
- **Range:** 1-1440 minutes (1 minute to 24 hours)
- **Per-user:** Each user can set their own cooldown preference
- **Purpose:** Prevents spam notifications for the same aircraft

After receiving a notification for a watched aircraft, you won't receive another notification for the same aircraft until your configured cooldown period expires.

### Watchlist Notifications
- **Automatic notifications** when watched aircraft come online
- Notifications sent via **DM** (if enabled) or in a **shared guild channel**
- **Configurable cooldown** per user (default: 10 minutes) to prevent spam
- Background task checks every **3 minutes**
- If aircraft is **already online** when added, you'll see its status immediately

### How It Works
1. Add aircraft to your watchlist using their ICAO hex code
2. The bot automatically checks your watchlist every 3 minutes
3. When a watched aircraft comes online, you receive a notification
4. Notifications include aircraft details and a link to track on airplanes.live

## Convenience Features

### Auto ICAO Lookup
Enable automatic aircraft lookup when someone types a 6-character hex code:
```