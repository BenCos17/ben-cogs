# Contact Support

Contact is a Red Discord Bot cog for private support conversations between members and staff.

## Setup

1. Load the cog.
2. Configure the staff channel:

```text
[p]contactsetup #support
```

3. Post a user-facing support panel:

```text
[p]contactpanel #support
```

The panel includes a button that opens a DM with the bot. Staff need `Manage Server` to configure the cog and post the panel.

## Ticket IDs

Every ticket receives a unique ID containing the server ID and a per-server sequence number:

```text
833376882896142393-0001
```

The ID is shown to the member when the ticket is created and appears in the Discord thread name:

```text
ticket-833376882896142393-0001-username
```

A member may have multiple open tickets at the same time.

## Member Workflow

- Click **Open a Support Ticket** in the support panel, or DM the bot directly.
- Keep the ticket ID shown in the creation message.
- When multiple tickets are open, send the ticket ID to select which ticket receives future messages.
- Send another ticket ID at any time to switch the active ticket.
- Close a ticket with:

```text
[p]contactclose <ticket-id>
```

Only the member who owns the ticket can close it with this command.

## Staff Workflow

Staff need `Manage Messages` to use support conversation commands.

List open tickets:

```text
[p]support list
```

Open an additional ticket for a member:

```text
[p]support open @member Hello, how can we help?
```

Reply using a member mention:

```text
[p]support reply @member Your reply here
```

Reply to an exact ticket when the member has multiple tickets:

```text
[p]support reply <ticket-id> Your reply here
```

Close a ticket by member or exact ticket ID:

```text
[p]support close <ticket-id>
```

Closing a ticket creates an HTML transcript and sends it to the configured staff channel and the member who owns the ticket. Replies are delivered to the member and mirrored in the ticket thread. Successful staff replies receive a checkmark reaction when the bot has permission to add reactions.

## Web Dashboard

Install and load Red-Web-Dashboard and WTForms. The Contact page is available under the server's third-party dashboard pages.

The dashboard provides:

- Open and closed ticket counts.
- Ticket IDs and member identity.
- Latest message previews and full transcripts.
- Direct links to Discord ticket threads.
- CSRF-protected reply forms.
- Dashboard ticket replies sent directly to the member.
- Ticket closing controls.
- Separate open and closed ticket lists.
- HTML transcript delivery when a ticket is closed.
- Success notifications and a cleared reply field after sending.

Refresh the selected ticket page to see new messages.

## Permissions

- `Manage Server`: configure the staff channel and post the support panel.
- `Manage Messages`: use staff ticket commands.
- Bot permissions: view and send messages in the staff channel, create public threads, send DMs, and add reactions.

