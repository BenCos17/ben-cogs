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

## Convenience Features

### Auto ICAO Lookup
Enable automatic aircraft lookup when someone types a 6-character hex code:
```
*aircraft autoicao true
```

### Auto-Delete "Not Found" Messages
```
*aircraft autodelete true
```
Automatically removes "no aircraft found" messages after 5 seconds.

## Server Management

### Check Settings
```
*aircraft autoicao     # Check auto ICAO status
*aircraft autodelete   # Check auto-delete status
```

### Clear Settings
```
*aircraft alertchannel    # Remove alert channel
*aircraft alertrole       # Remove alert role
```

## Troubleshooting

### No Aircraft Found?
- Try different search methods (ICAO vs callsign)
- Check if the aircraft is currently transmitting
- Some aircraft may be blocked for privacy

### No Photos?
- Photos depend on community contributions
- Not all aircraft have photos available
- Default icon is shown when no photo exists

### Alerts Not Working?
- Check channel permissions
- Verify the alert role exists
- Use `*aircraft showalertchannel` to check status

### API Issues?
If you're the bot owner, use:
```
*aircraft debugapi
```
This sends detailed debugging information to your DMs.

## Tips for Best Results

### Search Tips
- **ICAO codes** are usually the most reliable
- **Flight numbers** work best for commercial flights
- **Registration numbers** work for most aircraft
- Use **quotes** for multi-word searches

### Alert Setup Tips
- Create a dedicated #alerts channel
- Set up an @AircraftAlerts role
- Test with `*aircraft showalertchannel`
- Monitor the channel for emergency squawks

### Export Tips
- Use **PDF** for reports and sharing
- Use **CSV** for data analysis
- Use **HTML** for web viewing
- Multiple ICAO codes work: `"a03b67 a1ef6a"`

## Common Use Cases

### Aviation Enthusiasts
- Track specific aircraft: `*aircraft icao a03b67`
- Monitor military flights: `*aircraft military`
- Export flight data: `*aircraft export callsign DAL460 pdf`

### Server Administrators
- Set up emergency alerts
- Configure auto ICAO lookup
- Monitor aircraft activity

### Researchers
- Export data for analysis
- Track specific aircraft types
- Monitor emergency situations

## Getting Help

### Built-in Help
- `*help aircraft` - Detailed aircraft commands
- `*help airport` - Detailed airport commands
- `*aircraft` - Quick aircraft command overview
- `*airport` - Quick airport command overview

### Support
- Check this guide first
- Use the built-in help system
- Contact the bot owner for technical issues

For further assistance, you can message me on Discord at **bencos17** or tag me in the Red-DiscordBot server. 