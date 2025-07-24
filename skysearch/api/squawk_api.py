import asyncio
import logging
import time
from typing import Callable, Awaitable, List, Optional, Dict, Set, Any
from dataclasses import dataclass, field
from collections import defaultdict

log = logging.getLogger("red.skysearch.api")

@dataclass
class CallbackInfo:
    """Metadata about a registered callback."""
    callback: Callable
    cog_name: str
    priority: int = 0  # Higher priority callbacks run first
    timeout: float = 10.0  # Timeout in seconds
    max_failures: int = 5  # Max failures before disabling
    failure_count: int = 0
    last_failure: float = 0
    enabled: bool = True
    registered_at: float = field(default_factory=time.time)

class SquawkAlertAPI:
    """
    Enhanced API for registering and calling squawk alert callbacks.
    Other cogs can register coroutine callbacks to be notified when a squawk alert is triggered.
    Supports pre-send (message mutator) and post-send (after message sent) hooks.
    
    Features:
    - Callback deduplication
    - Error handling with circuit breaker
    - Priority-based execution
    - Performance metrics
    - Debug capabilities
    """
    def __init__(self):
        self._callbacks: List[CallbackInfo] = []
        self._pre_send_callbacks: List[CallbackInfo] = []
        self._post_send_callbacks: List[CallbackInfo] = []
        
        # Deduplication tracking
        self._recent_alerts: Dict[str, float] = {}
        self._dedup_window = 30.0  # seconds
        
        # Performance metrics
        self._metrics = {
            'total_calls': 0,
            'successful_calls': 0,
            'failed_calls': 0,
            'avg_execution_time': 0.0,
            'callback_stats': defaultdict(lambda: {'calls': 0, 'failures': 0, 'total_time': 0.0})
        }
        
        # Lock for thread safety
        self._lock = asyncio.Lock()

    def register_callback(self, callback: Callable, cog_name: str = "Unknown", priority: int = 0, timeout: float = 10.0) -> bool:
        """
        Register a basic squawk alert callback.
        
        Args:
            callback: Async function with signature (guild, aircraft_info, squawk_code)
            cog_name: Name of the registering cog for debugging
            priority: Higher priority callbacks run first (default: 0)
            timeout: Max execution time in seconds (default: 10.0)
            
        Returns:
            bool: True if registered successfully, False if already registered
        """
        if self._is_callback_registered(callback, self._callbacks):
            log.warning(f"Callback from {cog_name} already registered")
            return False
            
        callback_info = CallbackInfo(
            callback=callback,
            cog_name=cog_name,
            priority=priority,
            timeout=timeout
        )
        
        self._callbacks.append(callback_info)
        self._callbacks.sort(key=lambda x: x.priority, reverse=True)  # Higher priority first
        
        log.info(f"Registered squawk callback from {cog_name} (priority: {priority})")
        return True

    def register_pre_send_callback(self, callback: Callable, cog_name: str = "Unknown", priority: int = 0, timeout: float = 5.0) -> bool:
        """
        Register a callback to modify the message before it is sent.
        
        Args:
            callback: Async function with signature (guild, aircraft_info, squawk_code, message_data) -> Optional[dict]
            cog_name: Name of the registering cog
            priority: Higher priority callbacks run first
            timeout: Max execution time in seconds
            
        Returns:
            bool: True if registered successfully
        """
        if self._is_callback_registered(callback, self._pre_send_callbacks):
            log.warning(f"Pre-send callback from {cog_name} already registered")
            return False
            
        callback_info = CallbackInfo(
            callback=callback,
            cog_name=cog_name,
            priority=priority,
            timeout=timeout
        )
        
        self._pre_send_callbacks.append(callback_info)
        self._pre_send_callbacks.sort(key=lambda x: x.priority, reverse=True)
        
        log.info(f"Registered pre-send callback from {cog_name} (priority: {priority})")
        return True

    def register_post_send_callback(self, callback: Callable, cog_name: str = "Unknown", priority: int = 0, timeout: float = 10.0) -> bool:
        """
        Register a callback to run after the message is sent.
        
        Args:
            callback: Async function with signature (guild, aircraft_info, squawk_code, sent_message)
            cog_name: Name of the registering cog
            priority: Higher priority callbacks run first
            timeout: Max execution time in seconds
            
        Returns:
            bool: True if registered successfully
        """
        if self._is_callback_registered(callback, self._post_send_callbacks):
            log.warning(f"Post-send callback from {cog_name} already registered")
            return False
            
        callback_info = CallbackInfo(
            callback=callback,
            cog_name=cog_name,
            priority=priority,
            timeout=timeout
        )
        
        self._post_send_callbacks.append(callback_info)
        self._post_send_callbacks.sort(key=lambda x: x.priority, reverse=True)
        
        log.info(f"Registered post-send callback from {cog_name} (priority: {priority})")
        return True

    def unregister_callback(self, callback: Callable, callback_type: str = "all") -> bool:
        """
        Unregister a callback.
        
        Args:
            callback: The callback function to unregister
            callback_type: "basic", "pre_send", "post_send", or "all"
            
        Returns:
            bool: True if any callbacks were removed
        """
        removed = False
        
        if callback_type in ("basic", "all"):
            removed |= self._remove_callback_from_list(callback, self._callbacks)
            
        if callback_type in ("pre_send", "all"):
            removed |= self._remove_callback_from_list(callback, self._pre_send_callbacks)
            
        if callback_type in ("post_send", "all"):
            removed |= self._remove_callback_from_list(callback, self._post_send_callbacks)
            
        if removed:
            log.info(f"Unregistered callback ({callback_type})")
            
        return removed

    async def call_callbacks(self, guild, aircraft_info, squawk_code) -> Dict[str, Any]:
        """
        Call all registered basic callbacks with deduplication and error handling.
        
        Returns:
            Dict with execution results and metrics
        """
        alert_key = f"{guild.id}_{aircraft_info.get('hex')}_{squawk_code}"
        
        # Check for duplicate alerts
        async with self._lock:
            now = time.time()
            if alert_key in self._recent_alerts:
                time_since_last = now - self._recent_alerts[alert_key]
                if time_since_last < self._dedup_window:
                    log.debug(f"Skipping duplicate alert for {alert_key} ({time_since_last:.1f}s ago)")
                    return {"skipped": True, "reason": "duplicate", "time_since_last": time_since_last}
            
            self._recent_alerts[alert_key] = now
            self._cleanup_old_alerts(now)
        
        # Execute callbacks
        results = await self._execute_callbacks(
            self._callbacks, 
            "basic_callback",
            guild, aircraft_info, squawk_code
        )
        
        self._metrics['total_calls'] += 1
        if results['success_count'] > 0:
            self._metrics['successful_calls'] += 1
        if results['error_count'] > 0:
            self._metrics['failed_calls'] += 1
            
        return results

    async def run_pre_send(self, guild, aircraft_info, squawk_code, message_data: Dict) -> Dict:
        """Run pre-send callbacks to modify message data."""
        results = await self._execute_callbacks(
            self._pre_send_callbacks,
            "pre_send_callback", 
            guild, aircraft_info, squawk_code, message_data
        )
        
        # Apply modifications from successful callbacks
        for result in results['callback_results']:
            if result['success'] and result['return_value']:
                message_data.update(result['return_value'])
                
        return message_data

    async def run_post_send(self, guild, aircraft_info, squawk_code, sent_message):
        """Run post-send callbacks after message is sent."""
        return await self._execute_callbacks(
            self._post_send_callbacks,
            "post_send_callback",
            guild, aircraft_info, squawk_code, sent_message
        )

    async def _execute_callbacks(self, callback_list: List[CallbackInfo], callback_type: str, *args) -> Dict[str, Any]:
        """Execute a list of callbacks with error handling and metrics."""
        start_time = time.time()
        results = {
            'callback_type': callback_type,
            'total_callbacks': len(callback_list),
            'success_count': 0,
            'error_count': 0,
            'disabled_count': 0,
            'execution_time': 0.0,
            'callback_results': []
        }
        
        for callback_info in callback_list:
            if not callback_info.enabled:
                results['disabled_count'] += 1
                continue
                
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

    async def _handle_callback_failure(self, callback_info: CallbackInfo, error_msg: str):
        """Handle callback failure with circuit breaker logic."""
        callback_info.failure_count += 1
        callback_info.last_failure = time.time()
        
        log.error(f"Callback failure in {callback_info.cog_name}: {error_msg}")
        
        if callback_info.failure_count >= callback_info.max_failures:
            callback_info.enabled = False
            log.error(f"Disabled callback from {callback_info.cog_name} after {callback_info.failure_count} failures")

    def _is_callback_registered(self, callback: Callable, callback_list: List[CallbackInfo]) -> bool:
        """Check if a callback is already registered."""
        return any(cb.callback == callback for cb in callback_list)

    def _remove_callback_from_list(self, callback: Callable, callback_list: List[CallbackInfo]) -> bool:
        """Remove a callback from a list."""
        original_length = len(callback_list)
        callback_list[:] = [cb for cb in callback_list if cb.callback != callback]
        return len(callback_list) < original_length

    def _cleanup_old_alerts(self, current_time: float):
        """Remove old alert entries to prevent memory leaks."""
        cutoff_time = current_time - (self._dedup_window * 2)  # Keep 2x window for safety
        self._recent_alerts = {
            k: v for k, v in self._recent_alerts.items() 
            if v > cutoff_time
        }

    def get_stats(self) -> Dict[str, Any]:
        """Get API usage statistics."""
        return {
            'total_callbacks': len(self._callbacks) + len(self._pre_send_callbacks) + len(self._post_send_callbacks),
            'basic_callbacks': len(self._callbacks),
            'pre_send_callbacks': len(self._pre_send_callbacks),
            'post_send_callbacks': len(self._post_send_callbacks),
            'enabled_callbacks': sum(1 for cb in self._callbacks + self._pre_send_callbacks + self._post_send_callbacks if cb.enabled),
            'recent_alerts_tracked': len(self._recent_alerts),
            'metrics': self._metrics.copy(),
            'callback_details': [
                {
                    'cog_name': cb.cog_name,
                    'priority': cb.priority,
                    'enabled': cb.enabled,
                    'failure_count': cb.failure_count,
                    'registered_at': cb.registered_at
                }
                for cb in self._callbacks + self._pre_send_callbacks + self._post_send_callbacks
            ]
        }

    def enable_callback(self, cog_name: str) -> bool:
        """Re-enable callbacks from a specific cog."""
        enabled_any = False
        for callback_list in [self._callbacks, self._pre_send_callbacks, self._post_send_callbacks]:
            for cb in callback_list:
                if cb.cog_name == cog_name and not cb.enabled:
                    cb.enabled = True
                    cb.failure_count = 0
                    enabled_any = True
                    
        if enabled_any:
            log.info(f"Re-enabled callbacks from {cog_name}")
            
        return enabled_any

    def set_dedup_window(self, seconds: float):
        """Set the deduplication window in seconds."""
        if seconds < 1.0 or seconds > 300.0:
            raise ValueError("Deduplication window must be between 1 and 300 seconds")
        self._dedup_window = seconds
        log.info(f"Set deduplication window to {seconds}s") 