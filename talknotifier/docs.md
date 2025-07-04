# TalkNotifier Documentation

## Overview

The `TalkNotifier` cog provides notification-related commands for Discord servers. It can notify the server when specific users send messages, with customizable messages and cooldowns.

## Commands

### 1. `[p]talk setmessage <message>`
- **Description**: Set the notification message for the server.
- **Permissions**: Manage Server
- **Example**: `[p]talk setmessage {author} said: {content}`

### 2. `[p]talk showmessage`
- **Description**: Display the current notification message.
- **Permissions**: Manage Server
- **Example**: `[p]talk showmessage`

### 3. `[p]talk adduser <@user>`
- **Description**: Add a user to the target list for notifications.
- **Permissions**: Manage Server
- **Example**: `[p]talk adduser @username`

### 4. `[p]talk removeuser <@user>`
- **Description**: Remove a user from the target list for notifications.
- **Permissions**: Manage Server
- **Example**: `[p]talk removeuser @username`

### 5. `[p]talk clearusers`
- **Description**: Clear all target users from the notification list.
- **Permissions**: Manage Server
- **Example**: `[p]talk clearusers`

### 6. `[p]talk listusers`
- **Description**: List all users who are set to receive notifications.
- **Permissions**: Manage Server
- **Example**: `[p]talk listusers`

### 7. `[p]talk setcooldown <seconds>`
- **Description**: Set the cooldown period for notifications.
- **Permissions**: Manage Server
- **Example**: `[p]talk setcooldown 30`

## Notes
- Only users with Manage Server permissions can configure notification settings and users.
- The notification message can use `{author}` and `{content}` as placeholders.
- Cooldown prevents repeated notifications from the same user in a short period.

