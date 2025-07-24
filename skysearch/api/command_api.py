import asyncio
import logging
import time
from typing import Callable, Awaitable, List, Optional, Dict, Any
from dataclasses import dataclass, field
from collections import defaultdict

log = logging.getLogger("red.skysearch.command_api")

@dataclass
class CommandCallbackInfo:
    """Metadata about a registered command callback."""
    callback: Callable
    cog_name: str
    priority: int = 0
    timeout: float = 15.0  # Commands might take longer
    max_failures: int = 5
    failure_count: int = 0
    last_failure: float = 0
    enabled: bool = True
    registered_at: float = field(default_factory=time.time)
    command_filter: Optional[List[str]] = None  # Only run for specific commands

class CommandAPI:
    """
    Enhanced API for registering and calling command execution callbacks.
    Other cogs can register coroutine callbacks to be notified when SkySearch commands are executed.
    Supports pre-execute (before command runs) and post-execute (after command completes) hooks.
    
    Features:
    - Command filtering (only run callbacks for specific commands)
    - Performance metrics and timing
    - Circuit breaker for failing callbacks
    - Priority-based execution
    - Detailed execution results
    """
    def __init__(self):
        self._callbacks: List[CommandCallbackInfo] = []
        self._pre_execute_callbacks: List[CommandCallbackInfo] = []
        self._post_execute_callbacks: List[CommandCallbackInfo] = []
        
        # Performance metrics
        self._metrics = {
            'total_commands': 0,
            'successful_commands': 0,
            'cancelled_commands': 0,
            'failed_commands': 0,
            'avg_execution_time': 0.0,
            'command_stats': defaultdict(lambda: {'count': 0, 'avg_time': 0.0, 'failures': 0}),
            'callback_stats': defaultdict(lambda: {'calls': 0, 'failures': 0, 'total_time': 0.0})
        }
        
        # Command execution tracking
        self._active_commands: Dict[str, Dict] = {}  # Track currently executing commands
        self._lock = asyncio.Lock()

    def register_callback(self, callback: Callable, cog_name: str = "Unknown", priority: int = 0, 
                         timeout: float = 15.0, command_filter: Optional[List[str]] = None) -> bool:
        """
        Register a basic command execution callback.
        
        Args:
            callback: Async function with signature (ctx, command_name, args)
            cog_name: Name of the registering cog for debugging
            priority: Higher priority callbacks run first (default: 0)
            timeout: Max execution time in seconds (default: 15.0)
            command_filter: List of command names to filter for (None = all commands)
            
        Returns:
            bool: True if registered successfully, False if already registered
        """
        if self._is_callback_registered(callback, self._callbacks):
            log.warning(f"Command callback from {cog_name} already registered")
            return False
            
        callback_info = CommandCallbackInfo(
            callback=callback,
            cog_name=cog_name,
            priority=priority,
            timeout=timeout,
            command_filter=command_filter
        )
        
        self._callbacks.append(callback_info)
        self._callbacks.sort(key=lambda x: x.priority, reverse=True)
        
        filter_info = f" (filter: {command_filter})" if command_filter else ""
        log.info(f"Registered command callback from {cog_name} (priority: {priority}){filter_info}")
        return True

    def register_pre_execute_callback(self, callback: Callable, cog_name: str = "Unknown", 
                                    priority: int = 0, timeout: float = 10.0, 
                                    command_filter: Optional[List[str]] = None) -> bool:
        """
        Register a callback to run before a command executes.
        
        Args:
            callback: Async function with signature (ctx, command_name, args) -> Optional[bool]
            cog_name: Name of the registering cog
            priority: Higher priority callbacks run first
            timeout: Max execution time in seconds
            command_filter: List of command names to filter for
            
        Returns:
            bool: True if registered successfully
        """
        if self._is_callback_registered(callback, self._pre_execute_callbacks):
            log.warning(f"Pre-execute callback from {cog_name} already registered")
            return False
            
        callback_info = CommandCallbackInfo(
            callback=callback,
            cog_name=cog_name,
            priority=priority,
            timeout=timeout,
            command_filter=command_filter
        )
        
        self._pre_execute_callbacks.append(callback_info)
        self._pre_execute_callbacks.sort(key=lambda x: x.priority, reverse=True)
        
        filter_info = f" (filter: {command_filter})" if command_filter else ""
        log.info(f"Registered pre-execute callback from {cog_name} (priority: {priority}){filter_info}")
        return True

    def register_post_execute_callback(self, callback: Callable, cog_name: str = "Unknown", 
                                     priority: int = 0, timeout: float = 15.0, 
                                     command_filter: Optional[List[str]] = None) -> bool:
        """
        Register a callback to run after a command completes.
        
        Args:
            callback: Async function with signature (ctx, command_name, args, result, execution_time)
            cog_name: Name of the registering cog
            priority: Higher priority callbacks run first
            timeout: Max execution time in seconds
            command_filter: List of command names to filter for
            
        Returns:
            bool: True if registered successfully
        """
        if self._is_callback_registered(callback, self._post_execute_callbacks):
            log.warning(f"Post-execute callback from {cog_name} already registered")
            return False
            
        callback_info = CommandCallbackInfo(
            callback=callback,
            cog_name=cog_name,
            priority=priority,
            timeout=timeout,
            command_filter=command_filter
        )
        
        self._post_execute_callbacks.append(callback_info)
        self._post_execute_callbacks.sort(key=lambda x: x.priority, reverse=True)
        
        filter_info = f" (filter: {command_filter})" if command_filter else ""
        log.info(f"Registered post-execute callback from {cog_name} (priority: {priority}){filter_info}")
        return True

    def unregister_callback(self, callback: Callable, callback_type: str = "all") -> bool:
        """
        Unregister a callback.
        
        Args:
            callback: The callback function to unregister
            callback_type: "basic", "pre_execute", "post_execute", or "all"
            
        Returns:
            bool: True if any callbacks were removed
        """
        removed = False
        
        if callback_type in ("basic", "all"):
            removed |= self._remove_callback_from_list(callback, self._callbacks)
            
        if callback_type in ("pre_execute", "all"):
            removed |= self._remove_callback_from_list(callback, self._pre_execute_callbacks)
            
        if callback_type in ("post_execute", "all"):
            removed |= self._remove_callback_from_list(callback, self._post_execute_callbacks)
            
        if removed:
            log.info(f"Unregistered command callback ({callback_type})")
            
        return removed

    async def call_callbacks(self, ctx, command_name: str, args: list) -> Dict[str, Any]:
        """Call all basic callbacks when a command is executed."""
        command_key = f"{ctx.guild.id if ctx.guild else 'DM'}_{command_name}_{ctx.message.id}"
        
        async with self._lock:
            self._active_commands[command_key] = {
                'command_name': command_name,
                'start_time': time.time(),
                'guild_id': ctx.guild.id if ctx.guild else None,
                'user_id': ctx.author.id
            }
        
        try:
            results = await self._execute_callbacks(
                self._callbacks,
                "basic_callback",
                command_name,
                ctx, command_name, args
            )
            
            self._metrics['total_commands'] += 1
            return results
            
        finally:
            async with self._lock:
                self._active_commands.pop(command_key, None)

    async def run_pre_execute(self, ctx, command_name: str, args: list) -> bool:
        """Run pre-execute callbacks. Returns False if any callback cancels execution."""
        results = await self._execute_callbacks(
            self._pre_execute_callbacks,
            "pre_execute_callback",
            command_name,
            ctx, command_name, args
        )
        
        # Check if any callback cancelled execution
        for result in results['callback_results']:
            if result['success'] and result['return_value'] is False:
                log.info(f"Command {command_name} cancelled by {result['cog_name']}")
                self._metrics['cancelled_commands'] += 1
                return False
                
        return True

    async def run_post_execute(self, ctx, command_name: str, args: list, result: Any, execution_time: float) -> Dict[str, Any]:
        """Run post-execute callbacks after command completion."""
        # Update command statistics
        stats = self._metrics['command_stats'][command_name]
        stats['count'] += 1
        stats['avg_time'] = (stats['avg_time'] * (stats['count'] - 1) + execution_time) / stats['count']
        
        if isinstance(result, Exception):
            stats['failures'] += 1
            self._metrics['failed_commands'] += 1
        else:
            self._metrics['successful_commands'] += 1
        
        return await self._execute_callbacks(
            self._post_execute_callbacks,
            "post_execute_callback",
            command_name,
            ctx, command_name, args, result, execution_time
        )

    async def _execute_callbacks(self, callback_list: List[CommandCallbackInfo], callback_type: str, 
                               command_name: str, *args) -> Dict[str, Any]:
        """Execute a list of callbacks with filtering, error handling, and metrics."""
        start_time = time.time()
        results = {
            'callback_type': callback_type,
            'command_name': command_name,
            'total_callbacks': len(callback_list),
            'filtered_callbacks': 0,
            'success_count': 0,
            'error_count': 0,
            'disabled_count': 0,
            'execution_time': 0.0,
            'callback_results': []
        }
        
        # Filter callbacks by command if they have filters
        filtered_callbacks = []
        for callback_info in callback_list:
            if not callback_info.enabled:
                results['disabled_count'] += 1
                continue
                
            if callback_info.command_filter and command_name not in callback_info.command_filter:
                results['filtered_callbacks'] += 1
                continue
                
            filtered_callbacks.append(callback_info)
        
        # Execute filtered callbacks
        for callback_info in filtered_callbacks:
            callback_start = time.time()
            callback_result = {
                'cog_name': callback_info.cog_name,
                'success': False,
                'execution_time': 0.0,
                'error': None,
                'return_value': None
            }
            
            try:
                # Execute with timeout
                result = await asyncio.wait_for(
                    callback_info.callback(*args),
                    timeout=callback_info.timeout
                )
                
                callback_result['success'] = True
                callback_result['return_value'] = result
                results['success_count'] += 1
                
                # Reset failure count on success
                callback_info.failure_count = 0
                
            except asyncio.TimeoutError:
                error_msg = f"Callback timeout ({callback_info.timeout}s)"
                callback_result['error'] = error_msg
                results['error_count'] += 1
                await self._handle_callback_failure(callback_info, error_msg)
                
            except Exception as e:
                error_msg = f"Callback error: {e}"
                callback_result['error'] = error_msg
                results['error_count'] += 1
                await self._handle_callback_failure(callback_info, error_msg)
                
            finally:
                callback_result['execution_time'] = time.time() - callback_start
                results['callback_results'].append(callback_result)
                
                # Update metrics
                stats = self._metrics['callback_stats'][callback_info.cog_name]
                stats['calls'] += 1
                stats['total_time'] += callback_result['execution_time']
                if not callback_result['success']:
                    stats['failures'] += 1
        
        results['execution_time'] = time.time() - start_time
        return results

    async def _handle_callback_failure(self, callback_info: CommandCallbackInfo, error_msg: str):
        """Handle callback failure with circuit breaker logic."""
        callback_info.failure_count += 1
        callback_info.last_failure = time.time()
        
        log.error(f"Command callback failure in {callback_info.cog_name}: {error_msg}")
        
        if callback_info.failure_count >= callback_info.max_failures:
            callback_info.enabled = False
            log.error(f"Disabled command callback from {callback_info.cog_name} after {callback_info.failure_count} failures")

    def _is_callback_registered(self, callback: Callable, callback_list: List[CommandCallbackInfo]) -> bool:
        """Check if a callback is already registered."""
        return any(cb.callback == callback for cb in callback_list)

    def _remove_callback_from_list(self, callback: Callable, callback_list: List[CommandCallbackInfo]) -> bool:
        """Remove a callback from a list."""
        original_length = len(callback_list)
        callback_list[:] = [cb for cb in callback_list if cb.callback != callback]
        return len(callback_list) < original_length

    def get_stats(self) -> Dict[str, Any]:
        """Get comprehensive API usage statistics."""
        return {
            'total_callbacks': len(self._callbacks) + len(self._pre_execute_callbacks) + len(self._post_execute_callbacks),
            'basic_callbacks': len(self._callbacks),
            'pre_execute_callbacks': len(self._pre_execute_callbacks),
            'post_execute_callbacks': len(self._post_execute_callbacks),
            'enabled_callbacks': sum(1 for cb in self._callbacks + self._pre_execute_callbacks + self._post_execute_callbacks if cb.enabled),
            'active_commands': len(self._active_commands),
            'metrics': self._metrics.copy(),
            'callback_details': [
                {
                    'cog_name': cb.cog_name,
                    'priority': cb.priority,
                    'enabled': cb.enabled,
                    'failure_count': cb.failure_count,
                    'command_filter': cb.command_filter,
                    'registered_at': cb.registered_at
                }
                for cb in self._callbacks + self._pre_execute_callbacks + self._post_execute_callbacks
            ],
            'active_commands_details': list(self._active_commands.values())
        }

    def enable_callback(self, cog_name: str) -> bool:
        """Re-enable callbacks from a specific cog."""
        enabled_any = False
        for callback_list in [self._callbacks, self._pre_execute_callbacks, self._post_execute_callbacks]:
            for cb in callback_list:
                if cb.cog_name == cog_name and not cb.enabled:
                    cb.enabled = True
                    cb.failure_count = 0
                    enabled_any = True
                    
        if enabled_any:
            log.info(f"Re-enabled command callbacks from {cog_name}")
            
        return enabled_any

    def get_command_performance(self, command_name: str = None) -> Dict[str, Any]:
        """Get performance statistics for commands."""
        if command_name:
            return self._metrics['command_stats'].get(command_name, {})
        else:
            return dict(self._metrics['command_stats'])

    def get_active_commands(self) -> Dict[str, Dict]:
        """Get information about currently executing commands."""
        current_time = time.time()
        active_with_duration = {}
        
        for cmd_key, cmd_info in self._active_commands.items():
            cmd_info_copy = cmd_info.copy()
            cmd_info_copy['duration'] = current_time - cmd_info['start_time']
            active_with_duration[cmd_key] = cmd_info_copy
            
        return active_with_duration 