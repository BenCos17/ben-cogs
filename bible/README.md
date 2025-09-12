# Bible Cog for Red Discord Bot

A comprehensive Bible cog for Red Discord Bot that integrates with the API.Bible service to provide Bible verse lookups, searches, and more.

## Features

- 📖 **Verse Lookup**: Get specific Bible verses by reference
- 🔍 **Bible Search**: Search for verses containing specific text
- 📚 **Chapter Reading**: Read entire Bible chapters
- 🎲 **Random Verses**: Get random popular Bible verses
- ⚙️ **Configurable**: Customizable settings for display and behavior
- 🎨 **Beautiful Embeds**: Rich, formatted display of Bible content
- 🔐 **Secure**: Uses Red's config system for API key storage

## Installation

1. Place the `bible` folder in your Red bot's `cogs` directory
2. Load the cog: `[p]load bible`
3. Set your API key: `[p]bible setkey YOUR_API_KEY_HERE`

## Getting an API Key

1. Visit [API.Bible](https://scripture.api.bible/livedocs)
2. Sign up for a free account
3. Get your API key from the dashboard
4. Use `[p]bible setkey YOUR_KEY` to configure it

## Commands

### Basic Commands

- `[p]bible verse <reference>` - Get a specific verse (e.g., `[p]bible verse John 3:16`)
- `[p]bible chapter <reference>` - Get an entire chapter (e.g., `[p]bible chapter John 3`)
- `[p]bible search <query>` - Search for verses containing text
- `[p]bible random` - Get a random popular verse
- `[p]bible info` - View available Bibles and API information

### Configuration Commands (Owner Only)

- `[p]bible setkey <api_key>` - Set the API.Bible API key
- `[p]bible settings` - View current settings
- `[p]bible config <setting> <value>` - Configure settings

### Configuration Options

- `bible_id` - Set default Bible translation ID
- `max_verses` - Set maximum verses per page (1-20)
- `references` - Toggle reference display (true/false)
- `footnotes` - Toggle footnote display (true/false)

## Examples

```
[p]bible verse John 3:16
[p]bible verse Genesis 1:1
[p]bible verse Psalm 23:1-6
[p]bible chapter Matthew 5
[p]bible search love
[p]bible random
[p]bible config max_verses 15
[p]bible config references false
```

## Supported Book Names

The cog supports various book name formats:
- Full names: "Genesis", "Matthew", "Song of Solomon"
- Abbreviations: "Gen", "Matt", "SOS"
- Common variations: "1st John", "1 John", "1Jn"

## Requirements

- Red Discord Bot
- aiohttp (usually included with Red)
- Valid API.Bible API key

## Troubleshooting

- **"API key not set"**: Use `[p]bible setkey YOUR_KEY` to set your API key
- **"Verse not found"**: Check the reference format and book name
- **"Error fetching verse"**: Verify your API key is valid and has remaining requests

## Support

For issues with this cog, check:
1. Your API key is valid and set correctly
2. The reference format is correct
3. Your Red bot has internet access
4. The API.Bible service is operational

## License

This cog is provided as-is for use with Red Discord Bot.
