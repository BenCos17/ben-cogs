import asyncio
import aiohttp
import zipfile
import os
import io
from datetime import datetime

from redbot.core import commands, tasks
from redbot.core.bot import Red

class BackupBot(commands.Cog):
    def __init__(self, bot: Red):
        self.bot = bot
        self.backup_task.start()

    def cog_unload(self):
        self.backup_task.cancel()


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

        return backup_filename  # Returns filename on disk
        folders_to_backup = ["cogs", "data", "config"]  # Adjust as needed
        buffer = io.BytesIO()

        with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as zipf:
            for folder in folders_to_backup:
                if not os.path.exists(folder):
                    continue
                for root, _, files in os.walk(folder):
                    for file in files:
                        filepath = os.path.join(root, file)
                        arcname = os.path.relpath(filepath, ".")
                        zipf.write(filepath, arcname)

        buffer.seek(0)
        return buffer.read()

    async def send_backup(self, data: bytes):
        url = "http://your-backup-server/endpoint"  # Replace with your server
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(url, data={"file": data}) as resp:
                    if resp.status == 200:
                        print("✅ Backup sent successfully.")
                    else:
                        print(f"❌ Failed to send backup. Status: {resp.status}")
        except Exception as e:
            print(f"❌ Error sending backup: {e}")

    @commands.command()
    async def manualbackup(self, ctx: commands.Context):
        """Run backup manually"""
        data = self.create_backup_zip()
        await self.send_backup(data)
        await ctx.send("📦 Backup created and sent.")

    @tasks.loop(hours=24)
    async def backup_task(self):
        data = self.create_backup_zip()
        await self.send_backup(data)

    @backup_task.before_loop
    async def before_backup(self):
        await self.bot.wait_until_ready()
