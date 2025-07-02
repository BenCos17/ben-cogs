# SCP Cog Documentation

## Overview
The SCP Cog is a Red DiscordBot extension that allows users to look up, search, and browse SCP Foundation articles directly from Discord. It provides detailed information, summaries, and interactive lists with pagination and buttons for easy navigation.

---

## Installation
1. Ensure you have [Red DiscordBot](https://docs.discord.red/en/stable/) installed and running.
2. Add this cog to your bot:
  
   ```
   [p] repo add ben-cogs https://github.com/bencos18/SCPLookup
   [p]cog install ben-cogs scp
   ```
   Replace `[p]` with your bot's prefix.

---

## Commands

### Main Command Group
- **`[p]scp`**
  - Shows help or usage info for the SCP cog.

#### Subcommands

- **`[p]scp lookup <scp-number> [search-term]`**
  - Looks up a specific SCP by number (e.g., `scp-173`) and provides a summary. Optionally, search for a term within the article's description.
  - Example: `[p]scp lookup scp-173` or `[p]scp lookup scp-173 statue`

- **`[p]scp list [category]`**
  - Lists SCP articles, optionally filtered by category/tag (e.g., `safe`, `keter`).
  - Results are paginated with interactive buttons if there are many entries.
  - Example: `[p]scp list` or `[p]scp list safe`

- **`[p]scp random`**
  - Fetches a random SCP article and displays its summary.
  - Example: `[p]scp random`

- **`[p]scp info <scp-number>`**
  - Provides detailed information about a specific SCP, including the full article (split into pages if needed).
  - Example: `[p]scp info 173`

- **`[p]scp search <search-term>`**
  - Searches for SCP articles by name or content. This command may take longer as it scrapes the SCP Wiki.
  - Example: `[p]scp search lizard`

---

## Features & Notes
- **Pagination:** Long lists are split into multiple pages. Use the ⬅️, ➡️, and 🛑 buttons to navigate or cancel.
- **Embeds:** SCP lists are shown in rich embeds with links, author, rating, tags, and series.
- **Data Source:** Uses the [SCP Data API](https://scp-data.tedivm.com/data/scp/items/index.json) for fast lookups.
- **Limitations:**
  - Descriptions are not shown in lists due to API limitations.
  - Some commands (like `scp search`) may be slow or break if the SCP Wiki structure changes.
  - Only the user who invoked the command can control pagination.

---

## Troubleshooting
- **Bot not responding?** Make sure the cog is loaded and you have the right permissions.
- **Pagination not working?** Ensure the bot has permission to use message components (buttons) and manage messages.
- **API errors?** The SCP Data API may be temporarily unavailable. Try again later.
- **Still having issues?** Check your bot logs for errors or ask for help (see below).

---

## Credits & Data Source
- Data provided by the [SCP Data API](https://scp-data.tedivm.com/data/scp/items/index.json)
- SCP Foundation content is licensed under [CC BY-SA 3.0](https://creativecommons.org/licenses/by-sa/3.0/)
- Cog by BenCos18 and contributors 

---

## Getting Help / Reporting Issues
- For help, open an issue on the repository where you got this cog, or join my discord server https://discord.gg/WW4eNQj9qr or ping me (bencos18) in the redbot cog support server in #other-cogs or just find me and I'll help 