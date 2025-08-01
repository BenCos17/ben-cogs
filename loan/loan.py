import discord
from redbot.core import commands, Config, bank
from redbot.core.utils.chat_formatting import humanize_list
from datetime import datetime, timedelta
from redbot.core.bot import Red
from discord.ext import tasks


# Custom check to hide loanmod commands if bank is global
async def bank_not_global(ctx):
    return not await bank.is_global()

def loanmod_check():
    return commands.check(bank_not_global)

# Custom check to hide loanset commands if bank is global
loanset_check = loanmod_check  # Reuse the same check

# Custom check to hide loanowner commands if bank is not global
async def bank_is_global(ctx):
    return await bank.is_global()

def loanowner_check():
    return commands.check(bank_is_global)

class LoanApprovalView(discord.ui.View):
    def __init__(self, cog, ctx, request, is_owner):
        super().__init__(timeout=60)
        self.cog = cog
        self.ctx = ctx
        self.request = request
        self.is_owner = is_owner
        self.message = None

    @discord.ui.button(label="Approve", style=discord.ButtonStyle.green)
    async def approve(self, interaction: discord.Interaction, button: discord.ui.Button):
        try:
            # Defer the interaction first
            await interaction.response.defer()
            result = await self.cog.handle_approve(interaction, self.request, self.is_owner)
            if result:
                self.disable_all_items()
                await interaction.edit_original_response(view=self)
        except Exception:
            if not interaction.response.is_done():
                await interaction.response.defer(ephemeral=True)

    @discord.ui.button(label="Deny", style=discord.ButtonStyle.red)
    async def deny(self, interaction: discord.Interaction, button: discord.ui.Button):
        try:
            # Defer the interaction first
            await interaction.response.defer()
            result = await self.cog.handle_deny(interaction, self.request, self.is_owner)
            if result:
                self.disable_all_items()
                await interaction.edit_original_response(view=self)
        except Exception:
            if not interaction.response.is_done():
                await interaction.response.defer(ephemeral=True)

class LoanApprovalPaginator(discord.ui.View):
    def __init__(self, cog, ctx, requests, is_owner):
        super().__init__(timeout=120)
        self.cog = cog
        self.ctx = ctx
        self.requests = requests
        self.is_owner = is_owner
        self.index = 0
        self.message = None
        self.update_buttons()

    def update_buttons(self):
        self.clear_items()
        if self.index > 0:
            self.add_item(self.PrevButton(self))
        self.add_item(self.ApproveButton(self))
        self.add_item(self.DenyButton(self))
        if self.index < len(self.requests) - 1:
            self.add_item(self.NextButton(self))

    async def send(self):
        req = self.requests[self.index]
        embed = await self.cog.make_request_embed(self.ctx, req, self.is_owner)
        self.update_buttons()
        self.message = await self.ctx.send(embed=embed, view=self)

    async def update(self, interaction):
        req = self.requests[self.index]
        embed = await self.cog.make_request_embed(self.ctx, req, self.is_owner)
        self.update_buttons()
        await interaction.response.edit_message(embed=embed, view=self)
        # Optionally update self.message if needed
        if interaction.message:
            self.message = interaction.message

    class PrevButton(discord.ui.Button):
        def __init__(self, parent):
            super().__init__(style=discord.ButtonStyle.blurple, label="Previous")
            self.parent = parent
        async def callback(self, interaction: discord.Interaction):
            self.parent.index -= 1
            await self.parent.update(interaction)

    class NextButton(discord.ui.Button):
        def __init__(self, parent):
            super().__init__(style=discord.ButtonStyle.blurple, label="Next")
            self.parent = parent
        async def callback(self, interaction: discord.Interaction):
            self.parent.index += 1
            await self.parent.update(interaction)

    class ApproveButton(discord.ui.Button):
        def __init__(self, parent):
            super().__init__(style=discord.ButtonStyle.green, label="Approve")
            self.parent = parent
        async def callback(self, interaction: discord.Interaction):
            try:
                # Defer the interaction first
                await interaction.response.defer()
                req = self.parent.requests[self.parent.index]
                result = await self.parent.cog.handle_approve(interaction, req, self.parent.is_owner)
                if result:
                    self.parent.parent.disable_all_items()
                    await interaction.edit_original_response(view=self.parent)
            except Exception:
                if not interaction.response.is_done():
                    await interaction.response.defer(ephemeral=True)

    class DenyButton(discord.ui.Button):
        def __init__(self, parent):
            super().__init__(style=discord.ButtonStyle.red, label="Deny")
            self.parent = parent
        async def callback(self, interaction: discord.Interaction):
            try:
                # Defer the interaction first
                await interaction.response.defer()
                req = self.parent.requests[self.parent.index]
                result = await self.parent.cog.handle_deny(interaction, req, self.parent.is_owner)
                if result:
                    self.parent.parent.disable_all_items()
                    await interaction.edit_original_response(view=self.parent)
            except Exception:
                if not interaction.response.is_done():
                    await interaction.response.defer(ephemeral=True)

class BankLoan(commands.Cog):
    def __init__(self, bot):
        """
        Initialize the BankLoan cog with configuration.
        
        Config structure:
        - Guild: per-server settings (max loan, interest rate, review channel, etc.)
        - Global: bot-wide settings (owner approval queue, global interest, review channel)
        - User: individual loan amounts
        """
        self.bot = bot
        self.config = Config.get_conf(self, identifier=492089091320446976)
        default_guild = {
            "require_mod_approval": False,
            "max_loan": 1000,
            "pending_loans": [],  
            "review_channel": None,  # Channel ID for pending review
            "interest_rate": 0.05,  # Default 5% interest
            "interest_interval": "24h",  # Default 24 hours
            "last_interest": None,
            "dm_notify": False  # DM user on approval/denial
        }
        default_global = {
            "pending_owner_loans": [],  
            "interest_rate": 0.05,  # Default 5% interest (global)
            "interest_interval": "24h",  # Default 24 hours (global)
            "last_interest": None,
            "review_channel": None,  # Global review channel
            "dm_notify": False  # DM user on approval/denial (global)
        }
        default_user = {
            "loan_amount": 0
        }
        self.config.register_guild(**default_guild)
        self.config.register_global(**default_global)
        self.config.register_user(**default_user)

    def cog_load(self):
        """Start the background interest task when the cog loads."""
        self.interest_task.start()

    def cog_unload(self):
        """Cancel the background interest task when the cog unloads."""
        self.interest_task.cancel()

    @tasks.loop(minutes=10)
    async def interest_task(self):
        """
        Background task that runs every 10 minutes to check if interest should be applied.
        
        For global mode: applies interest to all users across all guilds
        For guild mode: applies interest to users in each guild individually
        
        The task checks the configured interval and last application time to determine
        if enough time has passed to apply interest again.
        """
        await self.bot.wait_until_red_ready()
        is_global = await bank.is_global()
        now = datetime.utcnow()
        if is_global:
            # Global mode: apply interest to all users across all guilds
            interval_str = await self.config.interest_interval()
            last_applied = await self.config.last_interest()
            interval = self.parse_interval(interval_str)
            if not interval:
                return
            if last_applied:
                last_applied_dt = datetime.fromisoformat(last_applied)
                if now < last_applied_dt + interval:
                    return  # Not enough time has passed
            # Apply global interest
            ctx = None  # No context for background
            await self.apply_interest_global()
            await self.config.last_interest.set(now.isoformat())
        else:
            # Guild mode: apply interest to users in each guild individually
            for guild in self.bot.guilds:
                interval_str = await self.config.guild(guild).interest_interval()
                last_applied = await self.config.guild(guild).last_interest()
                interval = self.parse_interval(interval_str)
                if not interval:
                    continue
                if last_applied:
                    last_applied_dt = datetime.fromisoformat(last_applied)
                    if now < last_applied_dt + interval:
                        continue  # Not enough time has passed for this guild
                await self.apply_interest_guild(guild)
                await self.config.guild(guild).last_interest.set(now.isoformat())

    @staticmethod
    def parse_interval(interval_str):
        """
        Parses a string representation of a time interval and convert it to a timedelta object.
        
        Supports formats:
        - "24h" for hours (e.g., "12h", "0.5h")
        - "2d" for days (e.g., "1d", "0.5d") 
        - "24" for hours (fallback, assumes hours if no suffix)
        
        Args:
            interval_str (str): The interval string to parse
            
        Returns:
            timedelta or None: The parsed interval, or None if invalid
        """
        if not interval_str:
            return None
        interval_str = interval_str.strip().lower()
        if interval_str.endswith("h"):
            try:
                hours = float(interval_str[:-1])
                return timedelta(hours=hours)
            except Exception:
                return None
        if interval_str.endswith("d"):
            try:
                days = float(interval_str[:-1])
                return timedelta(days=days)
            except Exception:
                return None
        try:
            # fallback: treat as hours
            hours = float(interval_str)
            return timedelta(hours=hours)
        except Exception:
            return None

    async def apply_interest_guild(self, guild):
        """
        Apply interest to all users with loans in a specific guild.
        
        Args:
            guild: The Discord guild to apply interest to
        """
        rate = await self.config.guild(guild).interest_rate()
        members = guild.members
        for member in members:
            loan_amount = await self.config.user(member).loan_amount()
            if loan_amount and loan_amount > 0:
                new_amount = int(loan_amount * (1 + rate))
                await self.config.user(member).loan_amount.set(new_amount)

    async def apply_interest_global(self):
        """
        Apply interest to all users with loans across all guilds (global mode).
        """
        rate = await self.config.interest_rate()
        for user_id in (await self.config.all_users()).keys():
            user = self.bot.get_user(int(user_id))
            if not user:
                continue
            loan_amount = await self.config.user(user).loan_amount()
            if loan_amount and loan_amount > 0:
                new_amount = int(loan_amount * (1 + rate))
                await self.config.user(user).loan_amount.set(new_amount)

    @commands.group()
    async def loan(self, ctx):
        """Bank loan commands"""

    @loan.command()
    async def request(self, ctx, amount: int):
        """
        Request a loan from the bank.
        
        Flow:
        1. Check if user already has a loan
        2. Check if amount exceeds max loan
        3. If global bank: add to owner approval queue
        4. If guild bank: check if mod approval required
        5. Send notifications to review channels if configured
        6. DM user if enabled and loan is auto-approved
        """
        user = ctx.author
        guild = ctx.guild
        has_loan = await self.config.user(user).loan_amount()
        if has_loan:
            await ctx.send("You already have an outstanding loan. Please repay it first.")
            return
        max_loan = await self.config.guild(guild).max_loan()
        if amount > max_loan:
            await ctx.send(f"The maximum loan amount is {max_loan}.")
            return
        is_global = await bank.is_global()
        now = datetime.utcnow().isoformat()
        if is_global:
            # Owner approval required for global bank mode
            pending = await self.config.pending_owner_loans()
            for req in pending:
                if req["user_id"] == user.id:
                    await ctx.send("You already have a pending loan request.")
                    return
            pending.append({"user_id": user.id, "amount": amount, "date": now})
            await self.config.pending_owner_loans.set(pending)
            await ctx.send(f"Loan request for {amount} submitted and is pending bot owner approval.")
            # Send to global review channel if set
            global_review_channel_id = await self.config.review_channel()
            if global_review_channel_id:
                for guild in self.bot.guilds:
                    channel = guild.get_channel(global_review_channel_id)
                    if channel:
                        embed = await self.make_request_embed(ctx, {"user_id": user.id, "amount": amount, "date": now}, is_owner=True)
                        view = LoanApprovalView(self, ctx, {"user_id": user.id, "amount": amount, "date": now}, is_owner=True)
                        try:
                            await channel.send(embed=embed, view=view)
                        except Exception:
                            pass
            # Also send to per-guild review channels if set (legacy support)
            for guild in self.bot.guilds:
                review_channel_id = await self.config.guild(guild).review_channel()
                if review_channel_id:
                    channel = guild.get_channel(review_channel_id)
                    if channel:
                        embed = await self.make_request_embed(ctx, {"user_id": user.id, "amount": amount, "date": now}, is_owner=True)
                        view = LoanApprovalView(self, ctx, {"user_id": user.id, "amount": amount, "date": now}, is_owner=True)
                        try:
                            await channel.send(embed=embed, view=view)
                        except Exception:
                            pass
            return
        require_mod = await self.config.guild(guild).require_mod_approval()
        if require_mod:
            # Add to pending queue for moderator approval
            pending = await self.config.guild(guild).pending_loans()
            for req in pending:
                if req["user_id"] == user.id:
                    await ctx.send("You already have a pending loan request.")
                    return
            pending.append({"user_id": user.id, "amount": amount, "date": now})
            await self.config.guild(guild).pending_loans.set(pending)
            await ctx.send(f"Loan request for {amount} submitted and is pending moderator approval.")
            # Send to review channel if set (guild mode)
            review_channel_id = await self.config.guild(guild).review_channel()
            if review_channel_id:
                channel = guild.get_channel(review_channel_id)
                if channel:
                    embed = await self.make_request_embed(ctx, {"user_id": user.id, "amount": amount, "date": now}, is_owner=False)
                    view = LoanApprovalView(self, ctx, {"user_id": user.id, "amount": amount, "date": now}, is_owner=False)
                    try:
                        await channel.send(embed=embed, view=view)
                    except Exception:
                        pass
        else:
            # Auto-approve the loan (no approval required)
            await bank.deposit_credits(user, amount)
            await self.config.user(user).loan_amount.set(amount)
            await ctx.send(f"Loan request for {amount} submitted and credited to your account.")

    @loan.command()
    async def repay(self, ctx, amount: int):
        """Repay a loan to the bank"""
        user = ctx.author
        if amount <= 0:
            await ctx.send("You must repay a positive amount.")
            return
        loan_amount = await self.config.user(user).loan_amount()
        if not loan_amount or loan_amount <= 0:
            await ctx.send("You do not have any outstanding loans.")
            return
        overpay = False
        if amount > loan_amount:
            amount = loan_amount
            overpay = True
        if not await bank.can_spend(user, amount):
            await ctx.send("You do not have enough funds to repay this amount.")
            return
        await bank.withdraw_credits(user, amount)
        await self.config.user(user).loan_amount.set(loan_amount - amount)
        if loan_amount - amount <= 0:
            if overpay:
                await ctx.send(f"You only owed {loan_amount}, so only {loan_amount} was repaid. You have fully repaid your loan!")
            else:
                await ctx.send(f"You have fully repaid your loan!")
        else:
            if overpay:
                await ctx.send(f"You only owed {loan_amount}, so only {loan_amount} was repaid. Remaining loan: {loan_amount - amount}")
            else:
                await ctx.send(f"Loan repayment of {amount} submitted. Remaining loan: {loan_amount - amount}")

    @commands.group()
    @commands.admin_or_permissions(manage_guild=True)
    @loanset_check()
    async def loanset(self, ctx):
        """Loan settings (admin only)"""

    @loanset.command()
    async def requiremod(self, ctx, value: bool):
        """Require moderator approval for loans (True/False)"""
        await self.config.guild(ctx.guild).require_mod_approval.set(value)
        await ctx.send(f"Moderator approval for loans set to {value}.")

    @loanset.command()
    async def maxloan(self, ctx, amount: int):
        """Set the maximum loan amount"""
        await self.config.guild(ctx.guild).max_loan.set(amount)
        await ctx.send(f"Maximum loan amount set to {amount}.")

    @loanset.command()
    async def reviewchannel(self, ctx, channel: discord.TextChannel = None):
        """Set the channel for pending loan review (leave blank to disable)"""
        current = await self.config.guild(ctx.guild).review_channel()
        if channel:
            if current == channel.id:
                await ctx.send(f"Review channel is already set to {channel.mention}.")
                return
        else:
            if current is None:
                await ctx.send("Review channel notifications are already disabled.")
                return
        await self.config.guild(ctx.guild).review_channel.set(channel.id if channel else None)
        if channel:
            await ctx.send(f"Review channel set to {channel.mention}.")
        else:
            await ctx.send("Review channel notifications disabled.")

    @loanset.command()
    async def interest(self, ctx, rate: float):
        """Set the interest rate for loans (e.g., 0.05 for 5%) (guild only)"""
        is_global = await bank.is_global()
        if is_global:
            await ctx.send("The bank is global. Use [p]loanowner setinterest to set the global interest rate.")
            return
        if rate < 0:
            await ctx.send("Interest rate must be non-negative.")
            return
        await self.config.guild(ctx.guild).interest_rate.set(rate)
        await ctx.send(f"Interest rate set to {rate * 100:.2f}% for this server.")

    @loanset.command()
    async def dmnotify(self, ctx, value: bool):
        """Enable or disable DM notifications for loan approval/denial (guild only)"""
        await self.config.guild(ctx.guild).dm_notify.set(value)
        await ctx.send(f"DM notifications for loan approval/denial set to {value}.")

    @commands.group()
    @commands.mod_or_permissions(manage_guild=True)
    @loanmod_check()
    async def loanmod(self, ctx):
        """Moderator loan approval commands"""

    @loanmod.command(name="pending")
    async def loanmod_pending(self, ctx):
        """List all pending loan requests with details and buttons (paginated)"""
        pending = await self.config.guild(ctx.guild).pending_loans()
        if not pending:
            await ctx.send("There are no pending loan requests.")
            return
        paginator = LoanApprovalPaginator(self, ctx, pending, is_owner=False)
        await paginator.send()

    async def handle_approve(self, interaction, request, is_owner):
        """
        Handle loan approval from button interaction.
        
        Args:
            interaction: Discord interaction object
            request: The loan request data containing user_id and amount
            is_owner: Whether this is owner approval (global) or mod approval (guild)
        
        Returns:
            bool: True if successful, False if error occurred
        """
        if is_owner:
            pending = await self.config.pending_owner_loans()
            user = self.bot.get_user(request["user_id"])
            dm_notify = await self.config.dm_notify()
        else:
            pending = await self.config.guild(interaction.guild).pending_loans()
            user = interaction.guild.get_member(request["user_id"])
            dm_notify = await self.config.guild(interaction.guild).dm_notify()
        if not user:
            await interaction.followup.send("User not found.", ephemeral=True)
            return False
        if request not in pending:
            await interaction.followup.send("Request no longer pending.", ephemeral=True)
            return False
        # Approve the loan: credit the user and set their loan amount
        await bank.deposit_credits(user, request["amount"])
        await self.config.user(user).loan_amount.set(request["amount"])
        pending.remove(request)
        if is_owner:
            await self.config.pending_owner_loans.set(pending)
        else:
            await self.config.guild(interaction.guild).pending_loans.set(pending)
        # Send confirmation message in the channel
        await interaction.followup.send(f"✅ Loan request for {user.display_name} ({request['amount']}) has been approved.")
        # DM notify if enabled
        if dm_notify:
            try:
                await user.send(f"Your loan request for {request['amount']} has been approved.")
            except Exception:
                pass
        return True

    async def handle_deny(self, interaction, request, is_owner):
        """
        Handle loan denial from button interaction.
        
        Args:
            interaction: Discord interaction object
            request: The loan request data containing user_id and amount
            is_owner: Whether this is owner denial (global) or mod denial (guild)
        
        Returns:
            bool: True if successful, False if error occurred
        """
        if is_owner:
            pending = await self.config.pending_owner_loans()
            user = self.bot.get_user(request["user_id"])
            dm_notify = await self.config.dm_notify()
        else:
            pending = await self.config.guild(interaction.guild).pending_loans()
            user = interaction.guild.get_member(request["user_id"])
            dm_notify = await self.config.guild(interaction.guild).dm_notify()
        if not user:
            await interaction.followup.send("User not found.", ephemeral=True)
            return False
        if request not in pending:
            await interaction.followup.send("Request no longer pending.", ephemeral=True)
            return False
        # Deny the loan: remove from pending queue
        pending.remove(request)
        if is_owner:
            await self.config.pending_owner_loans.set(pending)
        else:
            await self.config.guild(interaction.guild).pending_loans.set(pending)
        # Send confirmation message in the channel
        await interaction.followup.send(f"❌ Loan request for {user.display_name} ({request['amount']}) has been denied.")
        # DM notify if enabled
        if dm_notify:
            try:
                await user.send(f"Your loan request for {request['amount']} has been denied.")
            except Exception:
                pass
        return True

    @loanmod.command(name="approve")
    async def loanmod_approve(self, ctx, member: discord.Member):
        """Approve a user's pending loan request (manual fallback)"""
        pending = await self.config.guild(ctx.guild).pending_loans()
        for req in pending:
            if req["user_id"] == member.id:
                await bank.deposit_credits(member, req["amount"])
                await self.config.user(member).loan_amount.set(req["amount"])
                pending.remove(req)
                await self.config.guild(ctx.guild).pending_loans.set(pending)
                await ctx.send(f"Approved and credited {req['amount']} to {member.display_name}.")
                return
        await ctx.send("No pending loan request for that user.")

    @loanmod.command(name="deny")
    async def loanmod_deny(self, ctx, member: discord.Member):
        """Deny a user's pending loan request (manual fallback)"""
        pending = await self.config.guild(ctx.guild).pending_loans()
        for req in pending:
            if req["user_id"] == member.id:
                pending.remove(req)
                await self.config.guild(ctx.guild).pending_loans.set(pending)
                await ctx.send(f"Denied loan request for {member.display_name}.")
                return
        await ctx.send("No pending loan request for that user.")

    @commands.group()
    @loanowner_check()
    async def loanowner(self, ctx):
        """Bot owner loan approval commands (global bank only)"""
        is_global = await bank.is_global()
        if not is_global:
            await ctx.send("The bank is not global. Use mod approval commands instead.")
            return
        if not await ctx.bot.is_owner(ctx.author):
            await ctx.send("Only the bot owner can use these commands.")
            return

    @loanowner.command(name="pending")
    async def loanowner_pending(self, ctx):
        """List all pending owner loan requests with details and buttons (paginated, global bank only)"""
        is_global = await bank.is_global()
        if not is_global:
            await ctx.send("The bank is not global. Use mod approval commands instead.")
            return
        if not await ctx.bot.is_owner(ctx.author):
            await ctx.send("Only the bot owner can use this command.")
            return
        pending = await self.config.pending_owner_loans()
        if not pending:
            await ctx.send("There are no pending owner loan requests.")
            return
        paginator = LoanApprovalPaginator(self, ctx, pending, is_owner=True)
        await paginator.send()

    @loanowner.command(name="approve")
    async def loanowner_approve(self, ctx, user: discord.User):
        """Approve a user's pending owner loan request (manual fallback, global bank only)"""
        is_global = await bank.is_global()
        if not is_global:
            await ctx.send("The bank is not global. Use mod approval commands instead.")
            return
        if not await ctx.bot.is_owner(ctx.author):
            await ctx.send("Only the bot owner can use this command.")
            return
        pending = await self.config.pending_owner_loans()
        for req in pending:
            if req["user_id"] == user.id:
                await bank.deposit_credits(user, req["amount"])
                await self.config.user(user).loan_amount.set(req["amount"])
                pending.remove(req)
                await self.config.pending_owner_loans.set(pending)
                await ctx.send(f"Approved and credited {req['amount']} to {user.display_name}.")
                return
        await ctx.send("No pending owner loan request for that user.")

    @loanowner.command(name="deny")
    async def loanowner_deny(self, ctx, user: discord.User):
        """Deny a user's pending owner loan request (manual fallback, global bank only)"""
        is_global = await bank.is_global()
        if not is_global:
            await ctx.send("The bank is not global. Use mod approval commands instead.")
            return
        if not await ctx.bot.is_owner(ctx.author):
            await ctx.send("Only the bot owner can use this command.")
            return
        pending = await self.config.pending_owner_loans()
        for req in pending:
            if req["user_id"] == user.id:
                pending.remove(req)
                await self.config.pending_owner_loans.set(pending)
                await ctx.send(f"Denied owner loan request for {user.display_name}.")
                return
        await ctx.send("No pending owner loan request for that user.")

    @loanowner.command(name="setinterest")
    async def loanowner_setinterest(self, ctx, rate: float):
        """Set the global interest rate (owner only, global bank only)"""
        is_global = await bank.is_global()
        if not is_global:
            await ctx.send("The bank is not global. Use [p]loanset interest for guilds.")
            return
        if not await ctx.bot.is_owner(ctx.author):
            await ctx.send("Only the bot owner can use this command.")
            return
        if rate < 0:
            await ctx.send("Interest rate must be non-negative.")
            return
        await self.config.interest_rate.set(rate)
        await ctx.send(f"Global interest rate set to {rate * 100:.2f}%.")

    @loanset.command()
    async def interestinterval(self, ctx, interval: str = None):
        """Set or show the interest interval (e.g., 12h, 2d, 24h). Leave blank to show current."""
        is_global = await bank.is_global()
        if is_global:
            await ctx.send("The bank is global. Use [p]loanowner setinterestinterval to set the global interval.")
            return
        if interval is None:
            interval_str = await self.config.guild(ctx.guild).interest_interval()
            last_applied = await self.config.guild(ctx.guild).last_interest()
            msg = f"Current interest interval: {interval_str}."
            if last_applied:
                msg += f" Last applied: {last_applied} UTC."
            await ctx.send(msg)
            return
        if not self.parse_interval(interval):
            await ctx.send("Invalid interval. Use e.g. 12h, 2d, 24h.")
            return
        await self.config.guild(ctx.guild).interest_interval.set(interval)
        await ctx.send(f"Interest interval set to {interval}.")

    @loanowner.command(name="setinterestinterval")
    async def loanowner_setinterestinterval(self, ctx, interval: str = None):
        """Set or show the global interest interval (owner only, global bank only). Leave blank to show current."""
        is_global = await bank.is_global()
        if not is_global:
            await ctx.send("The bank is not global. Use [p]loanset interestinterval for guilds.")
            return
        if not await ctx.bot.is_owner(ctx.author):
            await ctx.send("Only the bot owner can use this command.")
            return
        if interval is None:
            interval_str = await self.config.interest_interval()
            last_applied = await self.config.last_interest()
            msg = f"Current global interest interval: {interval_str}."
            if last_applied:
                msg += f" Last applied: {last_applied} UTC."
            await ctx.send(msg)
            return
        if not self.parse_interval(interval):
            await ctx.send("Invalid interval. Use e.g. 12h, 2d, 24h.")
            return
        await self.config.interest_interval.set(interval)
        await ctx.send(f"Global interest interval set to {interval}.")

    @loanowner.command(name="setreviewchannel")
    async def loanowner_setreviewchannel(self, ctx, channel: discord.TextChannel = None):
        """Set the global review channel for owner loan requests (leave blank to disable)"""
        is_global = await bank.is_global()
        if not is_global:
            await ctx.send("The bank is not global. Use [p]loanset reviewchannel for guilds.")
            return
        if not await ctx.bot.is_owner(ctx.author):
            await ctx.send("Only the bot owner can use this command.")
            return
        current = await self.config.review_channel()
        if channel:
            if current == channel.id:
                await ctx.send(f"Global review channel is already set to {channel.mention}.")
                return
        else:
            if current is None:
                await ctx.send("Global review channel notifications are already disabled.")
                return
        await self.config.review_channel.set(channel.id if channel else None)
        if channel:
            await ctx.send(f"Global review channel set to {channel.mention}.")
        else:
            await ctx.send("Global review channel notifications disabled.")

    @loanowner.command(name="setdmnotify")
    async def loanowner_setdmnotify(self, ctx, value: bool):
        """Enable or disable global DM notifications for loan approval/denial (owner only, global mode)"""
        is_global = await bank.is_global()
        if not is_global:
            await ctx.send("The bank is not global. Use [p]loanset dmnotify for guilds.")
            return
        if not await ctx.bot.is_owner(ctx.author):
            await ctx.send("Only the bot owner can use this command.")
            return
        await self.config.dm_notify.set(value)
        await ctx.send(f"Global DM notifications for loan approval/denial set to {value}.")

    @loan.command()
    async def interest(self, ctx):
        """Show the current interest rate and your interest owed (if you have a loan)"""
        is_global = await bank.is_global()
        if is_global:
            rate = await self.config.interest_rate()
        else:
            rate = await self.config.guild(ctx.guild).interest_rate()
        loan_amount = await self.config.user(ctx.author).loan_amount()
        if loan_amount and loan_amount > 0:
            interest = loan_amount * rate
            await ctx.send(f"Current interest rate: {rate * 100:.2f}%. You owe {interest:.2f} in interest on your loan of {loan_amount}.")
        else:
            await ctx.send(f"Current interest rate: {rate * 100:.2f}%. You have no outstanding loan.")

    @loan.command()
    @commands.admin_or_permissions(manage_guild=True)
    async def applyinterest(self, ctx):
        """Apply interest to all outstanding loans (guild or global, admin/owner only)"""
        is_global = await bank.is_global()
        if is_global:
            if not await ctx.bot.is_owner(ctx.author):
                await ctx.send("Only the bot owner can apply global interest.")
                return
            rate = await self.config.interest_rate()
            # Apply to all users in all guilds
            count = 0
            for user_id in (await self.config.all_users()).keys():
                user = self.bot.get_user(int(user_id))
                if not user:
                    continue
                loan_amount = await self.config.user(user).loan_amount()
                if loan_amount and loan_amount > 0:
                    new_amount = int(loan_amount * (1 + rate))
                    await self.config.user(user).loan_amount.set(new_amount)
                    count += 1
            await ctx.send(f"Applied {rate * 100:.2f}% global interest to {count} loans.")
        else:
            rate = await self.config.guild(ctx.guild).interest_rate()
            members = ctx.guild.members
            count = 0
            for member in members:
                loan_amount = await self.config.user(member).loan_amount()
                if loan_amount and loan_amount > 0:
                    new_amount = int(loan_amount * (1 + rate))
                    await self.config.user(member).loan_amount.set(new_amount)
                    count += 1
            await ctx.send(f"Applied {rate * 100:.2f}% interest to {count} loans in this server.")

    async def make_request_embed(self, ctx, req, is_owner):
        """
        Create an embed for displaying loan request information.
        
        Args:
            ctx: Command context
            req: Request data containing user_id, amount, and date
            is_owner: Whether this is for owner approval (global) or mod approval (guild)
        
        Returns:
            discord.Embed: The formatted embed for the loan request
        """
        if is_owner:
            user = self.bot.get_user(req["user_id"])
            name = user.display_name if user else f"User ID {req['user_id']}"
            balance = await bank.get_balance(user) if user else "N/A"
        else:
            member = ctx.guild.get_member(req["user_id"])
            name = member.display_name if member else f"User ID {req['user_id']}"
            balance = await bank.get_balance(member) if member else "N/A"
        date = req.get("date", "N/A")
        embed = discord.Embed(title="Pending Loan Request" if not is_owner else "Pending Owner Loan Request", color=discord.Color.orange() if not is_owner else discord.Color.purple())
        embed.add_field(name="User", value=name, inline=True)
        embed.add_field(name="Amount", value=req["amount"], inline=True)
        embed.add_field(name="Date Submitted", value=date, inline=False)
        embed.add_field(name="Current Balance", value=balance, inline=True)
        return embed

    @loan.command()
    async def balance(self, ctx):
        """Show your current loan balance."""
        loan_amount = await self.config.user(ctx.author).loan_amount()
        if loan_amount and loan_amount > 0:
            await ctx.send(f"Your current loan balance is {loan_amount}.")
        else:
            await ctx.send("You have no outstanding loan.")

    @loanset.command()
    async def listloans(self, ctx):
        """List all users in this server with a loan balance (admin only)."""
        members = ctx.guild.members
        results = []
        for member in members:
            loan_amount = await self.config.user(member).loan_amount()
            if loan_amount and loan_amount > 0:
                results.append(f"{member.display_name} ({member.id}): {loan_amount}")
        if results:
            msg = "Users with outstanding loans:\n" + "\n".join(results)
        else:
            msg = "No users in this server have an outstanding loan."
        await ctx.send(msg)

    @loanowner.command(name="listloans")
    async def loanowner_listloans(self, ctx):
        """List all users globally with a loan balance (owner only, global bank only)."""
        is_global = await bank.is_global()
        if not is_global:
            await ctx.send("The bank is not global. Use [p]loanset listloans for guilds.")
            return
        if not await ctx.bot.is_owner(ctx.author):
            await ctx.send("Only the bot owner can use this command.")
            return
        results = []
        for user_id in (await self.config.all_users()).keys():
            user = self.bot.get_user(int(user_id))
            if not user:
                continue
            loan_amount = await self.config.user(user).loan_amount()
            if loan_amount and loan_amount > 0:
                results.append(f"{user.display_name} ({user.id}): {loan_amount}")
        if results:
            msg = "Users with outstanding loans (global):\n" + "\n".join(results)
        else:
            msg = "No users globally have an outstanding loan."
        await ctx.send(msg)





