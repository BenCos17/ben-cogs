import re
from typing import Optional, Union, List
import datetime
import discord

from redbot.core import commands, Config
from redbot.core.utils.chat_formatting import box


class Counter(commands.Cog):
    """Flexible counters: per-guild, per-user, and global."""

    def __init__(self, bot):
        self.bot = bot
        self.config = Config.get_conf(self, identifier=492089091320446976)
        # Guild counters now support multiple counters with unique IDs per guild.
        default_guild = {"counters": {}, "next_id": 1, "pending_owner_requests": {}, "next_req_id": 1}
        default_user = {"counters": {}}
        default_global = {"counters": {}}
        self.config.register_guild(**default_guild)
        self.config.register_user(**default_user)
        self.config.register_global(**default_global)

    @staticmethod
    def _clean_name(name: str) -> str:
        """Normalize counter names to lower-case with underscores for storage."""
        cleaned = re.sub(r"\s+", "_", name.strip().lower())
        # keep alnum and underscores and dashes
        cleaned = re.sub(r"[^a-z0-9_\-]", "", cleaned)
        return cleaned

    @staticmethod
    def _normalize_scope(raw: Optional[str]) -> str:
        if not raw:
            return "guild"
        raw = raw.lower()
        if raw in ("g", "guild", "server", "s"):
            return "guild"
        if raw in ("u", "user", "member"):
            return "user"
        if raw in ("global", "glo", "gl"):
            return "global"
        return raw

    async def _get_counter_store(self, ctx: commands.Context, scope: str):
        """Return (store_accessor, human_scope) where store_accessor is a context manager for modifying counters."""
        if scope == "guild":
            if ctx.guild is None:
                raise commands.BadArgument("Guild scope requires a server context.")
            return self.config.guild(ctx.guild), "guild"
        if scope == "user":
            return self.config.user(ctx.author), "user"
        return self.config, "global"

    async def _ensure_guild_schema(self, store) -> None:
        """Ensure guild store uses the id-based schema; migrate from name->int if needed."""
        data = await store.all()
        counters = data.get("counters", {})
        next_id = data.get("next_id")
        # If next_id missing, either new guild or legacy format; migrate if needed
        if next_id is None:
            # Legacy format: counters are name->int
            if counters and all(not isinstance(v, dict) for v in counters.values()):
                new = {}
                nid = 1
                for name, val in counters.items():
                    new[str(nid)] = {
                        "name": name,
                        "value": int(val),
                        "owner": None,
                        "creator": None,
                        "created_at": None,
                    }
                    nid += 1
                async with store.counters() as s:
                    s.clear()
                    s.update(new)
                await store.next_id.set(nid)
            else:
                # Fresh schema
                await store.next_id.set(1)

    async def _resolve_guild_counter(self, store, identifier: str):
        """Resolve an identifier (id or name) to a single (id, counter) tuple.

        Returns:
        - (id, counter) if unique match
        - None if none found
        - list of (id, counter) if multiple matches
        """
        counters = await store.counters()
        if not counters:
            return None
        if identifier.isdigit():
            cid = str(int(identifier))
            if cid in counters:
                return cid, counters[cid]
            return None
        name_key = self._clean_name(identifier)
        matches = [(cid, c) for cid, c in counters.items() if c.get("name") == name_key]
        if not matches:
            return None
        if len(matches) == 1:
            return matches[0]
        return matches

    async def _create_guild_counter(self, store, name_key: str, initial: int, owner_id: Optional[int], creator_id: int):
        """Create a guild counter and return (id, data)."""
        nid = await store.next_id()
        data = {
            "name": name_key,
            "value": int(initial),
            "owner": owner_id,
            "creator": creator_id,
            "created_at": datetime.datetime.utcnow().isoformat(),
        }
        async with store.counters() as counters:
            counters[str(nid)] = data
        await store.next_id.set(nid + 1)
        return str(nid), data

    async def _create_pending_request(self, store, name_key: str, initial: int, requester_id: int, owner_id: int, channel_id: int):
        """Create a pending owner-request and return its request id."""
        rid = await store.next_req_id()
        data = {
            "name": name_key,
            "initial": int(initial),
            "requester": requester_id,
            "owner": owner_id,
            "channel_id": channel_id,
            "requested_at": datetime.datetime.utcnow().isoformat(),
        }
        async with store.pending_owner_requests() as reqs:
            reqs[str(rid)] = data
        await store.next_req_id.set(rid + 1)
        return str(rid)


class OwnerApprovalView(discord.ui.View):
    def __init__(self, cog: "Counter", guild_id: int, req_id: str, request_data: dict, *, timeout: Optional[float] = 86400):
        super().__init__(timeout=timeout)
        self.cog = cog
        self.guild_id = guild_id
        self.req_id = req_id
        self.request_data = request_data

    async def _finalize(self, interaction: discord.Interaction, accepted: bool, message_text: str):
        # Attempt to remove pending request and notify requester
        guild = self.cog.bot.get_guild(self.guild_id)
        store = self.cog.config.guild(guild)
        async with store.pending_owner_requests() as reqs:
            if self.req_id in reqs:
                del reqs[self.req_id]
        # Disable buttons
        for item in self.children:
            try:
                item.disabled = True
            except Exception:
                pass
        try:
            await interaction.response.edit_message(content=message_text, view=self)
        except Exception:
            try:
                await interaction.response.send_message(message_text, ephemeral=True)
            except Exception:
                pass
        # Notify requester in the original channel if possible
        channel_id = self.request_data.get("channel_id")
        try:
            if channel_id is not None:
                channel = self.cog.bot.get_channel(int(channel_id))
                if channel is not None:
                    try:
                        await channel.send(f"<@{self.request_data.get('requester')}> Your owner request `{self.req_id}` for counter **{self.request_data.get('name')}** was {'accepted' if accepted else 'declined'}.")
                    except Exception:
                        pass
        except Exception:
            pass
        # Also DM the requester if possible
        requester_id = self.request_data.get("requester")
        try:
            requester = self.cog.bot.get_user(int(requester_id)) if requester_id is not None else None
        except Exception:
            requester = None
        if requester:
            try:
                await requester.send(f"Your owner request `{self.req_id}` for counter **{self.request_data.get('name')}** was {'accepted' if accepted else 'declined'}.")
            except Exception:
                pass

    @discord.ui.button(label="Accept", style=discord.ButtonStyle.green)
    async def accept(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != int(self.request_data.get("owner")):
            return await interaction.response.send_message("You are not the requested owner for this request.", ephemeral=True)
        # Create the counter
        guild = self.cog.bot.get_guild(self.guild_id)
        store = self.cog.config.guild(guild)
        name = str(self.request_data.get("name") or "")
        initial = int(self.request_data.get("initial") or 0)
        owner_id = int(self.request_data.get("owner"))
        requester_id = int(self.request_data.get("requester") or 0)
        nid, data = await self.cog._create_guild_counter(store, name, initial, owner_id, requester_id)
        await self._finalize(interaction, True, f"You accepted request `{self.req_id}` — created counter **{data['name']}** with id `{nid}` assigned to you.")

    @discord.ui.button(label="Decline", style=discord.ButtonStyle.red)
    async def decline(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != int(self.request_data.get("owner")):
            return await interaction.response.send_message("You are not the requested owner for this request.", ephemeral=True)
        await self._finalize(interaction, False, f"You declined owner request `{self.req_id}` for counter **{self.request_data.get('name')}**.")


    @commands.group(name="counter", invoke_without_command=True)
    async def counter(self, ctx: commands.Context) -> None:
        """Counter commands. Use subcommands like `create`, `inc`, `dec`, `set`, `delete`, `show`, `list`."""
        await ctx.send_help(ctx.command)

    @counter.command(name="create")
    async def create(self, ctx: commands.Context, name: str, scope: Optional[str] = None, initial: int = 0, owner: Optional[discord.Member] = None) -> None:
        """Create a counter. Scope: guild (default), user, global.

        Guild scope supports multiple counters with the same name; each counter receives a unique id.
        Optionally provide `owner` (mention or id) to associate the counter with a member.
        """
        scope = self._normalize_scope(scope)
        if scope == "global" and not await self.bot.is_owner(ctx.author):
            return await ctx.send("Global counters can only be created by the bot owner.")
        name_key = self._clean_name(name)
        store, human_scope = await self._get_counter_store(ctx, scope)
        if scope == "guild":
            await self._ensure_guild_schema(store)
            # if owner omitted or owner is the requester, create immediately
            if not owner or owner.id == ctx.author.id:
                nid, data = await self._create_guild_counter(store, name_key, initial, owner.id if owner else None, ctx.author.id)
                owner_text = f" (owner <@{data['owner']}>)" if data['owner'] else ""
                await ctx.send(f"Created counter **{name_key}** with id `{nid}` in {human_scope} scope{owner_text} with value `{initial}`.")
                return
            # Prevent duplicate pending requests for same name-owner
            existing = await store.pending_owner_requests()
            for k, v in existing.items():
                if v.get("name") == name_key and v.get("owner") == owner.id:
                    return await ctx.send(f"There is already a pending owner request `{k}` for **{name_key}** assigned to {owner.mention}.")
            # Create a pending owner request and notify the owner in the server channel (ping)
            rid = await self._create_pending_request(store, name_key, initial, ctx.author.id, owner.id, ctx.channel.id)
            owner_user = owner
            view = OwnerApprovalView(self, ctx.guild.id, rid, {
                "name": name_key,
                "initial": int(initial),
                "requester": ctx.author.id,
                "owner": owner.id,
                "channel_id": ctx.channel.id,
                "requested_at": datetime.datetime.utcnow().isoformat(),
            })
            try:
                await ctx.send(f"{owner_user.mention}, {ctx.author.mention} has requested you be the owner of counter **{name_key}** in this guild. You can Accept or Decline below.", view=view)
            except Exception:
                # If we can't send in the channel (rare), still register request but inform the requester
                await ctx.send(f"Owner request `{rid}` registered but I couldn't notify {owner_user.mention} in this channel. They will need to accept via `counter owner accept {rid}`.")
            else:
                await ctx.send(f"Owner request `{rid}` sent to {owner_user.mention} for counter **{name_key}** — waiting for their approval.")
            return
        # user/global legacy behavior
        async with store.counters() as counters:
            if name_key in counters:
                return await ctx.send(f"A counter named **{name_key}** already exists in {human_scope} scope.")
            counters[name_key] = int(initial)
        await ctx.send(f"Created counter **{name_key}** in {human_scope} scope with value `{initial}`.")

    @counter.command(name="inc")
    async def inc(self, ctx: commands.Context, name: str, amount: int = 1, scope: Optional[str] = None) -> None:
        """Increment a counter by amount (default 1)."""
        scope = self._normalize_scope(scope)
        store, human_scope = await self._get_counter_store(ctx, scope)
        if scope == "guild":
            await self._ensure_guild_schema(store)
            res = await self._resolve_guild_counter(store, name)
            if res is None:
                return await ctx.send(f"No counter named **{name}** found in {human_scope} scope.")
            if isinstance(res, list):
                lines = [f"`{cid}`: **{c.get('name')}** val={c.get('value')} owner={('<@%d>'%c['owner']) if c.get('owner') else 'none'}" for cid, c in res]
                return await ctx.send("Multiple counters match that name. Use the id to disambiguate:\n" + "\n".join(lines))
            cid, c = res
            async with store.counters() as counters:
                counters[cid]['value'] = int(counters[cid]['value']) + int(amount)
                new = counters[cid]['value']
            await ctx.send(f"**{c['name']}** (id `{cid}`) in {human_scope} is now `{new}` (+{amount}).")
            return
        # user/global legacy behavior
        name_key = self._clean_name(name)
        async with store.counters() as counters:
            if name_key not in counters:
                return await ctx.send(f"No counter named **{name_key}** found in {human_scope} scope.")
            counters[name_key] = int(counters[name_key]) + int(amount)
            new = counters[name_key]
        await ctx.send(f"**{name_key}** in {human_scope} is now `{new}` (+{amount}).")

    @counter.command(name="dec")
    async def dec(self, ctx: commands.Context, name: str, amount: int = 1, scope: Optional[str] = None) -> None:
        """Decrement a counter by amount (default 1)."""
        scope = self._normalize_scope(scope)
        store, human_scope = await self._get_counter_store(ctx, scope)
        if scope == "guild":
            await self._ensure_guild_schema(store)
            res = await self._resolve_guild_counter(store, name)
            if res is None:
                return await ctx.send(f"No counter named **{name}** found in {human_scope} scope.")
            if isinstance(res, list):
                lines = [f"`{cid}`: **{c.get('name')}** val={c.get('value')} owner={('<@%d>'%c['owner']) if c.get('owner') else 'none'}" for cid, c in res]
                return await ctx.send("Multiple counters match that name. Use the id to disambiguate:\n" + "\n".join(lines))
            cid, c = res
            async with store.counters() as counters:
                counters[cid]['value'] = int(counters[cid]['value']) - int(amount)
                new = counters[cid]['value']
            await ctx.send(f"**{c['name']}** (id `{cid}`) in {human_scope} is now `{new}` (-{amount}).")
            return
        # user/global legacy behavior
        name_key = self._clean_name(name)
        async with store.counters() as counters:
            if name_key not in counters:
                return await ctx.send(f"No counter named **{name_key}** found in {human_scope} scope.")
            counters[name_key] = int(counters[name_key]) - int(amount)
            new = counters[name_key]
        await ctx.send(f"**{name_key}** in {human_scope} is now `{new}` (-{amount}).")

    @counter.command(name="set")
    async def set_(self, ctx: commands.Context, name: str, value: int, scope: Optional[str] = None) -> None:
        """Set a counter to a specific integer value."""
        scope = self._normalize_scope(scope)
        if scope == "global" and not await self.bot.is_owner(ctx.author):
            return await ctx.send("Global counters can only be modified by the bot owner.")
        store, human_scope = await self._get_counter_store(ctx, scope)
        if scope == "guild":
            await self._ensure_guild_schema(store)
            res = await self._resolve_guild_counter(store, name)
            if res is None:
                return await ctx.send(f"No counter named **{name}** found in {human_scope} scope.")
            if isinstance(res, list):
                lines = [f"`{cid}`: **{c.get('name')}** val={c.get('value')} owner={('<@%d>'%c['owner']) if c.get('owner') else 'none'}" for cid, c in res]
                return await ctx.send("Multiple counters match that name. Use the id to disambiguate:\n" + "\n".join(lines))
            cid, c = res
            async with store.counters() as counters:
                counters[cid]['value'] = int(value)
            await ctx.send(f"Set **{c['name']}** (id `{cid}`) in {human_scope} to `{value}`.")
            return
        name_key = self._clean_name(name)
        async with store.counters() as counters:
            if name_key not in counters:
                return await ctx.send(f"No counter named **{name_key}** found in {human_scope} scope.")
            counters[name_key] = int(value)
        await ctx.send(f"Set **{name_key}** in {human_scope} to `{value}`.")

    @counter.command(name="delete")
    async def delete(self, ctx: commands.Context, name: str, scope: Optional[str] = None) -> None:
        """Delete a counter."""
        scope = self._normalize_scope(scope)
        if scope == "global" and not await self.bot.is_owner(ctx.author):
            return await ctx.send("Global counters can only be deleted by the bot owner.")
        store, human_scope = await self._get_counter_store(ctx, scope)
        if scope == "guild":
            await self._ensure_guild_schema(store)
            res = await self._resolve_guild_counter(store, name)
            if res is None:
                return await ctx.send(f"No counter named **{name}** found in {human_scope} scope.")
            if isinstance(res, list):
                lines = [f"`{cid}`: **{c.get('name')}** val={c.get('value')} owner={('<@%d>'%c['owner']) if c.get('owner') else 'none'}" for cid, c in res]
                return await ctx.send("Multiple counters match that name. Use the id to disambiguate:\n" + "\n".join(lines))
            cid, c = res
            async with store.counters() as counters:
                del counters[cid]
            await ctx.send(f"Deleted **{c['name']}** (id `{cid}`) from {human_scope} scope.")
            return
        name_key = self._clean_name(name)
        async with store.counters() as counters:
            if name_key not in counters:
                return await ctx.send(f"No counter named **{name_key}** found in {human_scope} scope.")
            del counters[name_key]
        await ctx.send(f"Deleted **{name_key}** from {human_scope} scope.")

    @counter.command(name="show")
    async def show(self, ctx: commands.Context, name: str, scope: Optional[str] = None) -> None:
        """Show the value of a counter."""
        scope = self._normalize_scope(scope)
        store, human_scope = await self._get_counter_store(ctx, scope)
        if scope == "guild":
            await self._ensure_guild_schema(store)
            res = await self._resolve_guild_counter(store, name)
            if res is None:
                return await ctx.send(f"No counter named **{name}** found in {human_scope} scope.")
            if isinstance(res, list):
                lines = [f"`{cid}`: **{c.get('name')}** val={c.get('value')} owner={('<@%d>'%c['owner']) if c.get('owner') else 'none'}" for cid, c in res]
                return await ctx.send("Multiple counters match that name. Use the id to disambiguate:\n" + "\n".join(lines))
            cid, c = res
            await ctx.send(f"**{c['name']}** (id `{cid}`) in {human_scope} is `{c['value']}`.")
            return
        name_key = self._clean_name(name)
        counters = await store.counters()
        if name_key not in counters:
            return await ctx.send(f"No counter named **{name_key}** found in {human_scope} scope.")
        await ctx.send(f"**{name_key}** in {human_scope} is `{counters[name_key]}`.")

    @counter.command(name="list")
    async def list_(self, ctx: commands.Context, scope: Optional[str] = None) -> None:
        """List counters in a scope (guild by default)."""
        scope = self._normalize_scope(scope)
        store, human_scope = await self._get_counter_store(ctx, scope)
        if scope == "guild":
            await self._ensure_guild_schema(store)
            counters = await store.counters()
            if not counters:
                return await ctx.send(f"No counters in {human_scope} scope.")
            lines = []
            for cid, c in sorted(counters.items(), key=lambda x: int(x[0])):
                owner = f"<@{c['owner']}" + ">" if c.get('owner') else "none"
                creator = f"<@{c['creator']}" + ">" if c.get('creator') else "unknown"
                created = c.get('created_at') or 'unknown'
                lines.append(f"`{cid}` **{c['name']}**: {c['value']} owner:{owner} creator:{creator} created:{created}")
            text = "\n".join(lines)
            await ctx.send(box(text, lang="ini"))
            return
        counters = await store.counters()
        if not counters:
            return await ctx.send(f"No counters in {human_scope} scope.")
        lines = [f"**{k}**: {v}" for k, v in sorted(counters.items())]
        text = "\n".join(lines)
        await ctx.send(box(text, lang="ini"))

    @counter.command(name="transfer")
    async def transfer(self, ctx: commands.Context, name: str, target_scope: str, scope: Optional[str] = None) -> None:
        """Transfer a counter from one scope to another (only bot owner for global target)."""
        scope = self._normalize_scope(scope)
        target_scope = self._normalize_scope(target_scope)
        src_store, src_human = await self._get_counter_store(ctx, scope)
        dst_store, dst_human = await self._get_counter_store(ctx, target_scope)
        if target_scope == "global" and not await self.bot.is_owner(ctx.author):
            return await ctx.send("You must be the bot owner to move counters to global scope.")
        # Guild source: resolve id/name
        if scope == "guild":
            await self._ensure_guild_schema(src_store)
            res = await self._resolve_guild_counter(src_store, name)
            if res is None:
                return await ctx.send(f"No counter named **{name}** in {src_human} scope.")
            if isinstance(res, list):
                lines = [f"`{cid}`: **{c.get('name')}** val={c.get('value')} owner={('<@%d>'%c['owner']) if c.get('owner') else 'none'}" for cid, c in res]
                return await ctx.send("Multiple counters match that name. Use the id to disambiguate:\n" + "\n".join(lines))
            cid, c = res
            value = c['value']
            async with src_store.counters() as src_counters:
                del src_counters[cid]
        else:
            name_key = self._clean_name(name)
            async with src_store.counters() as src_counters:
                if name_key not in src_counters:
                    return await ctx.send(f"No counter named **{name_key}** in {src_human} scope.")
                value = src_counters[name_key]
                del src_counters[name_key]
        # Destination: store value (convert guild->legacy formats)
        if target_scope == "guild":
            await self._ensure_guild_schema(dst_store)
            nid = await dst_store.next_id()
            data = {"name": self._clean_name(name), "value": int(value), "owner": None, "creator": ctx.author.id, "created_at": datetime.datetime.utcnow().isoformat()}
            async with dst_store.counters() as dst_counters:
                dst_counters[str(nid)] = data
            await dst_store.next_id.set(nid + 1)
            await ctx.send(f"Moved **{data['name']}** ({value}) from {src_human} to {dst_human} scope as id `{nid}`.")
            return
        async with dst_store.counters() as dst_counters:
            dst_counters[self._clean_name(name)] = int(value)
        await ctx.send(f"Moved **{self._clean_name(name)}** ({value}) from {src_human} to {dst_human} scope.")

    @counter.group(name="owner", invoke_without_command=True)
    async def owner_group(self, ctx: commands.Context) -> None:
        """Owner-related subcommands for pending owner requests (list/accept/decline)."""
        await ctx.send_help(ctx.command)

    @owner_group.command(name="list")
    async def owner_list(self, ctx: commands.Context) -> None:
        """List pending owner requests addressed to you in this guild."""
        if ctx.guild is None:
            return await ctx.send("This command must be used in a guild.")
        store = self.config.guild(ctx.guild)
        data = await store.pending_owner_requests()
        found = [(rid, r) for rid, r in data.items() if r.get("owner") == ctx.author.id]
        if not found:
            return await ctx.send("You have no pending owner requests in this guild.")
        lines = [f"`{rid}`: counter **{r.get('name')}** requested by <@{r.get('requester')}> at {r.get('requested_at')}" for rid, r in found]
        await ctx.send(box("\n".join(lines), lang="ini"))

    @owner_group.command(name="accept")
    async def owner_accept(self, ctx: commands.Context, request_id: str) -> None:
        """Accept a pending owner request by id."""
        if ctx.guild is None:
            return await ctx.send("This command must be used in a guild.")
        store = self.config.guild(ctx.guild)
        async with store.pending_owner_requests() as reqs:
            if request_id not in reqs:
                return await ctx.send("No such owner request id.")
            req = reqs[request_id]
            if req.get("owner") != ctx.author.id:
                return await ctx.send("You are not the requested owner for that request.")
            # create counter
            nid, data = await self._create_guild_counter(store, req.get("name"), req.get("initial"), req.get("owner"), req.get("requester"))
            del reqs[request_id]
        await ctx.send(f"Accepted owner request `{request_id}` — created counter **{data['name']}** with id `{nid}` and assigned to you.")

    @owner_group.command(name="decline")
    async def owner_decline(self, ctx: commands.Context, request_id: str) -> None:
        """Decline a pending owner request by id."""
        if ctx.guild is None:
            return await ctx.send("This command must be used in a guild.")
        store = self.config.guild(ctx.guild)
        async with store.pending_owner_requests() as reqs:
            if request_id not in reqs:
                return await ctx.send("No such owner request id.")
            req = reqs[request_id]
            if req.get("owner") != ctx.author.id:
                return await ctx.send("You are not the requested owner for that request.")
            del reqs[request_id]
        await ctx.send(f"Declined owner request `{request_id}`.")
