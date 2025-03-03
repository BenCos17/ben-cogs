import asyncio
import sdnotify
from redbot.core import commands

class Watchdog(commands.Cog):
    """Systemd watchdog for Redbot"""

    def __init__(self, bot):
        self.bot = bot
        self.notifier = sdnotify.SystemdNotifier()
        self.bot.loop.create_task(self.watchdog_loop())

    async def watchdog_loop(self):
        self.notifier.notify("READY=1")
        while True:
            self.notifier.notify("WATCHDOG=1")
            await asyncio.sleep(10)  # Ping systemd every 10 seconds


