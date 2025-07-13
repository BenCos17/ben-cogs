# SkySearch Cog Documentation

## Overview
SkySearch is a powerful aircraft tracking and information Discord bot cog that provides real-time aircraft data, airport information, and emergency squawk monitoring. It integrates with multiple aviation APIs to deliver comprehensive aircraft intelligence.

## Installation

### Prerequisites
- Red-DiscordBot installed and configured
- Python 3.8 or higher
- Internet connection for API access

### Setup Steps
1. **Download the cog files** to your Red-DiscordBot cogs directory
2. **Load the cog** using Red-DiscordBot's cog manager or manually
3. **Set up API key** (optional but recommended for full functionality)
4. **Configure alert channels** for emergency squawk monitoring

## API Configuration

### Setting Up API Key
```bash
# Set the airplanes.live API key (owner only)
*setapikey YOUR_API_KEY_HERE

# Check API key status
*apikey

# Clear API key if needed
*clearapikey
```

**Note**: While the cog works without an API key, some features may be limited. Get your free API key from [airplanes.live](https://airplanes.live/).

## Core Commands

### Main Menu
```
*skysearch
```
Displays the main SkySearch menu with links to aircraft and airport commands.

### Statistics
```
*skysearch stats
```
Shows comprehensive statistics about data sources, tracked aircraft, and categorized aircraft counts.

## Aircraft Commands

### Search Commands

#### ICAO Lookup
```
*aircraft icao <hex_code>
```
Get detailed information about an aircraft by its 24-bit ICAO address.

**Example**: `*aircraft icao a03b67`

#### Callsign Search
```
*aircraft callsign <callsign>
```
Find aircraft by their flight callsign.

**Example**: `*aircraft callsign DAL460`

#### Registration Search
```
*aircraft reg <registration>
```
Search for aircraft by their registration number.

**Example**: `*aircraft reg N12345`

#### Aircraft Type Search
```
*aircraft type <type>
```
Find aircraft by their type/model.

**Example**: `*aircraft type A321`

#### Squawk Code Search
```
*aircraft squawk <squawk>
```
Find aircraft by their transponder squawk code.

**Example**: `*aircraft squawk 7700`

#### Radius Search
```
*aircraft radius <lat> <lon> <radius>
```
Find aircraft within a specified radius of coordinates.

**Example**: `*aircraft radius 40.7128 -74.0060 50`

#### Closest Aircraft
```
*aircraft closest <lat> <lon> [radius]
```
Find the closest aircraft to specified coordinates.

**Example**: `*aircraft closest 40.7128 -74.0060 100`

### Special Aircraft Commands

#### Military Aircraft
```
*aircraft military
```
View live military aircraft with detailed information and photos.

#### LADD-Restricted Aircraft
```
*aircraft ladd
```
View aircraft with Limited Aircraft Data Display restrictions.

#### Private ICAO Aircraft
```
*aircraft pia
```
View aircraft using private ICAO addresses.

### Export Functionality
```
*aircraft export <search_type> <search_value> <format>
```
Export aircraft data to various formats.

**Search Types**: `icao`, `callsign`, `squawk`, `type`
**Formats**: `csv`, `pdf`, `txt`, `html`

**Examples**:
- `*aircraft export icao "a03b67 a1ef6a" pdf`
- `*aircraft export callsign DAL460 csv`
- `*aircraft export squawk 7700 html`

### Utility Commands

#### Scroll Through Aircraft
```
*aircraft scroll
```
Browse through available aircraft with interactive navigation.

## Airport Commands

### Airport Information
```
*airport info <code>
```
Get comprehensive airport information by ICAO or IATA code.

**Example**: `*airport info KLAX`

### Runway Information
```
*airport runway <code>
```
Get detailed runway information for an airport.

**Example**: `*airport runway KLAX`

### Navigational Aids
```
*airport navaid <code>
```
Get navigational aids information for an airport.

**Example**: `*airport navaid KLAX`

### Weather Forecast
```
*airport forecast <code>
```
Get weather forecast for an airport.

**Example**: `*airport forecast KLAX`

## Configuration Commands

### Alert Channel Setup
```
*aircraft alertchannel [#channel]
```
Set or clear the channel for emergency squawk alerts.

**Examples**:
- `*aircraft alertchannel #alerts` - Set alert channel
- `*aircraft alertchannel` - Clear alert channel

### Alert Role Setup
```
*aircraft alertrole @role
```
Set or clear the role to mention during emergency squawks.

**Examples**:
- `*aircraft alertrole @AircraftAlerts` - Set alert role
- `*aircraft alertrole` - Clear alert role

### Auto ICAO Lookup
```
*aircraft autoicao [true/false]
```
Enable or disable automatic ICAO lookup when users type 6-character hex codes.

**Examples**:
- `*aircraft autoicao true` - Enable auto lookup
- `*aircraft autoicao false` - Disable auto lookup
- `*aircraft autoicao` - Check current status

### Auto-Delete Settings
```
*aircraft autodelete [true/false]
```
Control automatic deletion of "not found" messages.

**Examples**:
- `*aircraft autodelete true` - Enable auto-delete
- `*aircraft autodelete false` - Disable auto-delete
- `*aircraft autodelete` - Check current status

### Alert Status
```
*aircraft showalertchannel
```
Check the status of emergency squawk monitoring and alert channels.

## Owner Commands

### API Debugging
```
*aircraft debugapi
```
Debug API connectivity and configuration issues (sends detailed report via DM).

**Note**: Owner only command.

### API Key Management
```
*setapikey <key>     # Set API key
*apikey              # Check API status
*clearapikey         # Clear API key
```
Manage the airplanes.live API key.

**Note**: Owner only commands.

## Emergency Squawk Monitoring

### Automatic Monitoring
SkySearch automatically monitors for emergency squawk codes:
- **7500**: Aircraft hijacking
- **7600**: Radio communication failure
- **7700**: General emergency

### Alert System
When emergency squawks are detected:
1. **Role mention** (if configured)
2. **Aircraft information** with emergency status
3. **Landing notifications** when aircraft descend below 25 feet

### Background Task
The monitoring runs every 2 minutes and respects API rate limits.

## Data Sources

### Primary APIs
- **airplanes.live**: Real-time aircraft tracking data
- **Planespotters.net**: Aircraft photos and information
- **airport-data.com**: Airport information
- **airportdb.io**: Runway and navaid data
- **Google Maps**: Airport imagery and mapping

### Categorized Aircraft
SkySearch includes intelligence on:
- Law enforcement aircraft
- Military and government aircraft
- Medical response aircraft
- Media/news aircraft
- Damaged aircraft
- Wartime conflict aircraft
- Utility/agricultural aircraft
- Balloons and special craft
- Suspicious surveillance aircraft

## Troubleshooting

### Common Issues

#### No Aircraft Found
- Check if the aircraft is currently transmitting
- Verify the search parameters are correct
- Try different search methods (ICAO vs callsign)

#### No Photos Available
- Photos depend on community contributions to Planespotters.net
- Not all aircraft have photos available
- Default aircraft icon is shown when no photo exists

#### API Errors
- Use `*aircraft debugapi` to diagnose connectivity issues
- Check your API key configuration
- Verify internet connectivity

#### Alert System Not Working
- Check alert channel configuration with `*aircraft showalertchannel`
- Ensure the bot has permissions in the alert channel
- Verify the alert role exists and is mentionable

### Debug Commands
```
*aircraft debugapi
```
Provides comprehensive debugging information including:
- API key status
- Connectivity tests
- Response validation
- Rate limit information

## Best Practices

### Server Setup
1. **Create dedicated channels** for aircraft alerts
2. **Set up appropriate roles** for different alert levels
3. **Configure auto-delete** based on your server's needs
4. **Use auto ICAO lookup** for convenience

### Command Usage
1. **Use specific search terms** for better results
2. **Combine search methods** when one doesn't work
3. **Export data** for analysis and record-keeping
4. **Monitor emergency squawks** for safety awareness

### Performance
1. **Respect API rate limits** - the cog handles this automatically
2. **Use appropriate radius** for area searches
3. **Limit export sizes** for large datasets
4. **Monitor background tasks** for system health

## Support

### Getting Help
- Check this documentation first
- Use the built-in help system: `*help aircraft` or `*help airport`
- Review the README.md file for technical details
- Use debug commands for troubleshooting

### Contributing
- Report issues with detailed information
- Include debug output when possible
- Test with different aircraft types and scenarios

## Version Information
This documentation covers SkySearch cog version as of the latest update. For the most current information, refer to the cog's README.md file and built-in help system. 