from typing import Callable, Awaitable, List, Optional, Dict

class CommandAPI:
    """
    API for registering and calling command execution callbacks.
    Other cogs can register a coroutine callback to be notified when SkySearch commands are executed.
    Supports pre-execute (before command runs) and post-execute (after command completes) hooks.
    """
    def __init__(self):
        self._callbacks: List[Callable] = []
        self._pre_execute_callbacks: List[Callable] = []
        self._post_execute_callbacks: List[Callable] = []

    def register_callback(self, callback: Callable):
        """Register a basic callback for command execution."""
        self._callbacks.append(callback)

    def register_pre_execute_callback(self, callback: Callable):
        """
        Register a callback to run before a command executes.
        The callback should be: async def cb(ctx, command_name, args) -> Optional[bool]
        Return True to continue execution, False to cancel, None for no change.
        """
        self._pre_execute_callbacks.append(callback)

    def register_post_execute_callback(self, callback: Callable):
        """
        Register a callback to run after a command completes.
        The callback should be: async def cb(ctx, command_name, args, result, execution_time)
        """
        self._post_execute_callbacks.append(callback)

    async def call_callbacks(self, ctx, command_name: str, args: list):
        """Call all basic callbacks when a command is executed."""
        for cb in self._callbacks:
            try:
                await cb(ctx, command_name, args)
            except Exception as e:
                print(f"Error in command callback: {e}")

    async def run_pre_execute(self, ctx, command_name: str, args: list) -> bool:
        """Run pre-execute callbacks. Returns False if any callback cancels execution."""
        for cb in self._pre_execute_callbacks:
            try:
                result = await cb(ctx, command_name, args)
                if result is False:  # Explicitly check for False to cancel
                    return False
            except Exception as e:
                print(f"Error in pre-execute callback: {e}")
        return True

    async def run_post_execute(self, ctx, command_name: str, args: list, result: any, execution_time: float):
        """Run post-execute callbacks after command completion."""
        for cb in self._post_execute_callbacks:
            try:
                await cb(ctx, command_name, args, result, execution_time)
            except Exception as e:
                print(f"Error in post-execute callback: {e}") 