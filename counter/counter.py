import re
from typing import Optional

from redbot.core import commands, Config
from redbot.core.utils.chat_formatting import box


class Counter(commands.Cog):
    """Flexible counters: per-guild, per-user, and global."""

    def __init__(self, bot):
        self.bot = bot
        # Unique identifier for Config. Large random-ish int to avoid collisions.
        self.config = Config.get_conf(self, identifier=987654321012345678)
        default_guild = {"counters": {}}
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

    @commands.group(name="counter", invoke_without_command=True)
    async def counter(self, ctx: commands.Context) -> None:
        """Counter commands. Use subcommands like `create`, `inc`, `dec`, `set`, `delete`, `show`, `list`."""
        await ctx.send_help(ctx.command)

    @counter.command(name="create")
    async def create(self, ctx: commands.Context, name: str, scope: Optional[str] = None, initial: int = 0) -> None:
        """Create a counter. Scope: guild (default), user, global."""
        scope = self._normalize_scope(scope)
        if scope == "global" and not await self.bot.is_owner(ctx.author):
            return await ctx.send("Global counters can only be created by the bot owner.")
        name_key = self._clean_name(name)
        store, human_scope = await self._get_counter_store(ctx, scope)
        async with store.counters() as counters:
            if name_key in counters:
                return await ctx.send(f"A counter named **{name_key}** already exists in {human_scope} scope.")
            counters[name_key] = int(initial)
        await ctx.send(f"Created counter **{name_key}** in {human_scope} scope with value `{initial}`.")

    @counter.command(name="inc")
    async def inc(self, ctx: commands.Context, name: str, amount: int = 1, scope: Optional[str] = None) -> None:
        """Increment a counter by amount (default 1)."""
        scope = self._normalize_scope(scope)
        name_key = self._clean_name(name)
        store, human_scope = await self._get_counter_store(ctx, scope)
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
        name_key = self._clean_name(name)
        store, human_scope = await self._get_counter_store(ctx, scope)
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
        name_key = self._clean_name(name)
        store, human_scope = await self._get_counter_store(ctx, scope)
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
        name_key = self._clean_name(name)
        store, human_scope = await self._get_counter_store(ctx, scope)
        async with store.counters() as counters:
            if name_key not in counters:
                return await ctx.send(f"No counter named **{name_key}** found in {human_scope} scope.")
            del counters[name_key]
        await ctx.send(f"Deleted **{name_key}** from {human_scope} scope.")

    @counter.command(name="show")
    async def show(self, ctx: commands.Context, name: str, scope: Optional[str] = None) -> None:
        """Show the value of a counter."""
        scope = self._normalize_scope(scope)
        name_key = self._clean_name(name)
        store, human_scope = await self._get_counter_store(ctx, scope)
        counters = await store.counters()
        if name_key not in counters:
            return await ctx.send(f"No counter named **{name_key}** found in {human_scope} scope.")
        await ctx.send(f"**{name_key}** in {human_scope} is `{counters[name_key]}`.")

    @counter.command(name="list")
    async def list_(self, ctx: commands.Context, scope: Optional[str] = None) -> None:
        """List counters in a scope (guild by default)."""
        scope = self._normalize_scope(scope)
        store, human_scope = await self._get_counter_store(ctx, scope)
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
        name_key = self._clean_name(name)
        src_store, src_human = await self._get_counter_store(ctx, scope)
        dst_store, dst_human = await self._get_counter_store(ctx, target_scope)
        if target_scope == "global" and not await self.bot.is_owner(ctx.author):
            return await ctx.send("You must be the bot owner to move counters to global scope.")
        async with src_store.counters() as src_counters:
            if name_key not in src_counters:
                return await ctx.send(f"No counter named **{name_key}** in {src_human} scope.")
            value = src_counters[name_key]
            del src_counters[name_key]
        async with dst_store.counters() as dst_counters:
            dst_counters[name_key] = value
        await ctx.send(f"Moved **{name_key}** ({value}) from {src_human} to {dst_human} scope.")
