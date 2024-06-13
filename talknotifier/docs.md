# TalkNotifier Documentation

The `TalkNotifier` cog provides notification-related commands for Discord servers.

## Commands

- `[p]talk setmessage`: Set the notification message for the server.
- `[p]talk showmessage`: Display the current notification message.
- `[p]talk adduser`: Add a user to the target list for notifications.
- `[p]talk removeuser`: Remove a user from the target list for notifications.
- `[p]talk clearusers`: Clear all target users from the notification list.
- `[p]talk listusers`: List all users who are set to receive notifications.
- `[p]talk setcooldown`: Set the cooldown period for notifications.

## Usage

To set the notification message:

1. Use the command `[p]talk setmessage` followed by the desired message enclosed in double quotes. For example:
   ```
   [p]talk setmessage "New notification message here"
   ```

2. To display the current notification message, use the command `[p]talk showmessage`. This will show the current message set for notifications.

3. Add a user to the notification target list by using the command `[p]talk adduser` followed by mentioning the user. For instance:
   ```
   [p]talk adduser @username
   ```

4. Remove a user from the notification target list with the command `[p]talk removeuser` followed by mentioning the user to be removed.

5. Clear all target users from the notification list using the command `[p]talk clearusers`.

6. To list all users set to receive notifications, utilize the command `[p]talk listusers`.

7. Set the cooldown period for notifications using the command `[p]talk setcooldown` followed by the desired cooldown time in seconds.

