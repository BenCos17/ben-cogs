# ScamImages Redbot Cog

ScamImages checks image attachments against the Excessive Space scam image API. Servers are opted out by default.

## Install

Copy this folder into a Redbot cog repository, load it, and install the cog in Redbot. The cog requires the `Pillow` and `ImageHash` Python packages; Redbot can install these from `info.json` when using the downloader.

The bot needs permission to read message history and attachments. If deletion is enabled, it also needs Manage Messages.

## Commands

- `[p]scamimages enable` opts the current server in.
- `[p]scamimages disable` opts the current server out.
- `[p]scamimages status` shows the current settings.
- `[p]scamimages threshold <1-10>` changes the minimum score; the default is `4`.
- `[p]scamimages delete true|false` controls whether detected messages are deleted; the default is `false`.

All commands require Manage Server or administrator permission.
