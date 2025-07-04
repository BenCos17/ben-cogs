# Spamatron Cog Documentation

## Overview

The `Spamatron` cog provides several features for Discord servers:
- **Spam command**: Allows administrators to spam a message in a specified channel a specified number of times (with confirmation).
- **Typo Watch**: Lets admins configure words to watch for common typos and respond with custom messages.
- **Ghostping**: Allows admins to ghostping a user in a channel a specified number of times at a set interval.

## Installation

To use the `Spamatron` cog, follow these steps:

1. Ensure you have Red-DiscordBot installed and running.
2. Add the `Spamatron` cog to your Red-DiscordBot instance:
   ```
   [p]repo add ben-cogs https://github.com/BenCos17/ben-cogs/
   [p]cog install ben-cogs spamatron
   ```

## Commands

### 1. `[p]spam <channel_mention> <amount> <message>`
- **Description**: Spam a message in a channel a specified number of times (requires confirmation).
- **Permissions**: Administrator
- **Example**: `[p]spam #general 10 Hello world!`

### 2. `[p]typowatch`
- **Description**: Configure typo watch settings for this server. Use subcommands to manage watched words and responses.
- **Permissions**: Administrator
- **Subcommands:**
  - `[p]typowatch add <correct_word> <typo_word> <response>`: Add a typo to watch for with a response.
    - Example: `[p]typowatch add available availible "Did you mean 'available'?"`
  - `[p]typowatch remove <correct_word>`: Remove a watched word.
  - `[p]typowatch responses <correct_word> <response1 | response2 | ...>`: Set custom responses for a word.
  - `[p]typowatch list [word]`: List all watched words or details about a specific word.
  - `[p]typowatch edit <word> <new_typo>`: Edit the typo for a watched word.
  - `[p]typowatch toggle`: Enable or disable typo watching.

### 3. `[p]ghostping <member> <channel> [amount] [interval]`
- **Description**: Ghostping a member in a specified channel a given number of times at a set interval.
- **Permissions**: Administrator
- **Example**: `[p]ghostping @user #general 5 2`

### 4. `[p]stopghostping`
- **Description**: Stop your currently running ghostping task.
- **Permissions**: Administrator

## Notes
- All commands require the user to have administrator permissions.
- This cog is designed for Red-DiscordBot version 3.x.
