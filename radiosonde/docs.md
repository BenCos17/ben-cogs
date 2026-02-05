# Radiosonde Cog Documentation

## Overview

The `Radiosonde` cog allows you to track radiosondes (weather balloons) using the SondeHub API. It automatically monitors specified sondes and sends periodic updates to a configured channel with their current location, altitude, and speed.

## Installation

1. Ensure you have [Red DiscordBot](https://docs.discord.red/en/stable/) installed and running.
2. Add this cog to your bot:
   ```
   [p]repo add ben-cogs https://github.com/bencos18/ben-cogs
   [p]cog install ben-cogs radiosonde
   ```
   Replace `[p]` with your bot's prefix.

---

## Commands

### Main Command Group
- **`[p]sonde`**
  - Shows help or usage info for the sonde tracking commands.

#### Subcommands

- **`[p]sonde add <sonde_id>`**
  - Add a sonde to track in this server.
  - The sonde ID should match the ID from the SondeHub API.
  - Example: `[p]sonde add U1234567`

- **`[p]sonde remove <sonde_id>`**
  - Stop tracking a specific sonde.
  - Example: `[p]sonde remove U1234567`

- **`[p]sonde list`**
  - List all sondes currently being tracked in this server.
  - Example: `[p]sonde list`

- **`[p]sonde status`**
  - List the current status of all tracked sondes (latitude, longitude, altitude, speed). Fetches live data from the SondeHub API.
  - Example: `[p]sonde status`

- **`[p]sonde setchannel <channel>`**
  - Set the channel where sonde updates will be sent.
  - You can mention the channel or use the channel ID.
  - Example: `[p]sonde setchannel #weather-updates` or `[p]sonde setchannel 123456789012345678`

- **`[p]sonde interval <seconds>`**
  - Set how often (in seconds) the bot checks for sonde updates.
  - Minimum interval is 30 seconds.
  - Default is 300 seconds (5 minutes).
  - Example: `[p]sonde interval 60` (check every minute)

---

## Setup Guide

### How to Set Up Sonde Tracking

1. **Set the update channel:**
   ```
   [p]sonde setchannel #your-channel
   ```
   This tells the bot where to send sonde updates.

2. **Add a sonde to track:**
   ```
   [p]sonde add <sonde_id>
   ```
   Replace `<sonde_id>` with the actual sonde ID you want to track. You can find sonde IDs from the [SondeHub website](https://sondehub.org/) or API.

3. **(Optional) Adjust the update interval:**
   ```
   [p]sonde interval 120
   ```
   This sets the bot to check for updates every 120 seconds (2 minutes).

4. **View tracked sondes:**
   ```
   [p]sonde list
   ```
   This shows all sondes currently being tracked.

### Example Setup Flow

```
[p]sonde setchannel #weather-data
[p]sonde add U1234567
[p]sonde add U7654321
[p]sonde interval 180
[p]sonde list
```

---

## Update Format

When a tracked sonde is updated, the bot sends a message with the following information:
- **Sonde ID**: The identifier of the sonde
- **Lat**: Latitude coordinate
- **Lon**: Longitude coordinate
- **Alt**: Altitude in meters
- **Speed**: Velocity in meters per second

Example update message:
```
**Sonde U1234567 Update**
Lat: 40.7128
Lon: -74.0060
Alt: 1234.5 m
Speed: 5.2 m/s
```

---

## Features & Notes

- **Per-server configuration**: Each server can track different sondes and have different update channels.
- **Automatic updates**: The bot continuously monitors tracked sondes and sends updates automatically.
- **API Source**: Uses the [SondeHub API](https://api.v2.sondehub.org/sondes/latest.json) for real-time sonde data.
- **Update frequency**: The bot checks for updates every minute, but only sends messages based on your configured interval.
- **Minimum interval**: Update intervals must be at least 30 seconds to prevent API abuse.

---

## Troubleshooting

- **No updates being sent**: Make sure you've set a channel with `[p]sonde setchannel` and added at least one sonde with `[p]sonde add`.
- **Sonde not found**: Verify the sonde ID is correct. The sonde must be active and present in the SondeHub API.
- **Updates too frequent/infrequent**: Adjust the interval using `[p]sonde interval <seconds>`.

---

## Permissions

- Users need permission to send messages in the channel where commands are used.
- The bot needs permission to send messages in the configured update channel.
