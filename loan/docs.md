# Bank Loan Cog

The Bank Loan cog provides commands for requesting, approving, and denying loans, as well as managing interest and loan settings.

## Getting Started

[p] is your bot prefix 
To use the Bank Loan cog, simply type `[p]loan` followed by the desired command.

## Commands

### User Commands

* `[p]loan request <amount>`: Request a loan from the bank.
* `[p]loan repay <amount>`: Repay a loan to the bank. If you try to repay more than you owe, only the remaining balance will be repaid and you will be notified.
* `[p]loan balance`: Show your current loan balance.
* `[p]loan interest`: Show the current interest rate and how much interest you owe (if you have a loan).

### Interest Application

* `[p]loan applyinterest`: Apply interest to all outstanding loans (admin only in guild mode, owner only in global mode). Interest is also applied automatically at the configured interval.

### Loan Listing

* `[p]loanset listloans`: List all users in this server with a loan balance (admin only, guild mode).
* `[p]loanowner listloans`: List all users globally with a loan balance (owner only, global mode).

### Approval and Denial

**Note:** If the bank is global, the ` [p]loanmod` commands are not available. Instead, use the ` [p]loanowner` commands.

#### Server Moderator Commands (Guild Mode Only)

* `[p]loanmod pending`: List all pending loan requests (with interactive approval/denial buttons).
* `[p]loanmod approve <user>`: Approve a user's pending loan request.
* `[p]loanmod deny <user>`: Deny a user's pending loan request.

#### Bot Owner Commands (Global Mode Only)

* `[p]loanowner pending`: List all pending owner loan requests (with interactive approval/denial buttons).
* `[p]loanowner approve <user>`: Approve a user's pending owner loan request.
* `[p]loanowner deny <user>`: Deny a user's pending owner loan request.

## Settings

### Guild Settings (Guild Mode Only)

* `[p]loanset requiremod true/false`: Set whether moderator approval is required for loans (true/false).
* `[p]loanset maxloan <amount>`: Set the maximum loan amount.
* `[p]loanset reviewchannel <#channel>`: Set the channel for pending loan review notifications (leave blank to disable).
* `[p]loanset interest <rate>`: Set the interest rate for loans (e.g., 0.05 for 5%).
* `[p]loanset interestinterval <interval>`: Set or show the interest interval (e.g., 12h, 2d, 24h). Leave blank to show current.
* `[p]loanset dmnotify true/false`: Enable or disable DM notifications for loan approval/denial.
* `[p]loanset listloans`: List all users in this server with a loan balance (admin only).

### Global Settings (Global Mode Only, Owner Only)

* `[p]loanowner setinterest <rate>`: Set the global interest rate (e.g., 0.05 for 5%).
* `[p]loanowner setinterestinterval <interval>`: Set or show the global interest interval (e.g., 12h, 2d, 24h). Leave blank to show current.
* `[p]loanowner setreviewchannel <#channel>`: Set the global review channel for owner loan requests (leave blank to disable).
* `[p]loanowner setdmnotify true/false`: Enable or disable global DM notifications for loan approval/denial.
* `[p]loanowner listloans`: List all users globally with a loan balance (owner only).

## Automatic Interest

Interest is applied automatically at the configured interval (default: every 24 hours). You can change the interval using the interval commands above. You can also apply interest manually at any time using `[p]loan applyinterest`.

## Notes

- The available commands and settings depend on whether the bank is in guild or global mode.
- All balances are integers (no decimals).
- If you try to repay more than you owe, only the remaining balance will be repaid and you will be notified.
- Review channels can be set for both guild and global loan requests for pending review notifications.
- DM notifications can be enabled to notify users when their loan is approved or denied.
- Only the bot owner can set the global review channel or global interest settings in global mode.
- Admins can set per-guild review channels and interest settings in guild mode.




