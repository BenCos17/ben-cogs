# Bank Loan Cog

The Bank Loan cog provides commands for requesting, approving, and denying loans.

## Getting Started

[p] is your bot prefix 
To use the Bank Loan cog, simply type `[p]loan` followed by the desired command.

## Commands

### Loan Management

* `[p]loan request <amount>`: Request a loan from the bank.
* `[p]loan repay <amount>`: Repay a loan to the bank.

### Approval and Denial

**Note:** If the bank is global, the ` [p]loanmod` commands are not available. Instead, use the ` [p]loanowner` commands.

#### Server Moderator Commands

* `[p]loanmod pending`: List all pending loan requests.
* `[p]loanmod approve <user>`: Approve a user's pending loan request.
* `[p]loanmod deny <user>`: Deny a user's pending loan request.

#### Bot Owner Commands

* `[p]loanowner pending`: List all pending owner loan requests.
* `[p]loanowner approve <user>`: Approve a user's pending owner loan request.
* `[p]loanowner deny <user>`: Deny a user's pending owner loan request.

## Settings

* `[p]loanset requiremod true/false`: Set whether moderator approval is required for loans (true/false).
* `[p]loanset maxloan <amount>`: Set the maximum loan amount.




