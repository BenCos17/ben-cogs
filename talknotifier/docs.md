TalkNotifier Cog
Description

The TalkNotifier cog provides functionality for notifying specific users in a Discord server when they are mentioned by other users.
Commands

    setnotificationmessage
        Description: Sets the notification message format.
        Usage: [p]setnotificationmessage <message>
        Permissions Required: Manage Server

    addtargetuser
        Description: Adds a user to the list of users who will receive notifications.
        Usage: [p]addtargetuser <user>
        Permissions Required: Manage Server

    removetargetuser
        Description: Removes a user from the list of users who will receive notifications.
        Usage: [p]removetargetuser <user>
        Permissions Required: Manage Server

    setcooldown
        Description: Sets the cooldown period between notifications for each user.
        Usage: [p]setcooldown <cooldown>
        Permissions Required: Manage Server



Configuration Options

    notification_message
        Description: Defines the format of the notification message.
        Default Value: "{author} said: {content}"

    target_users
        Description: List of user IDs who will receive notifications.
        Default Value: []

    cooldown
        Description: Cooldown period in seconds between notifications for each user.
        Default Value: 10

