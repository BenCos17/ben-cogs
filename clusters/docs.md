# How to Use Clusters


## Getting Started



### First Time Setup

1\. **Load the cog** in your Red-DiscordBot instance

[p]repo add ben-cogs https://github.com/bencos17/ben-cogs

[p]cog install ben-cogs clusters

### Basic Commands

- `[p]clusters` - main cluster info command
- `[p]renamecluster ` - allows the bot owner to override the default cluster names
- `[p]clusters` now also includes host OS, CPU, RAM, swap, storage, and process stats

### API

The cog exposes a single web endpoint on port `8080`.

`GET http://<your-host>:8080/clusters`

### Response Shape

Top-level keys:

| Key | Description |
| --- | --- |
| `version` | API version for the payload |
| `bot_uptime` | Bot uptime as a formatted string |
| `server_uptime` | Host uptime as a formatted string |
| `system_stats` | Host and process statistics |
| `clusters` | Per-shard status information |

`system_stats` fields:

| Field | Description |
| --- | --- |
| `os` | Host OS name |
| `os_release` | OS release |
| `os_version` | OS version string |
| `platform` | Full platform string |
| `machine` | Machine architecture |
| `processor` | Processor string |
| `python_version` | Python runtime version |
| `cpu_logical` | Logical core count |
| `cpu_physical` | Physical core count when available |
| `cpu_count` | Best available core count |
| `cpu_affinity` | Cores available to the process when available |
| `cpu_usage_percent` | Total CPU usage percentage |
| `load_average` | Load average, when supported |
| `ram_used_gb` | Used RAM in GB |
| `ram_total_gb` | Total RAM in GB |
| `ram_percent` | RAM usage percentage |
| `swap_used_gb` | Used swap in GB |
| `swap_total_gb` | Total swap in GB |
| `swap_percent` | Swap usage percentage |
| `disk_used_gb` | Used disk space for the root path in GB |
| `disk_total_gb` | Total disk space for the root path in GB |
| `disk_percent` | Disk usage percentage for the root path |
| `process_rss_gb` | Bot process RSS memory in GB |
| `process_cpu_percent` | Bot process CPU usage percentage |
| `process_threads` | Number of bot process threads |
| `process_open_files` | Open files count, if available |

Each object in `clusters` includes:

| Field | Description |
| --- | --- |
| `shard_id` | Shard index |
| `name` | Cluster name |
| `servers` | Guild count on the shard |
| `users` | Total member count on the shard |
| `latency_ms` | Shard latency in milliseconds |
| `status` | `Online` or `Offline` |

```json
{
	"version": "1.0.0",
	"bot_uptime": "Unknown",
	"server_uptime": "12 weeks and 3 days and 5 hours ago",
	"system_stats": {
		"platform": "Windows-11-10.0.22631-SP0",
		"cpu_usage_percent": 18.2,
		"cpu_total_percent": 18.2,
		"cpu_physical": 8,
		"cpu_logical": 16,
		"ram_used_gb": 9.12,
		"ram_total_gb": 31.82,
		"swap_used_gb": 0.0,
		"swap_total_gb": 4.0,
		"process_rss_gb": 0.41,
		"bot_ram_gb": 0.41,
		"bot_ram_limit_gb": 10.0
	},
	"clusters": [
		{
			"shard_id": 0,
			"name": "IronMan",
			"servers": 42,
			"users": 1200,
			"latency_ms": 85,
			"status": "Online"
		}
	]
}
```

`system_stats` includes the host platform, CPU, memory, swap, disk, Python, and bot process metrics.



## Usage

\[p]clusters 
prints out the bots current clusters

the embed now also exposes system information like the host platform, CPU usage, RAM, swap, disk, and bot process stats

for example this is my current output on my bot

<img width="506" height="516" alt="image" src="https://github.com/user-attachments/assets/f44dd0d7-df98-410b-8b23-8a66f3d9cc7f" />







[p]renamecluster <shard\_id> <new\_name>





<shard\_id> is a number between 0 and your max amount of shards

<new\_name> what you want the cluster to be called from now on

this is how it's used 

<img width="391" height="120" alt="image" src="https://github.com/user-attachments/assets/43378549-920d-4443-8ea1-fb2ccd6430e0" />






