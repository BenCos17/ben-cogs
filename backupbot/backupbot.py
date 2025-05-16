from redbot.core import commands
from redbot.core.bot import Red
from redbot.core.config import Config
from discord.ext import tasks
import aiohttp
import zipfile
import os
from datetime import datetime

class BackupBot(commands.Cog):
    def __init__(self, bot: Red):
        self.bot = bot
        self.config = Config.get_conf(self, identifier=1234567890)
        self.config.register_global(url=None)  # Store URL globally
        self.backup_task.start()

    def cog_unload(self):
        self.backup_task.cancel()

    async def get_backup_url(self) -> str | None:
        return await self.config.url()

    async def set_backup_url(self, url: str):
        await self.config.url.set(url)

    def create_backup_zip(self) -> str:
        folders_to_backup = ["cogs", "data", "config"]
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_filename = f"backup_{timestamp}.zip"

        with zipfile.ZipFile(backup_filename, "w", zipfile.ZIP_DEFLATED) as zipf:
            for folder in folders_to_backup:
                if not os.path.exists(folder):
                    continue
                for root, _, files in os.walk(folder):
                    for file in files:
                        filepath = os.path.join(root, file)
                        arcname = os.path.relpath(filepath, ".")
                        zipf.write(filepath, arcname)

        return backup_filename

    async def send_backup(self, filepath: str):
        url = await self.get_backup_url()
        if not url:
            print("❌ Backup URL not configured.")
            return
        try:
            async with aiohttp.ClientSession() as session:
                with open(filepath, "rb") as f:
                    data = f.read()
                    async with session.post(url, data={"file": data}) as resp:
                        if resp.status == 200:
                            print("✅ Backup sent successfully.")
                        else:
                            print(f"❌ Failed to send backup. Status: {resp.status}")
        except Exception as e:
            print(f"❌ Error sending backup: {e}")

    @commands.group()
    async def backupbot(self, ctx: commands.Context):
        """Backup bot configuration commands."""
        if ctx.invoked_subcommand is None:
            await ctx.send_help()

    @backupbot.command()
    async def seturl(self, ctx: commands.Context, url: str):
        """Set the backup server URL."""
        await self.set_backup_url(url)
        await ctx.send(f"Backup URL set to: {url}")

    @backupbot.command()
    async def geturl(self, ctx: commands.Context):
        """Get the current backup server URL."""
        url = await self.get_backup_url()
        if url:
            await ctx.send(f"Current backup URL: {url}")
        else:
            await ctx.send("Backup URL is not set.")

    @commands.command()
    async def manualbackup(self, ctx: commands.Context):
        """Run backup manually"""
        filepath = self.create_backup_zip()
        await self.send_backup(filepath)
        await ctx.send("📦 Backup created and sent.")

    @tasks.loop(hours=24)
    async def backup_task(self):
        filepath = self.create_backup_zip()
        await self.send_backup(filepath)

    @backup_task.before_loop
    async def before_backup(self):
        await self.bot.wait_until_ready()
