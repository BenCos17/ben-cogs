# SkySearch - Aircraft Tracking Discord Bot Cog

A powerful, modular Discord bot cog for tracking aircraft and airport information using real-time data from airplanes.live and other aviation APIs.

## 🚀 Getting Started

To use the SkySearch cog, follow these steps:

1. **Dependencies**:
 red discord bot: https://docs.discord.red/en/stable/

2. **Configure API Keys** :
   - Set up airplanes.live API key: `[p]setapikey <your-api-key>`
   - Optional: Configure Google Maps API for airport imagery
   - Optional: Configure OpenAI API for airport summaries
   - Optional: Configure airportdb.io API for runway data

3. **Load the Cog**:
   ```bash
   [p] repo add ben https://github.com/bencos17/ben-cogs
   [p]cog install ben skysearch 
   [p]load skysearch
   ```

## 🚀 Using the Cog

### Aircraft Commands
- `[p]aircraft icao <hex>` - Search by ICAO hex code
- `[p]aircraft callsign <callsign>` - Search by flight callsign
- `[p]aircraft reg <registration>` - Search by registration
- `[p]aircraft type <type>` - Search by aircraft type
- `[p]aircraft squawk <code>` - Search by squawk code
- `[p]aircraft military` - View military aircraft
- `[p]aircraft ladd` - View LADD-restricted aircraft
- `[p]aircraft pia` - View private ICAO aircraft
- `[p]aircraft radius <lat> <lon> <radius>` - Search within radius
- `[p]aircraft closest <lat> <lon> [radius]` - Find closest aircraft
- `[p]aircraft export <type> <value> <format>` - Export data
- `[p]aircraft scroll` - Scroll through aircraft

### Watchlist Commands
- `[p]aircraft watchlist` - View your watchlist
- `[p]aircraft watchlist add <icao>` - Add aircraft to your personal watchlist
- `[p]aircraft watchlist remove <icao>` - Remove aircraft from watchlist
- `[p]aircraft watchlist list` - List all watched aircraft with online/offline status
- `[p]aircraft watchlist status` - Get detailed status of all watched aircraft
- `[p]aircraft watchlist clear` - Clear your entire watchlist
- `[p]aircraft watchlist cooldown [minutes]` - Set or view notification cooldown (default: 10 minutes)

**Features:**
- Personal watchlist per user
- Automatic notifications when watched aircraft come online (via DM or guild channel)
- If aircraft is already online when added, you'll see its current status immediately
- Configurable cooldown per user (1-1440 minutes, default: 10 minutes) to prevent spam
- Background task checks every 3 minutes

### Airport Commands
- `[p]airport info <code>` - Get airport information
- `[p]airport runway <code>` - Get runway information
- `[p]airport navaid <code>` - Get navigational aids
- `[p]airport forecast <code>` - Get weather forecast

### Admin Commands
- `[p]aircraft alertchannel [#channel]` - Set alert channel
- `[p]aircraft alertrole [@role]` - Set alert role
- `[p]aircraft autoicao [true/false]` - Configure auto ICAO lookup
- `[p]aircraft autodelete [true/false]` - Configure auto-deletion
- `[p]aircraft showalertchannel` - Show alert status

### Custom Alerts
- `[p]aircraft addalert <type> <value> [cooldown] [#channel]`
  - Types: `icao`, `callsign`, `squawk`, `type`, `reg`
  - Cooldown minutes (default: 5). Optional custom destination channel.
- `[p]aircraft removealert <alert_id>`
- `[p]aircraft listalerts`
- `[p]aircraft clearalerts`
- `[p]aircraft forcealert <alert_id>` (owner only) — send immediately, ignoring cooldown

Notes:
- The background scanner runs every 2 minutes and checks the full aircraft feed.
- Custom alerts use the same embed/buttons and pre/post hooks as emergency alerts.

### Owner Commands
- `[p]setapikey <key>` - Set airplanes.live API key
- `[p]apikey` - Check API key status
- `[p]clearapikey` - Clear API key
- `[p]debugapi` - Debug API issues

### API Monitoring Commands
- `[p]skysearch apistats` - View comprehensive API request statistics and performance metrics
- `[p]skysearch apistats_config` - View API statistics auto-save configuration (owner only)
- `[p]skysearch apistats_reset` - Reset API statistics (owner only)
- `[p]skysearch apistats_save` - Manually save API statistics (owner only)

### Dashboard Integration
- `/third-parties/Skysearch` - Web interface for the cog
there is 4 total pages in it 
 - `Main Page` - shows stats for airplanes.live and tagged aircraft (tags aren't currently updated)
 - `Apistats` - shows apistats for the cog itself
 - `Guild` - allows you to change cog settings in the dashboard (uses ids, to get them enable developer mode on discord)
 - `Lookup` - allows you to lookup data directly in the cog dashboard page
