# Bell Cog Documentation

## Overview

The `Bell` cog lets users ring a bell in the server, tracking how many times each user has rung the bell. Users can also reset their bell count (with confirmation).

## Commands

### 1. `[p]ringbell` or `[p]bell`
- **Description**: Ring the bell and increment your bell count in this server.
- **Usage**: `[p]ringbell`
- **Permissions**: None (must be used in a server, not DMs)
- **Example**: `[p]ringbell`

### 2. `[p]reset_bell` or `[p]resetbell`
- **Description**: Reset your bell count in this server after confirmation.
- **Usage**: `[p]reset_bell`
- **Permissions**: None (only resets your own count, must be used in a server)
- **Example**: `[p]reset_bell`

## Notes
- The bell count is tracked per user per server.
- A bell ringing GIF is sent with each ring.
- Commands must be used in a server (not in DMs).
