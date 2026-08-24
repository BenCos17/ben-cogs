\# 🛰️ J.A.R.V.I.S. ISS-Mimic Telemetry Suite



This documentation covers the setup, operation, and troubleshooting of the ISS Cog. This system bridges NASA's public Lightstreamer telemetry feed directly into your Discord server.



---



\## 🛠️ Core Commands



| Command | Usage | Description |

| :--- | :--- | :--- |

| `\*iss` | `\*iss` | \*\*Interactive Console\*\*: Opens a public dropdown menu to browse telemetry by category. |

| `\*iss all` | `\*iss all` | \*\*Master Snapshot\*\*: Sends two massive embeds containing every tracked sensor in the system. |

| `\*iss status` | `\*iss status` | \*\*Stream Health\*\*: Checks which sensors are currently broadcasting live data (updated in the last 60s). |

| `\*iss \[cat]` | `\*iss gnc` | \*\*Quick View\*\*: Direct access to specific categories (gnc, ethos, robotics, russian, etc.). |



---



\## 🚦 Understanding Sensor States



Because NASA uses \*\*MERGE\*\* mode for data transmission, sensors will show different states based on station activity:



\* \*\*🟢 Active (Green Circle)\*\*: Data has been received for this system within the last 60 seconds.

\* \*\*💤 Standby (Zzz Emoji)\*\*: The system is subscribed, but the value hasn't changed recently, so NASA isn't pushing updates.

\* \*\*🔹 Blue Diamond\*\*: Appears next to individual sensors that are currently streaming live data.

\* \*\*--- / Connecting\*\*: The bot is connected but waiting for the very first data packet to arrive for that specific ID.







---



\## 📂 Configuration (`telemetry.json`)



The Cog is entirely data-driven. To add or rename sensors, edit the `telemetry.json` file.



\*\*Format:\*\*

```json

"CATEGORY\_NAME": {

&nbsp;   "NASA\_OPCODE": "Display Label"

}

