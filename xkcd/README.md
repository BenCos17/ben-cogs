# XKCD Cog for Red Discord Bot

A comprehensive XKCD comic lookup cog for Red Discord Bot that allows users to search, browse, and discover XKCD comics directly in Discord.

## Features

- **Comic Lookup**: Get specific comics by number
- **Random Comics**: Discover random XKCD comics
- **Latest Comic**: Always see the most recent XKCD comic
- **Search Functionality**: Search comics by title and alt text
- **Rich Embeds**: Beautiful Discord embeds with comic images and metadata
- **Interactive Menus**: Paginated results for multiple search results

## Commands

| Command | Description | Example |
|---------|-------------|---------|
| `[p]xkcd <number>` | Get a specific comic by number | `[p]xkcd 1337` |
| `[p]xkcd random` | Get a random comic | `[p]xkcd random` |
| `[p]xkcd latest` | Get the latest comic | `[p]xkcd latest` |
| `[p]xkcd <search terms>` | Search comics by title/alt text | `[p]xkcd python programming` |

## Installation

### Method 1: Manual Installation

1. Download the `xkcd.py` file
2. Place it in your Red Bot's `cogs` folder
3. Restart your bot or reload the cog with `[p]reload xkcd`

### Method 2: Using Red's Downloader (Recommended)

1. Add this repository to your bot's downloader:
   ```
   [p]repo add xkcd https://github.com/yourusername/xkcd-cog
   ```

2. Install the cog:
   ```
   [p]cog install xkcd
   ```

## Requirements

- Red Discord Bot v3.0+
- Python 3.8+
- `aiohttp` library (usually included with Red)

## Usage Examples

### Get a specific comic
```
[p]xkcd 1337
```
This will display XKCD comic #1337 with its image, title, alt text, and publication date.

### Get a random comic
```
[p]xkcd random
```
This will fetch and display a random XKCD comic from the entire collection.

### Get the latest comic
```
[p]xkcd latest
```
This will show the most recent XKCD comic published.

### Search for comics
```
[p]xkcd python
```
This will search through recent comics for any with "python" in the title or alt text.

## Features in Detail

### Comic Display
Each comic is displayed in a rich Discord embed containing:
- Comic number and title
- The comic image
- Alt text (hover text)
- Publication date
- Direct link to the comic on xkcd.com

### Search Algorithm
The search function:
- Searches through the last 100 comics for efficiency
- Matches against both comic titles and alt text
- Limits results to 10 comics to prevent spam
- Provides interactive pagination for multiple results

### Error Handling
The cog includes comprehensive error handling for:
- Network failures
- Invalid comic numbers
- Search queries with no results
- API rate limiting

## Configuration

This cog uses Red's configuration system but doesn't require any special setup. All settings are handled automatically.

## Troubleshooting

### Common Issues

1. **"Failed to fetch comic" error**
   - Check your internet connection
   - Verify xkcd.com is accessible
   - Try again later (the site might be temporarily down)

2. **Search not returning results**
   - Try different search terms
   - Search is limited to recent comics for performance
   - Use more specific terms

3. **Images not loading**
   - Check if your Discord server allows external images
   - Verify the bot has permission to embed links

### Performance Notes

- The search function is optimized to only search recent comics
- Random comic generation is fast and efficient
- All API calls use async/await for optimal performance

## Contributing

Feel free to submit issues, feature requests, or pull requests to improve this cog!

## License

This cog is open source and available under the MIT License.

## Support

If you need help with this cog:
1. Check the troubleshooting section above
2. Open an issue on the GitHub repository
3. Ask in the Red Discord Bot support server

---

**Enjoy discovering XKCD comics with your Discord community! 🎭**
