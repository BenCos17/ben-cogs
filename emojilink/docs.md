markdown

# EmojiLink Cog

The `EmojiLink` cog provides commands to interact with emojis on Discord, including getting emoji links, listing emojis, getting information about specific emojis, and searching for emojis.

## Installation

To use this cog, you can easily install it using Red-DiscordBot's downloader. Here's how:

```python
[p]repo add EmojiLinkCog https://github.com/your-username/your-repo
[p]cog install EmojiLinkCog emojilink
[p]load emojilink

Replace [p] with your bot's prefix and https://github.com/your-username/your-repo with the URL of your GitHub repository where the cog file (emojilink.py) is located.
Commands
getemojilink

Get the link for a Discord emoji.

Parameters:

    emoji: The Discord emoji (custom emoji or Unicode emoji).

listemojis

List all custom emojis in the server along with their names and links.
emojiinfo

Get information about a specific custom emoji, including its name, ID, and creation date.

Parameters:

    emoji: The Discord emoji (custom emoji or Unicode emoji).

randomemoji

Get a link for a random custom emoji in the server.
emojisearch

Search for custom emojis based on their names or keywords.

Parameters:

    keyword: The search keyword.

Usage

Once the cog is installed and loaded, you can use the commands listed above to interact with emojis on your Discord server.
Example

python

[p]getemojilink :smile:
[p]listemojis
[p]emojiinfo :thumbsup:
[p]randomemoji
[p]emojisearch heart