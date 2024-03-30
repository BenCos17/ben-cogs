# Spamatron Cog Documentation

## Overview

The `Spamatron` cog provides a command to spam a message in a specified channel a specified number of times. This can be useful for testing or administrative purposes.

## Installation

To use the `Spamatron` cog, follow these steps:

1. Ensure you have Red-DiscordBot installed and running.

2. Add the `Spamatron` cog to your Red-DiscordBot instance.
   [p]repo add ben-cogs https://github.com/BenCos17/ben-cogs/
    [p]cog install ben-cogs spamatron

## Commands

The `Spamatron` cog provides the following command:

1. **spam**
   - Description: Spam a message in a channel a specified number of times.
   - Usage: `[p]spam <channel_mention> <amount> <message>`
     - Replace `[p]` with your bot's prefix.
     - `<channel_mention>`: Mention the channel where you want to spam the message.
     - `<amount>`: The number of times to spam the message (must be a positive integer).
     - `<message>`: The message to be spammed.
   - Example: `[p]spam #general 10 Hello world!`

## Implementation Details

The `Spamatron` cog allows users with administrator permissions to spam a message in a specified channel a specified number of times. Before sending the spam messages, it prompts the user for confirmation to prevent accidental spamming.

## Note

This cog is designed for Red-DiscordBot version 3.x.
