# Spamatron

A Red-DiscordBot cog for typo watching and ghostping features with web dashboard integration.

## Features

### Typo Watch
- Automatically detect and respond to common typos in messages
- Configurable word pairs and responses
- Multiple response options per word
- Server-specific settings

### Ghostping
- Send ghostpings to members in specified channels
- Configurable amount and interval
- Task management and cancellation

### Web Dashboard
- **Stats Page**: View overall statistics across all servers
- **Typo Watch Management**: Web interface for managing typo watch settings
- **Ghostping Management**: Web interface for managing ghostping tasks

## Dashboard Integration

This cog integrates with the Red-DiscordBot dashboard system, providing web-based management interfaces.

### Dashboard Pages

1. **Stats Page** (`/dashboard/spamatron/`)
   - Shows total servers with typo watch enabled
   - Displays total watched words across all servers
   - Shows active ghostping tasks

2. **Typo Watch Management** (`/dashboard/spamatron/typowatch`)
   - Toggle typo watch on/off
   - Add new word pairs with responses
   - Remove words from watch list
   - Update responses for existing words
   - View current watched words

3. **Ghostping Management** (`/dashboard/spamatron/ghostping`)
   - Start ghostping tasks
   - Stop active ghostping tasks
   - View current active tasks

## Commands

### Typo Watch Commands
- `[p]typowatch` - Show current settings
- `[p]typowatch toggle` - Toggle typo watching
- `[p]typowatch add <correct> <typo> <response>` - Add new word
- `[p]typowatch remove <word>` - Remove word from watch list
- `[p]typowatch responses <word> <responses>` - Set responses
- `[p]typowatch list [word]` - List watched words
- `[p]typowatch edit <word> <new_typo>` - Edit typo for word
- `[p]typowatch addresponse <word> <response>` - Add response
- `[p]typowatch delresponse <word> <index>` - Delete response
- `[p]typowatch editresponse <word> <index> <response>` - Edit response

### Ghostping Commands
- `[p]spam <channel> <amount> <message>` - Spam messages
- `[p]ghostping <member> <channel> [amount] [interval]` - Start ghostping
- `[p]stopghostping` - Stop ghostping tasks

## Installation

1. Download the cog files
2. Place them in your Red-DiscordBot cogs folder
3. Load the cog: `[p]load spamatron`
4. Access the dashboard at your bot's dashboard URL

## Requirements

- Red-DiscordBot with dashboard enabled
- Administrator permissions for configuration commands
- Dashboard cog must be loaded for web interface

## Configuration

The cog uses Red's config system to store settings per guild. All settings are managed through commands or the web dashboard interface.

## Dashboard Access

Once loaded, the dashboard pages will be available at:
- `/dashboard/spamatron/` - Main stats page
- `/dashboard/spamatron/typowatch` - Typo watch management
- `/dashboard/spamatron/ghostping` - Ghostping management

The dashboard requires proper permissions and the dashboard cog to be loaded and configured. 