# EmojiLink Cog Documentation

## Overview

The `EmojiLink` cog provides commands to interact with emojis on Discord, including getting emoji links, listing emojis, getting information about specific emojis, and searching for emojis.

This cog is coded to be used with Discord bot using the Red-DiscordBot framework and running on the 3.5.x version of redbot.

## Installation

To use the `EmojiLink` cog, follow these steps:

1. Add the repository containing the cog to your Red-DiscordBot instance:
   
   ```
   [p]repo add ben-cogs https://github.com/BenCos17/ben-cogs/
   ```

   Replace `[p]` with your bot's prefix

2. Install the `EmojiLink` cog:

   ```
   [p]cog install ben-cogs emojilink
   ```

   Replace `[p]` with your bot's prefix  

3. Load the `EmojiLink` cog:

   ```
   [p]load emojilink
   ```

   Replace `[p]` with your bot's prefix.

## Commands

The `EmojiLink` cog provides the following commands:

1. **getemojilink**
   - Get the link for a Discord emoji.
   - **Parameters:**
     - `emoji`: The Discord emoji (custom emoji or Unicode emoji).

2. **listemojis**
   - List all custom emojis in the server along with their names and links.

3. **emojiinfo**
   - Get information about a specific custom emoji, including its name, ID, and creation date.
   - **Parameters:**
     - `emoji`: The Discord emoji (custom emoji or Unicode emoji).

4. **randomemoji**
   - Get a link for a random custom emoji in the server.

5. **emojisearch**
   - Search for custom emojis based on their names or keywords.
   - **Parameters:**
     - `keyword`: The search keyword.

## Usage

Once the cog is installed and loaded, you can use the commands provided by the `EmojiLink` cog to interact with emojis on your Discord server.

## Example

```
[p]getemojilink :smile:
[p]listemojis    (currently broken...)
[p]emojiinfo :thumbsup:
[p]randomemoji
[p]emojisearch heart
```
Replace `[p]` with your bot's prefix.
```
