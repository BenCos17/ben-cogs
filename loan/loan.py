import discord
from redbot.core import commands, Config, bank
from redbot.core.utils.chat_formatting import humanize_list
from datetime import datetime


# Custom check to hide loanmod commands if bank is global
async def bank_not_global(ctx):
    return not await bank.is_global()

def loanmod_check():
    return commands.check(bank_not_global)

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

class BankLoan(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.config = Config.get_conf(self, identifier=492089091320446976)
        default_guild = {
            "require_mod_approval": False,
            "max_loan": 1000,
            "pending_loans": []  # List of dicts: {"user_id": int, "amount": int, "date": str}
        }
        default_global = {
            "pending_owner_loans": []  # List of dicts: {"user_id": int, "amount": int, "date": str}
        }
        default_user = {
            "loan_amount": 0
        }
        self.config.register_guild(**default_guild)
        self.config.register_global(**default_global)
        self.config.register_user(**default_user)

    @commands.group()
    async def loan(self, ctx):
        """Bank loan commands"""
        if ctx.invoked_subcommand is None:
            await ctx.send("Invalid subcommand")

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
        if ctx.invoked_subcommand is None:
            await ctx.send("Invalid subcommand")

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

    @commands.group()
    @commands.mod_or_permissions(manage_guild=True)
    @loanmod_check()
    async def loanmod(self, ctx):
        """Moderator loan approval commands"""
        if ctx.invoked_subcommand is None:
            await ctx.send("Invalid subcommand")

    @loanmod.command(name="pending")
    async def loanmod_pending(self, ctx):
        """List all pending loan requests with details and buttons"""
        pending = await self.config.guild(ctx.guild).pending_loans()
        if not pending:
            await ctx.send("There are no pending loan requests.")
            return
        for req in pending:
            member = ctx.guild.get_member(req["user_id"])
            name = member.display_name if member else f"User ID {req['user_id']}"
            balance = await bank.get_balance(member) if member else "N/A"
            date = req.get("date", "N/A")
            embed = discord.Embed(title="Pending Loan Request", color=discord.Color.orange())
            embed.add_field(name="User", value=name, inline=True)
            embed.add_field(name="Amount", value=req["amount"], inline=True)
            embed.add_field(name="Date Submitted", value=date, inline=False)
            embed.add_field(name="Current Balance", value=balance, inline=True)
            await ctx.send(embed=embed, view=LoanApprovalView(self, ctx, req, is_owner=False))

    async def handle_approve(self, interaction, request, is_owner):
        if is_owner:
            pending = await self.config.pending_owner_loans()
            user = self.bot.get_user(request["user_id"])
        else:
            pending = await self.config.guild(interaction.guild).pending_loans()
            user = interaction.guild.get_member(request["user_id"])
        if not user:
            await interaction.followup.send("User not found.", ephemeral=True)
            return
        if request not in pending:
            await interaction.followup.send("Request no longer pending.", ephemeral=True)
            return
        await bank.deposit_credits(user, request["amount"])
        await self.config.user(user).loan_amount.set(request["amount"])
        pending.remove(request)
        if is_owner:
            await self.config.pending_owner_loans.set(pending)
        else:
            await self.config.guild(interaction.guild).pending_loans.set(pending)
        await interaction.followup.send(f"Approved and credited {request['amount']} to {user.display_name}.", ephemeral=True)

    async def handle_deny(self, interaction, request, is_owner):
        if is_owner:
            pending = await self.config.pending_owner_loans()
            user = self.bot.get_user(request["user_id"])
        else:
            pending = await self.config.guild(interaction.guild).pending_loans()
            user = interaction.guild.get_member(request["user_id"])
        if not user:
            await interaction.followup.send("User not found.", ephemeral=True)
            return
        if request not in pending:
            await interaction.followup.send("Request no longer pending.", ephemeral=True)
            return
        pending.remove(request)
        if is_owner:
            await self.config.pending_owner_loans.set(pending)
        else:
            await self.config.guild(interaction.guild).pending_loans.set(pending)
        await interaction.followup.send(f"Denied loan request for {user.display_name}.", ephemeral=True)

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
    async def loanowner(self, ctx):
        """Bot owner loan approval commands (global bank only)"""
        is_global = await bank.is_global()
        if not is_global:
            await ctx.send("The bank is not global. Use mod approval commands instead.")
            return
        if not await ctx.bot.is_owner(ctx.author):
            await ctx.send("Only the bot owner can use these commands.")
            return
        if ctx.invoked_subcommand is None:
            await ctx.send("Invalid subcommand")

    @loanowner.command(name="pending")
    async def loanowner_pending(self, ctx):
        """List all pending owner loan requests with details and buttons (global bank only)"""
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
        for req in pending:
            user = self.bot.get_user(req["user_id"])
            name = user.display_name if user else f"User ID {req['user_id']}"
            balance = await bank.get_balance(user) if user else "N/A"
            date = req.get("date", "N/A")
            embed = discord.Embed(title="Pending Owner Loan Request", color=discord.Color.purple())
            embed.add_field(name="User", value=name, inline=True)
            embed.add_field(name="Amount", value=req["amount"], inline=True)
            embed.add_field(name="Date Submitted", value=date, inline=False)
            embed.add_field(name="Current Balance", value=balance, inline=True)
            await ctx.send(embed=embed, view=LoanApprovalView(self, ctx, req, is_owner=True))

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





