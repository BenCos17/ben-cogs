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
- **Permissions**: Requires Manage Server permission or admin.
- **Parameters**:
  - `<tag>`: The Amazon affiliate tag to be set for this server.

#### 1.2 `show_tag`
- **Usage**: `[p]amazon show_tag`
- **Description**: Shows the current Amazon affiliate tag for the server.
- **Permissions**: Requires Manage Server permission or admin.

#### 1.3 `current_tag`
- **Usage**: `[p]amazon current_tag`
- **Description**: Displays the current Amazon affiliate tag for the server.
- **Permissions**: Requires Manage Server permission or admin.

#### 1.4 `enable`
- **Usage**: `[p]amazon enable`
- **Description**: Enables Amazon affiliate link handling for the server.
- **Permissions**: Requires Manage Server permission or admin.

#### 1.5 `disable`
- **Usage**: `[p]amazon disable`
- **Description**: Disables Amazon affiliate link handling for the server.
- **Permissions**: Requires Manage Server permission or admin.

## Listener Overview

### `on_message`
- **Description**: Listens to messages across the server. If any Amazon product links are found, it converts them into affiliate links using the server's configured affiliate tag.
- **Note**: This listener only operates if the affiliate link handling is enabled for the server.

## Configuration Options

- `affiliate_tag`: The Amazon affiliate tag used for generating affiliate links.

## Examples

- Setting an affiliate tag: `[p]amazon set_tag yourtag-20`
- Showing the current tag: `[p]amazon show_tag`
- Displaying the current tag: `[p]amazon current_tag`
- Enabling affiliate link handling: `[p]amazon enable`
- Disabling affiliate link handling: `[p]amazon disable`
