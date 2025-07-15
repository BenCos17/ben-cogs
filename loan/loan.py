import discord
from redbot.core import commands, Config, bank
from redbot.core.utils.chat_formatting import humanize_list

class BankLoan(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.config = Config.get_conf(self, identifier=1234567890)
        default_guild = {
            "require_mod_approval": False,
            "max_loan": 1000,
            "pending_loans": []  # List of dicts: {"user_id": int, "amount": int}
        }
        default_user = {
            "loan_amount": 0
        }
        self.config.register_guild(**default_guild)
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
        require_mod = await self.config.guild(guild).require_mod_approval()
        if require_mod:
            # Add to pending queue
            pending = await self.config.guild(guild).pending_loans()
            for req in pending:
                if req["user_id"] == user.id:
                    await ctx.send("You already have a pending loan request.")
                    return
            pending.append({"user_id": user.id, "amount": amount})
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
    async def loanmod(self, ctx):
        """Moderator loan approval commands"""
        if ctx.invoked_subcommand is None:
            await ctx.send("Invalid subcommand")

    @loanmod.command(name="pending")
    async def loanmod_pending(self, ctx):
        """List all pending loan requests"""
        pending = await self.config.guild(ctx.guild).pending_loans()
        if not pending:
            await ctx.send("There are no pending loan requests.")
            return
        lines = []
        for req in pending:
            member = ctx.guild.get_member(req["user_id"])
            name = member.display_name if member else f"User ID {req['user_id']}"
            lines.append(f"{name}: {req['amount']}")
        await ctx.send("Pending loan requests:\n" + "\n".join(lines))

    @loanmod.command(name="approve")
    async def loanmod_approve(self, ctx, member: discord.Member):
        """Approve a user's pending loan request"""
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
        """Deny a user's pending loan request"""
        pending = await self.config.guild(ctx.guild).pending_loans()
        for req in pending:
            if req["user_id"] == member.id:
                pending.remove(req)
                await self.config.guild(ctx.guild).pending_loans.set(pending)
                await ctx.send(f"Denied loan request for {member.display_name}.")
                return
        await ctx.send("No pending loan request for that user.")





