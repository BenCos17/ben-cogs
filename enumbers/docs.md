# Enumbers Cog Documentation

A cog for looking up E-numbers (food additives) using the enumbers API.

## Features
- Look up information about food additives by their E-number code (e.g., E621, E100, E950).
- Provides details such as the additive's name, OpenFoodFacts links, and Wikidata references if available.

## Commands

### [p]enumber <code>
Look up an E-number (food additive) and get detailed information.

**Usage:**
```
[p]enumber <code>
```
- `<code>`: The E-number code to look up (e.g., E621, E100, E950). Case-insensitive, spaces are ignored.

**Example:**
```
[p]enumber E621
[p]enumber e100
[p]enumber   e950
```

**What it does:**
- Fetches data from the enumbers API.
- Searches for the specified E-number.
- If found, displays:
  - The E-number and its name
  - OpenFoodFacts link (if available)
  - Additive name and info link (if available)
  - Wikidata links (if available)
- If not found, notifies the user.
- Handles API errors gracefully.

## API Source
- [enumbers.jarvisdiscordbot.net](https://enumbers.jarvisdiscordbot.net/api/enumbers)

## Permissions
- The bot must be able to send messages and embeds in the channel where the command is used.