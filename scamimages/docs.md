# ScamImages Redbot Cog

ScamImages checks image attachments against the Excessive Space scam image API. Servers are opted out by default.

## Install
[p]repo add ben-cogs https://github.com/bencos17/ben-cogs
[p]cog install ben-cogs scamimages
[p]load scamimages

The bot needs permission to read message history and attachments. If deletion is enabled, it also needs Manage Messages.

## Commands

- `[p]scamimages enable` opts the current server in.
- `[p]scamimages disable` opts the current server out.
- `[p]scamimages status` shows the current settings.
- `[p]scamimages threshold <1-10>` changes the minimum score; the default is `4`.
- `[p]scamimages delete true|false` controls whether detected messages are deleted; the default is `true`.
- `[p]scamimages timeout true|false` controls whether the posting user is timed out; the default is `true`.
- `[p]scamimages timeoutduration <seconds>` sets the timeout duration from 60 seconds to 28 days; the default is 3600 seconds.
- `[p]scamimages modlog true|false` controls whether detections create Redbot warning cases; the default is `true`.
- `[p]scamimages notify true|false` controls whether detections also post in the source channel; the default is `false`.
- `[p]scamimages useragent <value>` sets the API User-Agent; omit the value to reset it.
- `[p]scamimages hide #channel` hides a channel from detection.
- `[p]scamimages unhide #channel` restores detection in a hidden channel.
- `[p]scamimages hidden` lists hidden channels.

All commands require Manage Server or administrator permission.
