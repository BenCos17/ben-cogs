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

1. **getlink**
   - Get the link for a Discord emoji.
   - **Parameters:**
     - `emoji`: The Discord emoji (custom emoji or Unicode emoji).

2. **list** (aliases: **all**)
   - List all custom emojis in the server along with their names and links.

3. **info**
   - Get information about a specific custom emoji, including its name, ID, and creation date.
   - **Parameters:**
     - `emoji`: The Discord emoji (custom emoji or Unicode emoji).

4. **random**
   - Get a link for a random custom emoji in the server.

5. **search**
   - Search for custom emojis based on their names or keywords.
   - **Parameters:**
     - `keyword`: The search keyword.

6. **add** (aliases: **create**)
   - Add a custom emoji to the server from a URL, attachment, or existing emoji.
   - **Parameters:**
     - `name`: The name for the new emoji (2-32 characters, alphanumeric + underscores only).
     - `source`: The source for the emoji (existing emoji, URL, or image attachment).
   - **Permissions:** Requires "Manage Emojis" permission.

7. **copy**
   - Copy a custom emoji from one server to another.
   - **Parameters:**
     - `emoji`: The custom emoji to copy.
   - **Permissions:** Requires "Manage Emojis" permission.

8. **delete**
   - Delete a custom emoji from the server.
   - **Parameters:**
     - `emoji`: The custom emoji to delete.
   - **Permissions:** Requires "Manage Emojis" permission.

9. **rename** (aliases: **edit**)
   - Rename a custom emoji in the server.
   - **Parameters:**
     - `emoji`: The custom emoji to rename.
     - `new_name`: The new name for the emoji.
   - **Permissions:** Requires "Manage Emojis" permission.

## Usage

Once the cog is installed and loaded, you can use the commands provided by the `EmojiLink` cog to interact with emojis on your Discord server.

## Examples

### Basic Usage
```
[p]getlink :smile:
[p]list
[p]info :thumbsup:
[p]random
[p]search heart
```

### Adding Emojis
```
[p]add myemoji :existing_emoji:     # Copy existing emoji
[p]add myemoji https://example.com/image.png  # From URL
[p]add myemoji                       # From attached image
```

### Managing Emojis
```
[p]copy :emoji_to_copy:
[p]delete :emoji_to_delete:
[p]rename :old_emoji: new_name
```

Replace `[p]` with your bot's prefix.
```
