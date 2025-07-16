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

    @discord.ui.button(label="Approve", style=discord.ButtonStyle.green)
    async def approve(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.cog.handle_approve(interaction, self.request, self.is_owner)
        self.disable_all_items()
        await interaction.response.edit_message(view=self)

    @discord.ui.button(label="Deny", style=discord.ButtonStyle.red)
    async def deny(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.cog.handle_deny(interaction, self.request, self.is_owner)
        self.disable_all_items()
        await interaction.response.edit_message(view=self)

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
            req = self.parent.requests[self.parent.index]
            result = await self.parent.cog.handle_approve(interaction, req, self.parent.is_owner)
            if result is False:
                # Ensure the interaction is always responded to
                if not interaction.response.is_done():
                    await interaction.response.defer(ephemeral=True)
                return  # Error already handled
            del self.parent.requests[self.parent.index]
            if not self.parent.requests:
                await interaction.response.edit_message(content="No more pending requests.", embed=None, view=None)
                return
            if self.parent.index >= len(self.parent.requests):
                self.parent.index = len(self.parent.requests) - 1
            await self.parent.update(interaction)

    class DenyButton(discord.ui.Button):
        def __init__(self, parent):
            super().__init__(style=discord.ButtonStyle.red, label="Deny")
            self.parent = parent
        async def callback(self, interaction: discord.Interaction):
            req = self.parent.requests[self.parent.index]
            result = await self.parent.cog.handle_deny(interaction, req, self.parent.is_owner)
            if result is False:
                # Ensure the interaction is always responded to
                if not interaction.response.is_done():
                    await interaction.response.defer(ephemeral=True)
                return  # Error already handled
            del self.parent.requests[self.parent.index]
            if not self.parent.requests:
                await interaction.response.edit_message(content="No more pending requests.", embed=None, view=None)
                return
            if self.parent.index >= len(self.parent.requests):
                self.parent.index = len(self.parent.requests) - 1
            await self.parent.update(interaction)

class BankLoan(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.config = Config.get_conf(self, identifier=492089091320446976)
        default_guild = {
            "require_mod_approval": False,
            "max_loan": 1000,
            "pending_loans": [],  
            "review_channel": None,  # Channel ID for pending review
            "interest_rate": 0.05,  # Default 5% interest
            "interest_interval": "24h",  # Default 24 hours
            "last_interest": None
        }
        default_global = {
            "pending_owner_loans": [],  
            "interest_rate": 0.05,  # Default 5% interest (global)
            "interest_interval": "24h",  # Default 24 hours (global)
            "last_interest": None
        }
        default_user = {
            "loan_amount": 0
        }
        self.config.register_guild(**default_guild)
        self.config.register_global(**default_global)
        self.config.register_user(**default_user)

    def cog_load(self):
        self.interest_task.start()

    def cog_unload(self):
        self.interest_task.cancel()

    @tasks.loop(minutes=10)
    async def interest_task(self):
        await self.bot.wait_until_red_ready()
        is_global = await bank.is_global()
        now = datetime.utcnow()
        if is_global:
            interval_str = await self.config.interest_interval()
            last_applied = await self.config.last_interest()
            interval = self.parse_interval(interval_str)
            if not interval:
                return
            if last_applied:
                last_applied_dt = datetime.fromisoformat(last_applied)
                if now < last_applied_dt + interval:
                    return
            # Apply global interest
            ctx = None  # No context for background
            await self.apply_interest_global()
            await self.config.last_interest.set(now.isoformat())
        else:
            for guild in self.bot.guilds:
                interval_str = await self.config.guild(guild).interest_interval()
                last_applied = await self.config.guild(guild).last_interest()
                interval = self.parse_interval(interval_str)
                if not interval:
                    continue
                if last_applied:
                    last_applied_dt = datetime.fromisoformat(last_applied)
                    if now < last_applied_dt + interval:
                        continue
                await self.apply_interest_guild(guild)
                await self.config.guild(guild).last_interest.set(now.isoformat())

    @staticmethod
    def parse_interval(interval_str):
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
        rate = await self.config.guild(guild).interest_rate()
        members = guild.members
        for member in members:
            loan_amount = await self.config.user(member).loan_amount()
            if loan_amount and loan_amount > 0:
                new_amount = int(loan_amount * (1 + rate))
                await self.config.user(member).loan_amount.set(new_amount)

    async def apply_interest_global(self):
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
        """Request a loan from the bank"""
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
            # Owner approval required
            pending = await self.config.pending_owner_loans()
            for req in pending:
                if req["user_id"] == user.id:
                    await ctx.send("You already have a pending loan request.")
                    return
            pending.append({"user_id": user.id, "amount": amount, "date": now})
            await self.config.pending_owner_loans.set(pending)
            await ctx.send(f"Loan request for {amount} submitted and is pending bot owner approval.")
            # Send to review channel if set (global)
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
            # Add to pending queue
            pending = await self.config.guild(guild).pending_loans()
            for req in pending:
                if req["user_id"] == user.id:
                    await ctx.send("You already have a pending loan request.")
                    return
            pending.append({"user_id": user.id, "amount": amount, "date": now})
            await self.config.guild(guild).pending_loans.set(pending)
            await ctx.send(f"Loan request for {amount} submitted and is pending moderator approval.")
            # Send to review channel if set (guild)
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
            await bank.deposit_credits(user, amount)
            await self.config.user(user).loan_amount.set(amount)
            await ctx.send(f"Loan request for {amount} submitted and credited to your account.")

    @loan.command()
    async def repay(self, ctx, amount: int):
        """Repay a loan to the bank"""
        user = ctx.author
        loan_amount = await self.config.user(user).loan_amount()
        if not loan_amount or loan_amount <= 0:
            await ctx.send("You do not have any outstanding loans.")
            return
        if amount > loan_amount:
            amount = loan_amount
        if not await bank.can_spend(user, amount):
            await ctx.send("You do not have enough funds to repay this amount.")
            return
        await bank.withdraw_credits(user, amount)
        await self.config.user(user).loan_amount.set(loan_amount - amount)
        if loan_amount - amount <= 0:
            await ctx.send(f"You have fully repaid your loan!")
        else:
            await ctx.send(f"Loan repayment of {amount} submitted. Remaining loan: {loan_amount - amount}")

    @commands.group()
    @commands.admin_or_permissions(manage_guild=True)
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
        if is_owner:
            pending = await self.config.pending_owner_loans()
            user = self.bot.get_user(request["user_id"])
        else:
            pending = await self.config.guild(interaction.guild).pending_loans()
            user = interaction.guild.get_member(request["user_id"])
        if not user:
            await interaction.followup.send("User not found.", ephemeral=True)
            return False
        if request not in pending:
            await interaction.followup.send("Request no longer pending.", ephemeral=True)
            return False
        await bank.deposit_credits(user, request["amount"])
        await self.config.user(user).loan_amount.set(request["amount"])
        pending.remove(request)
        if is_owner:
            await self.config.pending_owner_loans.set(pending)
        else:
            await self.config.guild(interaction.guild).pending_loans.set(pending)
        # Do not send a followup message here; paginator will update the view
        return True

    async def handle_deny(self, interaction, request, is_owner):
        if is_owner:
            pending = await self.config.pending_owner_loans()
            user = self.bot.get_user(request["user_id"])
        else:
            pending = await self.config.guild(interaction.guild).pending_loans()
            user = interaction.guild.get_member(request["user_id"])
        if not user:
            await interaction.followup.send("User not found.", ephemeral=True)
            return False
        if request not in pending:
            await interaction.followup.send("Request no longer pending.", ephemeral=True)
            return False
        pending.remove(request)
        if is_owner:
            await self.config.pending_owner_loans.set(pending)
        else:
            await self.config.guild(interaction.guild).pending_loans.set(pending)
        # Do not send a followup message here; paginator will update the view
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





