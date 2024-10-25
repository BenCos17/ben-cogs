"""
Commands:

1. ringbell(ctx):
    - Aliases: ['bell']
    - Description: Rings a bell and increases the user's bell count in this server.
    - Parameters:
        - ctx: The context in which the command was invoked.
    - Behavior:
        - Retrieves the user's current bell count from the config.
        - Prepares a response message indicating the user's previous bell count if applicable.
        - Increments the user's bell count.
        - Updates the count for the user in the config.
        - Sends a message with the updated bell count.
        - Sends a bell ringing gif.

2. reset_bell(ctx):
    - Aliases: ['resetbell']
    - Description: Resets the user's bell count in this server after confirmation.
    - Parameters:
        - ctx: The context in which the command was invoked.
    - Behavior:
        - Asks the user for confirmation to reset their bell count.
        - Waits for the user's response (yes/no).
        - If the user confirms, resets the user's bell count in the config and sends a confirmation message.
        - If the user cancels or takes too long to respond, sends a cancellation message.
"""

