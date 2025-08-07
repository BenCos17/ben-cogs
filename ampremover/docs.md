# AmputatorBot Documentation

## Overview

AmputatorBot is a Discord bot cog designed to convert AMP URLs to their canonical URLs using the AmputatorBot API. This cog provides several commands to manage server preferences, convert URLs, and display the current settings. It also includes Red-Web-Dashboard integration for web-based management.

## Features

- **AMP URL Conversion**: Convert AMP URLs to canonical URLs using the AmputatorBot API
- **Server Settings**: Per-server opt-in/opt-out functionality
- **Automatic Detection**: Automatically detect and convert AMP URLs in messages (when enabled)
- **Web Dashboard**: Full Red-Web-Dashboard integration with web-based management interface
- **Statistics**: View conversion statistics and settings through the web interface

## Installation

1. Ensure you have Red-DiscordBot  installed.
2. Add the repository using the command: [p] is your bots prefix 
   ```
   [p]repo add ben-cogs https://github.com/bencos17/ben-cogs
   ```
3. Install the cog using the command: 
   ```
   [p]cog install ben-cogs ampremover
   ```

## Commands

### `[p]amputator`

The base command for AmputatorBot operations. This command provides a brief overview of the available subcommands.

**Usage:**
`[p]amputator`

### `[p]amputator optin`

Opt-in to use the AmputatorBot service. This command cannot be used in DMs and is a per-server setting.

**Usage:**
`[p]amputator optin`

### `[p]amputator optout`

Opt-out from using the AmputatorBot service. This command cannot be used in DMs and is a per-server setting.

**Usage:**
`[p]amputator optout`

### `[p]amputator convert <message>`

Converts AMP URLs to canonical URLs using the AmputatorBot API. Provide the message containing the URLs to be converted.

**Usage:**
`[p]amputator convert <message>`

### `[p]amputator settings`

Displays the current configuration settings for the AmputatorBot, including the opt-in status of the server. This command cannot be used in DMs.

**Usage:**
`[p]amputator settings`

**Details:**
- **Opt-in Status:** Shows whether the server is currently opted in to use the AmputatorBot service. A checkmark (✅) indicates the server is opted in, while a cross (❌) indicates it is not.
- **Embed Display:** The settings are displayed in an embed format, with the title showing the server's name. The embed color is green if opted in and red if not.
- **Footer Information:** The embed includes a footer with a reminder to use `[p]amputator` for more commands.

## Web Dashboard Integration

This cog includes full Red-Web-Dashboard integration, providing a web-based interface for managing AMP URL conversion settings and viewing statistics.

### Dashboard Features

- **URL Converter**: Web-based form for converting AMP URLs to canonical URLs
- **Settings Management**: Configure automatic AMP URL conversion settings for each guild
- **Statistics View**: View guild settings, bot information, and available commands
- **Real-time Updates**: Settings changes are applied immediately

### Accessing the Dashboard

1. Ensure you have Red-Web-Dashboard installed and configured
2. Load this cog on your bot
3. Access the dashboard through your Red-Web-Dashboard URL
4. Navigate to the "Third Parties" section
5. Find "AmputatorBot" in the list of available third-party integrations

### Dashboard Pages

- **Main Page** (`/third-party/AmputatorBot`): Convert AMP URLs to canonical URLs
- **Settings Page** (`/third-party/AmputatorBot/settings`): Configure guild settings
- **Statistics Page** (`/third-party/AmputatorBot/stats`): View guild statistics and information

### Requirements

- Red-Web-Dashboard must be installed and running
- The Dashboard cog must be loaded on your bot
- Users must have appropriate permissions to access the dashboard
