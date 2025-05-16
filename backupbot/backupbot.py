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
        self.config.register_global(url=None, backup_path=None)
        self.backup_task.start()

    def cog_unload(self):
        self.backup_task.cancel()

    async def get_backup_url(self) -> str | None:
        return await self.config.url()

    async def set_backup_url(self, url: str):
        await self.config.url.set(url)

    async def get_backup_path(self) -> str | None:
        return await self.config.backup_path()

    async def set_backup_path(self, path: str):
        await self.config.backup_path.set(path)

    def create_backup_zip(self, folder: str) -> str:
        """
        Backup:
          - Red data folder (self.bot.data_folder)
          - This cog source folder (__file__)
        """

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_filename = os.path.join(folder, f"backup_{timestamp}.zip")

        data_folder = str(self.data_path)
        cog_folder = os.path.dirname(os.path.abspath(__file__))

        with zipfile.ZipFile(backup_filename, "w", zipfile.ZIP_DEFLATED) as zipf:
            # Add Red data folder contents
            if os.path.exists(data_folder):
                for root, _, files in os.walk(data_folder):
                    for file in files:
                        filepath = os.path.join(root, file)
                        arcname = os.path.relpath(filepath, data_folder)
                        arcname = os.path.join("red_data", arcname)
                        zipf.write(filepath, arcname)

            # Add cog folder contents
            if os.path.exists(cog_folder):
                for root, _, files in os.walk(cog_folder):
                    for file in files:
                        filepath = os.path.join(root, file)
                        arcname = os.path.relpath(filepath, cog_folder)
                        arcname = os.path.join("cog_source", arcname)
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

    async def save_backup_locally(self, folder: str) -> str:
        if not os.path.exists(folder):
            os.makedirs(folder, exist_ok=True)
        filepath = self.create_backup_zip(folder)
        return filepath

    @commands.group()
    async def backupbot(self, ctx: commands.Context):
        """Backup bot configuration commands."""
        if ctx.invoked_subcommand is None:
            await ctx.send_help()

    @backupbot.command()
    @commands.is_owner()
    async def seturl(self, ctx: commands.Context, url: str):
        """Set the backup server URL for HTTP backups."""
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

    @backupbot.command()
    @commands.is_owner()
    async def setlocalpath(self, ctx: commands.Context, *, path: str):
        """Set local backup folder path (e.g., Samba mount)."""
        await self.set_backup_path(path)
        await ctx.send(f"Local backup path set to: `{path}`")

    @backupbot.command()
    async def getlocalpath(self, ctx: commands.Context):
        """Get the current local backup folder path."""
        path = await self.get_backup_path()
        if path:
            await ctx.send(f"Local backup path: `{path}`")
        else:
            await ctx.send("Local backup path is not set.")

    @commands.command()
    async def manualbackup(self, ctx: commands.Context):
        """Run backup manually, save locally if set, and send over HTTP if URL set."""
        path = await self.get_backup_path()
        if path:
            if not os.path.exists(path):
                await ctx.send(f"❌ Backup path `{path}` does not exist.")
                return
            filepath = await self.save_backup_locally(path)
            await ctx.send(f"📦 Backup saved locally at `{filepath}`")
        else:
            await ctx.send("⚠️ No local backup path set; skipping local save.")

        url = await self.get_backup_url()
        if url:
            if not path:
                filepath = self.create_backup_zip(".")
            await self.send_backup(filepath)
            await ctx.send("📦 Backup sent via HTTP.")
        else:
            await ctx.send("⚠️ No backup URL set; skipping HTTP send.")

    @tasks.loop(hours=24)
    async def backup_task(self):
        path = await self.get_backup_path()
        if path and os.path.exists(path):
            filepath = await self.save_backup_locally(path)
            print(f"📦 Backup saved locally at {filepath}")
        else:
            print("⚠️ Local backup path not set or does not exist; skipping local save.")

        url = await self.get_backup_url()
        if url:
            if not path:
                filepath = self.create_backup_zip(".")
            await self.send_backup(filepath)
            print("📦 Backup sent via HTTP.")
        else:
            print("⚠️ Backup URL not set; skipping HTTP send.")

    @backup_task.before_loop
    async def before_backup(self):
        await self.bot.wait_until_ready()
