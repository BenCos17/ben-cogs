# Servertools Cog Documentation

## Overview
Servertools is a Red-DiscordBot cog that provides server utility and moderation helpers, plus opt-in Spotify link cleaning.

Main features:
- Moderator DM sender with confirmation
- Voice channel member move command
- Channel lockdown helper
- Bulk message purge
- Audit log viewer
- Server icon updater (URL or attachment)
- Fake Discord ping image generator
- Auto-reactions by user and channel
- User online-status DM notifications
- Opt-in Spotify URL cleaner (removes si tracker parameter)

## Requirements
- Red-DiscordBot 3.4.0 or newer
- Python packages:
  - aiohttp
  - Pillow

## Data Storage
This cog uses Red Config and stores:

Guild scope:
- auto_reactions: dictionary keyed as channel_id-user_id with emoji value
- spotify_autoclean: boolean, default false

User scope:
- online_notifications: list of tracked user IDs

## Commands
Prefix examples use [p] as your bot prefix.

### 1) moddm
- Name: moddm
- Permission required: Manage Server
- Usage: [p]moddm <user> <message>
- What it does:
  - Sends a confirmation prompt in the channel
  - Waits up to 30 seconds for yes/y/no/n
  - If confirmed, sends the message to the target user in DM as an embed

Notes:
- Works only in a server
- Target user must be a member of that server

### 2) voicemove
- Name: voicemove
- Permission required: Move Members
- Usage: [p]voicemove <member> <voice_channel>
- What it does:
  - Moves the specified member to the specified voice channel

### 3) ld
- Name: ld
- Permission required: Manage Channels
- Usage: [p]ld <text_channel> <permissions>
- What it does:
  - Locks down the target text channel for @everyone by disabling send_messages

Important:
- The permissions text argument is currently accepted but not used by the implementation.

### 4) purge
- Name: purge
- Permission required: Manage Messages
- Usage: [p]purge <amount>
- What it does:
  - Deletes up to amount recent messages from the current channel

### 5) auditlog
- Name: auditlog
- Permission required: View Audit Log
- Usage: [p]auditlog <amount>
- What it does:
  - Sends recent audit log entries as channel messages

### 6) setservericon
- Name: setservericon
- Scope: Guild only
- Permission required: Manage Server
- Usage:
  - [p]setservericon <image_url>
  - [p]setservericon with an attached image
- What it does:
  - Updates the guild icon using PNG or WEBP image data

### 7) fakeping
- Name: fakeping
- Scope: Guild only
- Usage: [p]fakeping
- What it does:
  - Downloads the server icon
  - Draws a red notification badge with 1
  - Sends the generated image file

### 8) autoreact command group
- Name: autoreact
- Usage root: [p]autoreact
- What it does:
  - Manages automatic reactions for a specific user in a specific channel

Subcommands:
- [p]autoreact add <user> <channel> <emoji>
  - Adds or overwrites an auto-reaction mapping
- [p]autoreact remove <user> <channel>
  - Removes a mapping
- [p]autoreact list
  - Lists all mappings for the server

Runtime behavior:
- When a non-bot user sends a message, if channel_id-user_id exists in mappings, the bot adds that emoji reaction.

### 9) notify command group
- Name: notify
- Usage root: [p]notify
- What it does:
  - Lets a user track specific members and receive DM alerts when they come online

Subcommands:
- [p]notify add <user>
  - Adds user to your tracking list
  - Bots cannot be tracked
- [p]notify remove <user>
  - Removes user from your tracking list
- [p]notify list
  - Shows users you are currently tracking

Runtime behavior:
- On member status changes, tracked users are DMd when a member moves from offline or invisible to online.

### 10) spotifyclean command group
- Name: spotifyclean
- Scope: Guild only
- Permission required: Manage Server
- Usage root: [p]spotifyclean
- What it does:
  - Controls opt-in Spotify link cleaning per server

Subcommands:
- [p]spotifyclean on
  - Enables auto-cleaning for this guild
- [p]spotifyclean off
  - Disables auto-cleaning
- [p]spotifyclean status
  - Shows current enabled or disabled state

Runtime behavior:
- When enabled, the bot scans each non-bot message for open.spotify.com links.
- It removes only the si query parameter.
- If a cleaned URL differs from original, it posts the cleaned link to the channel.
- Original messages are not edited or deleted.

## Event Listeners
This cog includes these listeners:

1. on_message
- Ignores bot messages and DMs
- Handles auto-reactions
- Handles Spotify URL auto-clean posting when enabled

2. on_member_update
- Checks status transitions
- Sends online notifications to users tracking that member

## Permissions Summary
- Manage Server: moddm, setservericon, spotifyclean group
- Move Members: voicemove
- Manage Channels: ld
- Manage Messages: purge
- View Audit Log: auditlog
- No explicit command permission decorators: fakeping, autoreact group, notify group

## Operational Notes
- If the bot lacks Discord permissions for an action, commands return an error message.
- notify alerts are sent via DM and may fail if user DMs are closed.
- Spotify cleaning applies only to links in message text and only for open.spotify.com URLs.

## Quick Start
1. Load the cog.
2. Optional: enable Spotify cleaner in a server with [p]spotifyclean on.
3. Add auto-reactions with [p]autoreact add.
4. Add online tracking with [p]notify add.

## End User Data Statement
The cog stores guild and user data for utility features through Red Config and does not share that data with third parties.
