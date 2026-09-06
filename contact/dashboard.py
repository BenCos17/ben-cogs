import html
import typing

import discord
from redbot.core import commands


def dashboard_page(*args, **kwargs):
    """Mark a method as a page for the Red Dashboard cog."""
    def decorator(func):
        func.__dashboard_decorator_params__ = (args, kwargs)
        return func

    return decorator


class ContactDashboard:
    """Red Dashboard integration for the contact cog."""

    @staticmethod
    def _request_value(kwargs: dict, name: str) -> str:
        value = kwargs.get(name)
        if value is None:
            extra_kwargs = kwargs.get("extra_kwargs", {})
            value = extra_kwargs.get(name)
        if value is None:
            request_data = kwargs.get("data", {})
            form_data = request_data.get("form", {}) if isinstance(request_data, dict) else {}
            value = form_data.get(name)
        if value is None:
            value = ""
        if isinstance(value, (list, tuple)):
            value = value[-1] if value else ""
        return str(value)

    @staticmethod
    def _ticket_rows(guild: discord.Guild, tickets: dict) -> str:
        rows = []
        for ticket_id, ticket in tickets.items():
            if ticket.get("status") != "open":
                continue

            messages = ticket.get("messages", [])
            last_message = messages[-1] if messages else {}
            last_content = last_message.get("content") or "(attachment only)"
            last_author = last_message.get("author", "Unknown")
            user_id = ticket.get("user_id")
            member = guild.get_member(int(user_id)) if str(user_id).isdigit() else None
            user_label = member.display_name if member else f"User {user_id}"
            thread_id = ticket.get("thread_id")
            thread = guild.get_thread(thread_id) if isinstance(thread_id, int) else None
            thread_link = (
                f'<a aria-label="Open Discord thread for ticket {html.escape(str(ticket_id), quote=True)}" href="https://discord.com/channels/{guild.id}/{thread.id}">Open Discord thread</a>'
                if thread
                else '<span class="muted">Thread unavailable</span>'
            )
            reply_link = (
                f'<a class="button" aria-label="Reply to ticket {html.escape(str(ticket_id), quote=True)}" href="?ticket_id={html.escape(str(ticket_id), quote=True)}">Reply in dashboard</a>'
            )
            rows.append(
                "<tr>"
                f"<td><a href=\"?ticket_id={html.escape(str(ticket_id), quote=True)}\"><strong>{html.escape(user_label)}</strong></a><br>"
                f"<span class=\"muted\">Ticket {html.escape(str(ticket_id))}</span><br>"
                f"<span class=\"muted\">ID {html.escape(str(user_id))}</span><br>"
                f"<span class=\"muted\">{html.escape(str(len(messages)))} messages</span></td>"
                f"<td>{html.escape(last_author)}<br>{html.escape(last_content[:240])}</td>"
                f"<td>{html.escape(last_message.get('timestamp', 'Unknown'))}</td>"
                f"<td>{reply_link}<br>{thread_link}</td>"
                "</tr>"
            )
        return "".join(rows) or '<tr><td colspan="4" class="empty">No open conversations.</td></tr>'

    @staticmethod
    def _ticket_detail(
        guild: discord.Guild,
        ticket_id: str,
        ticket: dict,
        reply_form: object,
        close_form: object,
    ) -> str:
        entries = []
        for entry in ticket.get("messages", []):
            direction = "Staff" if entry.get("direction") == "staff" else "User"
            entries.append(
                f'<article class="message"><strong>{html.escape(direction)}: '
                f'{html.escape(entry.get("author", "Unknown"))}</strong>'
                f'<time>{html.escape(entry.get("timestamp", ""))}</time>'
                f'<p>{html.escape(entry.get("content", "(attachment only)"))}</p></article>'
            )
        transcript = "".join(entries) or '<p class="muted">No messages yet.</p>'
        latest = ticket.get("messages", [])[-1] if ticket.get("messages") else {}
        latest_content = latest.get("content") or "(attachment only)"
        user_id = ticket.get("user_id")
        user_id_text = str(user_id)
        member = guild.get_member(int(user_id_text)) if user_id_text.isdigit() else None
        member_name = member.display_name if member else f"User {user_id}"
        reply_form_html = str(reply_form) if reply_form is not None else (
            f'<p class="muted">Reply form unavailable. Use <code>support reply {html.escape(ticket_id)} &lt;message&gt;</code>.</p>'
        )
        close_form_html = str(close_form) if close_form is not None else ""
        return f"""
        <section class="ticket-detail">
            <h3>Ticket {html.escape(ticket_id)} <span class="muted">for {html.escape(member_name)} (ID {html.escape(str(user_id))})</span></h3>
            <div class="latest"><strong>Latest message</strong><time>{html.escape(latest.get("timestamp", ""))}</time><p>{html.escape(latest_content)}</p></div>
            <div class="messages">{transcript}</div>
            {reply_form_html}
            <div class="close-form">{close_form_html}</div>
        </section>
        """

    async def _register_dashboard(self, dashboard_cog: commands.Cog) -> None:
        rpc = getattr(dashboard_cog, "rpc", None)
        handler = getattr(rpc, "third_parties_handler", None)
        if handler is not None:
            handler.add_third_party(self)

    async def cog_load(self) -> None:
        dashboard_cog = self.bot.get_cog("Dashboard")
        if dashboard_cog is not None:
            await self._register_dashboard(dashboard_cog)

    @commands.Cog.listener()
    async def on_dashboard_cog_add(self, dashboard_cog: commands.Cog) -> None:
        await self._register_dashboard(dashboard_cog)

    @dashboard_page(
        name=None,
        description="Contact Support Dashboard",
        methods=("GET", "POST"),
        context_ids=["guild_id"],
    )
    async def dashboard_support(self, guild: discord.Guild, **kwargs) -> typing.Dict[str, typing.Any]:
        import wtforms
        from wtforms.validators import InputRequired, Length

        form_base = kwargs.get("Form")
        reply_form = None
        close_form = None
        if form_base is not None:
            class ReplyForm(form_base):
                ticket_id = wtforms.HiddenField()
                action = wtforms.HiddenField(default="reply")
                message = wtforms.TextAreaField(
                    "Reply to the member",
                    validators=[InputRequired(), Length(max=2000)],
                    render_kw={"rows": 4, "placeholder": "Write a reply..."},
                )
                submit = wtforms.SubmitField("Send reply to member")

            class CloseForm(form_base):
                ticket_id = wtforms.HiddenField()
                action = wtforms.HiddenField(default="close")
                submit = wtforms.SubmitField("Close ticket")

            reply_form = ReplyForm(prefix="contact_reply_")
            close_form = CloseForm(prefix="contact_close_")

        tickets = await self._migrate_tickets(guild)
        action = self._request_value(kwargs, "action")
        ticket_id = self._request_value(kwargs, "ticket_id")
        notice = ""
        message = self._request_value(kwargs, "message").strip()
        if reply_form is not None and reply_form.validate_on_submit():
            action = "reply"
            ticket_id = str(reply_form.ticket_id.data)
            message = str(reply_form.message.data).strip()
        elif close_form is not None and close_form.validate_on_submit():
            action = "close"
            ticket_id = str(close_form.ticket_id.data)
        if action == "reply" and ticket_id and message:
            try:
                success = await self._reply_to_ticket(
                    guild, ticket_id, "Dashboard staff", message
                )
                notice = "Reply sent." if success else "That ticket is no longer open."
            except (discord.Forbidden, discord.HTTPException):
                notice = "The reply could not be delivered to the user."
            tickets = await self._migrate_tickets(guild)
        elif action == "close" and ticket_id:
            closed = await self._close_ticket(guild, ticket_id)
            notice = "Ticket closed." if closed else "Ticket not found."
            tickets = await self._migrate_tickets(guild)
        open_tickets = [ticket for ticket in tickets.values() if ticket.get("status") == "open"]
        closed_tickets = [ticket for ticket in tickets.values() if ticket.get("status") == "closed"]
        configured_channel = await self.config.guild(guild).staff_channel()
        channel = guild.get_channel(configured_channel) if configured_channel else None
        channel_name = f"#{channel.name}" if channel else "Not configured"

        rows = self._ticket_rows(guild, tickets)
        selected_ticket = tickets.get(ticket_id)
        if reply_form is not None:
            reply_form.ticket_id.data = ticket_id
        if close_form is not None:
            close_form.ticket_id.data = ticket_id
        detail = (
            self._ticket_detail(guild, ticket_id, selected_ticket, reply_form, close_form)
            if selected_ticket
            else ""
        )
        page = f"""
        <style>
            .contact-dashboard {{ max-width: 1100px; padding: 24px; color: #e6e6e6; background: #1e1f22; }}
            .contact-dashboard h2, .contact-dashboard h3 {{ color: #ffffff; margin-top: 0; }}
            .contact-dashboard .stats {{ display: flex; gap: 12px; flex-wrap: wrap; margin: 20px 0; }}
            .contact-dashboard .stat {{ min-width: 150px; padding: 14px; background: #2b2d31; border: 1px solid #3f4147; border-radius: 6px; }}
            .contact-dashboard .stat strong {{ display: block; font-size: 24px; color: #ffffff; }}
            .contact-dashboard table {{ width: 100%; border-collapse: collapse; background: #2b2d31; }}
            .contact-dashboard th, .contact-dashboard td {{ padding: 12px; border-bottom: 1px solid #3f4147; text-align: left; vertical-align: top; }}
            .contact-dashboard th {{ color: #b5bac1; font-size: 12px; text-transform: uppercase; }}
            .contact-dashboard .muted {{ color: #b5bac1; font-size: 12px; }}
            .contact-dashboard .empty {{ padding: 24px; text-align: center; color: #b5bac1; }}
            .contact-dashboard .button {{ display: inline-block; margin-bottom: 6px; padding: 6px 10px; color: #ffffff; background: #5865f2; border-radius: 4px; text-decoration: none; }}
            .contact-dashboard code {{ color: #dbdee1; font-size: 11px; }}
            .contact-dashboard a {{ color: #8ea1e1; }}
            .contact-dashboard textarea {{ width: 100%; box-sizing: border-box; margin: 8px 0; padding: 10px; color: #ffffff; background: #1e1f22; border: 1px solid #4e5058; border-radius: 4px; resize: vertical; }}
            .contact-dashboard button {{ padding: 8px 14px; color: #ffffff; background: #5865f2; border: 0; border-radius: 4px; cursor: pointer; }}
            .contact-dashboard button.danger {{ background: #da373c; }}
            .contact-dashboard .ticket-detail {{ margin-top: 24px; padding: 16px; background: #2b2d31; border: 1px solid #3f4147; border-radius: 6px; }}
            .contact-dashboard .message {{ margin: 10px 0; padding: 10px; background: #1e1f22; border-left: 3px solid #5865f2; }}
            .contact-dashboard time {{ display: block; color: #b5bac1; font-size: 11px; }}
            .contact-dashboard .message p {{ white-space: pre-wrap; margin-bottom: 0; }}
            .contact-dashboard .latest {{ margin-bottom: 16px; padding: 12px; background: #313338; border: 1px solid #5865f2; border-radius: 4px; }}
            .contact-dashboard .latest p {{ white-space: pre-wrap; margin-bottom: 0; }}
            .contact-dashboard .close-form {{ display: inline-block; margin-top: 10px; }}
            @media (max-width: 700px) {{ .contact-dashboard {{ padding: 16px; }} .contact-dashboard table, .contact-dashboard thead, .contact-dashboard tbody, .contact-dashboard th, .contact-dashboard td, .contact-dashboard tr {{ display: block; }} .contact-dashboard thead {{ display: none; }} .contact-dashboard tr {{ padding: 12px 0; border-bottom: 1px solid #3f4147; }} .contact-dashboard td {{ border: 0; padding: 4px 0; }} }}
        </style>
        <section class="contact-dashboard">
            <h2>Contact Support</h2>
            <p>Staff inbox for <strong>{html.escape(guild.name)}</strong>. <a href="?ticket_id={html.escape(ticket_id, quote=True)}">Refresh latest messages</a></p>
            <div class="stats">
                <div class="stat"><strong>{len(open_tickets)}</strong>Open conversations</div>
                <div class="stat"><strong>{len(closed_tickets)}</strong>Closed conversations</div>
                <div class="stat"><strong>{html.escape(str(channel_name))}</strong>Staff channel</div>
            </div>
            <h3>Open conversations</h3>
            {f'<p class="notice">{html.escape(notice)}</p>' if notice else ''}
            <table>
                <thead><tr><th>User</th><th>Latest message</th><th>Last activity</th><th>Actions</th></tr></thead>
                <tbody>{rows}</tbody>
            </table>
            {detail}
        </section>
        """
        return {"status": 0, "web_content": {"source": page}}

    async def dashboard_embed(self, guild: discord.Guild) -> discord.Embed:
        tickets = await self.config.guild(guild).tickets()
        open_tickets = [ticket for ticket in tickets.values() if ticket.get("status") == "open"]
        configured = await self.config.guild(guild).staff_channel()

        embed = discord.Embed(title="Contact Dashboard", color=discord.Color.blurple())
        embed.add_field(name="Open conversations", value=str(len(open_tickets)), inline=True)
        embed.add_field(name="Configured channel", value="yes" if configured else "no")
        for ticket_id, ticket in list(tickets.items()):
            if ticket.get("status") != "open":
                continue
            messages = ticket.get("messages", [])
            latest = messages[-1].get("content") or "(attachment only)" if messages else "No messages yet"
            embed.add_field(
                name=f"Ticket {ticket_id} ({len(messages)} messages)",
                value=latest[:180],
                inline=False,
            )
            if len(embed.fields) >= 25:
                break
        return embed