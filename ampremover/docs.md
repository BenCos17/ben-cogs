# AmputatorBot Documentation

## Overview

AmputatorBot is a Discord bot cog designed to convert AMP URLs to their canonical URLs using the AmputatorBot API. This cog provides several commands to manage server preferences, convert URLs, and display the current settings.

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
