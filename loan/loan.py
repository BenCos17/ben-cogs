import discord
from redbot.core import commands, Config, bank

class BankLoan(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.config = Config.get_conf(self, identifier=1234567890)

    @commands.group()
    async def loan(self, ctx):
        """Bank loan commands"""
        if ctx.invoked_subcommand is None:
            await ctx.send("Invalid subcommand")

    @loan.command()
    async def request(self, ctx, amount: int):
        """Request a loan from the bank"""
        user = ctx.author
        # Check if user already has a loan
        has_loan = await self.config.user(user).loan_amount()
        if has_loan:
            await ctx.send("You already have an outstanding loan. Please repay it first.")
            return
        # Give the user the loan amount
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
        # Check if user can pay
        if not await bank.can_spend(user, amount):
            await ctx.send("You do not have enough funds to repay this amount.")
            return
        await bank.withdraw_credits(user, amount)
        await self.config.user(user).loan_amount.set(loan_amount - amount)
        if loan_amount - amount <= 0:
            await ctx.send(f"You have fully repaid your loan!")
        else:
            await ctx.send(f"Loan repayment of {amount} submitted. Remaining loan: {loan_amount - amount}")





