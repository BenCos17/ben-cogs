# Ports Cog Documentation

**Warning:** The `scanports` and `searchports` commands can be used to scan for open ports on a host, which may be against the terms of service of the host or even illegal in some jurisdictions. Use these commands responsibly and only with permission from the host. For more information on the legality of port scanning, please visit [this link](https://www.stationx.net/is-port-scanning-legal/).

## Commands

### `scanports`

Scans a range of ports on a host.

**Usage:** `!scanports <host> <start_port> <end_port>`

**Example:** `!scanports example.com 24 50`

**Arguments:**

* `<host>`: The hostname or IP address of the host to scan.
* `<start_port>`: The starting port of the range to scan.
* `<end_port>`: The ending port of the range to scan.

### `searchports`

Searches for open ports on a host.

**Usage:** `!searchports <host>`

**Example:** `!searchports example.com`

**Arguments:**

* `<host>`: The hostname or IP address of the host to search.

## Notes

* The `scanports` and `searchports` commands are rate-limited to 1 use per 5 seconds per user.
* The `scanports` and `searchports` commands can only be used by the bot owner.
* The `scanports` command scans a range of ports, while the `searchports` command scans all 65535 ports.

