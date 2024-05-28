# Amazon Affiliate Link Cog Commands

## Commands Overview

This cog includes several commands to manage Amazon affiliate settings for your server. Below are the commands and their usage:

### 1. `amazon`
- **Usage**: `[p]amazon`
- **Description**: Base command for Amazon affiliate settings. Use subcommands to manage settings.

### Subcommands

#### 1.1 `set_tag`
- **Usage**: `[p]amazon set_tag <tag>`
- **Description**: Sets the Amazon affiliate tag for the server.
- **Parameters**:
  - `<tag>`: The Amazon affiliate tag to be set for this server.

#### 1.2 `enable`
- **Usage**: `[p]amazon enable`
- **Description**: Enables Amazon affiliate link handling for the server.

#### 1.3 `disable`
- **Usage**: `[p]amazon disable`
- **Description**: Disables Amazon affiliate link handling for the server.

## Listener Overview

### `on_message`
- **Description**: Listens to messages across the server. If any Amazon product links are found, it converts them into affiliate links using the server's configured affiliate tag.
- **Note**: This listener only operates if the affiliate link handling is enabled for the server.

## Configuration Options

- `affiliate_tag`: The Amazon affiliate tag used for generating affiliate links.
- `enabled`: A boolean indicating whether the affiliate link handling is enabled or disabled for the server.

## Examples

- Setting an affiliate tag: `[p]amazon set_tag yourtag-20`
- Enabling affiliate link handling: `[p]amazon enable`
- Disabling affiliate link handling: `[p]amazon disable`

These commands manage the affiliate settings and ensure that any Amazon links sent in the server are automatically converted to affiliate links if enabled.
