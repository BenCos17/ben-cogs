from typing import Callable, Awaitable, List, Optional, Dict

class SquawkAlertAPI:
    """
    API for registering and calling squawk alert callbacks.
    Other cogs can register a coroutine callback to be notified when a squawk alert is triggered.
    Supports pre-send (message mutator) and post-send (after message sent) hooks.
    """
    def __init__(self):
        self._callbacks: List[Callable] = []
        self._pre_send_callbacks: List[Callable] = []
        self._post_send_callbacks: List[Callable] = []

    def register_callback(self, callback: Callable):
        self._callbacks.append(callback)

    def register_pre_send_callback(self, callback: Callable):
        """
        Register a callback to modify the message before it is sent.
        The callback should be: async def cb(guild, aircraft_info, squawk_code, message_data) -> Optional[dict]
        message_data: {'content': str, 'embed': discord.Embed, 'view': discord.ui.View}
        Return a dict to replace/modify, or None to leave unchanged.
        """
        self._pre_send_callbacks.append(callback)

    def register_post_send_callback(self, callback: Callable):
        """
        Register a callback to run after the message is sent.
        The callback should be: async def cb(guild, aircraft_info, squawk_code, sent_message)
        """
        self._post_send_callbacks.append(callback)

    async def call_callbacks(self, guild: Optional[Discord Guild], 
                            aircraft_info: Dict, 
                            squawk_code: str) -> None:
        """Call all registered callbacks with the provided parameters."""
        for cb in self._callbacks:
            try:
                await cb(guild, aircraft_info, squawk_code)
            except Exception as e:
                print(f"Error in squawk alert callback: {e}")

    async def run_pre_send(self, guild: Optional[Discord Guild], 
                          aircraft_info: Dict, 
                          squawk_code: str, 
                          message_data: Dict) -> Dict:
        """
        Run all pre-send callbacks and update the message data.
        """
        for cb in self._pre_send_callbacks:
            try:
                result = await cb(guild, aircraft_info, squawk_code, message_data)
                if result:
                    message_data.update(result)
            except Exception as e:
                print(f"Error in pre-send callback: {e}")

    async def run_post_send(self, guild: Optional[Discord Guild], 
                          aircraft_info: Dict, 
                          squawk_code: str, 
                          sent_message: Any) -> None:
        """
        Run all post-send callbacks after the message has been sent.
        """
        for cb in self._post_send_callbacks:
            try:
                await cb(guild, aircraft_info, squawk_code, sent_message)
            except Exception as e:
                print(f"Error in post-send callback: {e}")
