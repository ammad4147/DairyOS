"""
Input manager for DairyOS.

This module manages multiple input modules, handles their lifecycle,
and provides a unified interface for data collection and event handling.
"""

from typing import Dict, List, Optional, Callable, Any
from dataclasses import dataclass
import asyncio
from datetime import datetime
from collections import deque
import logging
import yaml
import os
import time
from enum import Enum

from .module import InputModule, InputData, InputError, InputStatus, DataQuality, HealthReport


logger = logging.getLogger(__name__)


class ReconnectStrategy(Enum):
    """Enumeration of reconnect strategies."""
    LINEAR = "linear"
    EXPONENTIAL = "exponential"


@dataclass
class ModuleConfig:
    """Configuration for a module in the manager."""
    module_id: str
    module_class: type
    config: Optional[Dict[str, Any]] = None
    polling_interval: float = 1.0  # seconds
    is_active: bool = True
    calibration_offset: Optional[float] = None
    connection_params: Optional[Dict[str, Any]] = None
    max_reconnect_attempts: int = 5
    reconnect_strategy: ReconnectStrategy = ReconnectStrategy.EXPONENTIAL
    reconnect_base_delay: float = 1.0  # seconds
    offline_buffer_size: int = 1000
    watchdog_timeout: float = 30.0  # seconds


class InputManager:
    """
    Manager for input modules in DairyOS.
    
    This class handles registration, lifecycle management, and polling
    of multiple input modules. It provides buffering of recent readings
    and handles offline/reconnect logic.
    """
    
    def __init__(self, config_file: Optional[str] = None):
        """Initialize the input manager."""
        self._modules: Dict[str, InputModule] = {}
        self._module_configs: Dict[str, ModuleConfig] = {}
        self._polling_tasks: Dict[str, asyncio.Task] = {}
        self._buffer_size = 100
        self._data_buffer: Dict[str, deque] = {}
        self._error_buffer: Dict[str, deque] = {}
        self._offline_buffer: Dict[str, deque] = {}
        self._on_data_callbacks: List[Callable[[InputData], None]] = []
        self._on_error_callbacks: List[Callable[[InputError], None]] = []
        self._on_status_change_callbacks: List[Callable[[str, InputStatus], None]] = []
        self._on_health_change_callbacks: List[Callable[[HealthReport], None]] = []
        self._config_file = config_file
        self._watchdog_tasks: Dict[str, asyncio.Task] = {}
        
        # Event loop for async operations
        self._loop = asyncio.get_event_loop()
        
        # Load configuration if provided
        if config_file and os.path.exists(config_file):
            self._load_config(config_file)
    
    def _load_config(self, config_file: str) -> None:
        """
        Load configuration from YAML file.
        
        Args:
            config_file: Path to the YAML configuration file
        """
        try:
            with open(config_file, 'r') as file:
                config_data = yaml.safe_load(file) or {}
            
            # Process module configurations
            modules_config = config_data.get('modules', {})
            for module_id, module_data in modules_config.items():
                # Create ModuleConfig from YAML data
                config = ModuleConfig(
                    module_id=module_id,
                    module_class=module_data.get('module_class'),
                    config=module_data.get('config'),
                    polling_interval=module_data.get('polling_interval', 1.0),
                    is_active=module_data.get('is_active', True),
                    calibration_offset=module_data.get('calibration_offset'),
                    connection_params=module_data.get('connection_params'),
                    max_reconnect_attempts=module_data.get('max_reconnect_attempts', 5),
                    reconnect_strategy=ReconnectStrategy(module_data.get('reconnect_strategy', 'exponential')),
                    reconnect_base_delay=module_data.get('reconnect_base_delay', 1.0),
                    offline_buffer_size=module_data.get('offline_buffer_size', 1000),
                    watchdog_timeout=module_data.get('watchdog_timeout', 30.0)
                )
                
                # Register the module
                self.register_module(config)
                
            logger.info(f"Loaded configuration from {config_file}")
            
        except Exception as e:
            logger.error(f"Failed to load configuration from {config_file}: {e}")
    
    def register_module(self, config: ModuleConfig) -> None:
        """
        Register a new input module with the manager.
        
        Args:
            config: Configuration for the module to register
        """
        module = config.module_class(config.module_id, config.config)
        self._modules[config.module_id] = module
        self._module_configs[config.module_id] = config
        self._data_buffer[config.module_id] = deque(maxlen=config.offline_buffer_size)
        self._error_buffer[config.module_id] = deque(maxlen=100)
        self._offline_buffer[config.module_id] = deque(maxlen=config.offline_buffer_size)
        
        logger.info(f"Registered input module: {config.module_id}")
        
        # Start watchdog for this module
        if config.is_active:
            self._start_watchdog(config.module_id)
    
    def unregister_module(self, module_id: str) -> None:
        """
        Unregister an input module from the manager.
        
        Args:
            module_id: ID of the module to unregister
        """
        if module_id in self._modules:
            # Cancel any running polling task
            if module_id in self._polling_tasks:
                self._polling_tasks[module_id].cancel()
                del self._polling_tasks[module_id]
            
            # Cancel watchdog task
            if module_id in self._watchdog_tasks:
                self._watchdog_tasks[module_id].cancel()
                del self._watchdog_tasks[module_id]
            
            # Remove from all collections
            del self._modules[module_id]
            del self._module_configs[module_id]
            del self._data_buffer[module_id]
            del self._error_buffer[module_id]
            del self._offline_buffer[module_id]
            
            logger.info(f"Unregistered input module: {module_id}")
    
    async def start_all(self) -> None:
        """
        Start all registered input modules.
        
        This will connect and begin polling all active modules.
        """
        tasks = []
        for module_id, config in self._module_configs.items():
            if config.is_active:
                task = self._start_module(module_id)
                tasks.append(task)
        
        # Run all start tasks concurrently
        await asyncio.gather(*tasks, return_exceptions=True)
    
    async def stop_all(self) -> None:
        """
        Stop all registered input modules.
        
        This will disconnect all modules and cancel polling tasks.
        """
        tasks = []
        for module_id in list(self._modules.keys()):
            task = self._stop_module(module_id)
            tasks.append(task)
        
        # Run all stop tasks concurrently
        await asyncio.gather(*tasks, return_exceptions=True)
    
    async def _start_module(self, module_id: str) -> None:
        """
        Start a specific module.
        
        Args:
            module_id: ID of the module to start
        """
        try:
            module = self._modules[module_id]
            await module.start()
            
            # Set up polling if this is an active module
            config = self._module_configs[module_id]
            if config.is_active and config.polling_interval > 0:
                task = self._loop.create_task(self._poll_module(module_id))
                self._polling_tasks[module_id] = task
                
            logger.info(f"Started input module: {module_id}")
        except Exception as e:
            logger.error(f"Failed to start module {module_id}: {e}")
            self._handle_module_error(module_id, str(e))
    
    async def _stop_module(self, module_id: str) -> None:
        """
        Stop a specific module.
        
        Args:
            module_id: ID of the module to stop
        """
        try:
            module = self._modules[module_id]
            await module.stop()
            
            # Cancel polling task if exists
            if module_id in self._polling_tasks:
                self._polling_tasks[module_id].cancel()
                del self._polling_tasks[module_id]
                
            logger.info(f"Stopped input module: {module_id}")
        except Exception as e:
            logger.error(f"Failed to stop module {module_id}: {e}")
    
    async def _poll_module(self, module_id: str) -> None:
        """
        Poll a specific module on a schedule.
        
        Args:
            module_id: ID of the module to poll
        """
        config = self._module_configs[module_id]
        module = self._modules[module_id]
        
        # Track reconnect attempts
        reconnect_attempts = 0
        last_reconnect_time = 0
        
        while module.is_running:
            try:
                # Poll the module
                data = await module.poll()
                
                if data:
                    # Store in buffer
                    self._data_buffer[module_id].append(data)
                    
                    # Emit data event
                    self._emit_data_event(data)
                    
                    # Reset reconnect attempts on success
                    reconnect_attempts = 0
                else:
                    # Handle polling failure
                    logger.warning(f"Failed to poll module {module_id}")
                    
                    # Handle reconnection logic
                    if config.reconnect_strategy == ReconnectStrategy.EXPONENTIAL:
                        # Exponential backoff
                        delay = config.reconnect_base_delay * (2 ** reconnect_attempts)
                    else:
                        # Linear backoff
                        delay = config.reconnect_base_delay * reconnect_attempts
                    
                    # Limit maximum delay
                    delay = min(delay, 60.0)
                    
                    # Check if we should attempt reconnection
                    current_time = time.time()
                    if (current_time - last_reconnect_time) > delay and reconnect_attempts < config.max_reconnect_attempts:
                        logger.info(f"Attempting to reconnect to module {module_id} (attempt {reconnect_attempts + 1})")
                        last_reconnect_time = current_time
                        reconnect_attempts += 1
                        
                        # Try to reconnect
                        if await module.connect():
                            logger.info(f"Successfully reconnected to module {module_id}")
                            reconnect_attempts = 0
                        else:
                            logger.warning(f"Failed to reconnect to module {module_id}")
                    
                    # Store in offline buffer for later processing
                    self._store_offline_data(module_id)
                
                # Wait for next poll
                await asyncio.sleep(config.polling_interval)
                
            except asyncio.CancelledError:
                # Task was cancelled, exit gracefully
                break
            except Exception as e:
                # Handle unexpected errors
                logger.error(f"Error polling module {module_id}: {e}")
                self._handle_module_error(module_id, str(e))
                # Continue polling even after errors
                await asyncio.sleep(config.polling_interval)
    
    def _store_offline_data(self, module_id: str) -> None:
        """
        Store data in offline buffer when network/DB is down.
        
        Args:
            module_id: ID of the module
        """
        # This is a placeholder - in a real implementation, 
        # this would store data to persistent storage
        pass
    
    def _start_watchdog(self, module_id: str) -> None:
        """
        Start a watchdog task for a module.
        
        Args:
            module_id: ID of the module to watch
        """
        if module_id in self._watchdog_tasks:
            self._watchdog_tasks[module_id].cancel()
        
        task = self._loop.create_task(self._watchdog_loop(module_id))
        self._watchdog_tasks[module_id] = task
    
    async def _watchdog_loop(self, module_id: str) -> None:
        """
        Watchdog loop to monitor module health.
        
        Args:
            module_id: ID of the module to watch
        """
        config = self._module_configs[module_id]
        
        while True:
            try:
                # Check if module is still alive
                module = self._modules[module_id]
                current_time = datetime.now()
                
                # Check if module has timed out
                if (current_time - module.health_report.last_seen).total_seconds() > config.watchdog_timeout:
                    # Module is dead - update status
                    if module.status != InputStatus.OFFLINE:
                        old_status = module.status
                        module.status = InputStatus.OFFLINE
                        logger.warning(f"Module {module_id} is offline")
                        self._emit_status_change_event(module_id, InputStatus.OFFLINE)
                        self._emit_health_change_event(module.health_report)
                
                # Check health periodically
                if module.is_running:
                    health = await module.health_check()
                    logger.debug(f"Health check for {module_id}: {health}")
                
                # Wait before next check
                await asyncio.sleep(config.watchdog_timeout / 2)
                
            except asyncio.CancelledError:
                # Task was cancelled, exit gracefully
                break
            except Exception as e:
                logger.error(f"Error in watchdog for module {module_id}: {e}")
                await asyncio.sleep(1)
    
    def _handle_module_error(self, module_id: str, error: str) -> None:
        """
        Handle an error from a module.
        
        Args:
            module_id: ID of the module that errored
            error: Error message
        """
        error_obj = InputError(
            module_id=module_id,
            error=error,
            timestamp=datetime.now()
        )
        
        # Store in buffer
        self._error_buffer[module_id].append(error_obj)
        
        # Emit error event
        self._emit_error_event(error_obj)
    
    def add_data_callback(self, callback: Callable[[InputData], None]) -> None:
        """
        Add a callback for data events.
        
        Args:
            callback: Function to call when data is received
        """
        self._on_data_callbacks.append(callback)
    
    def add_error_callback(self, callback: Callable[[InputError], None]) -> None:
        """
        Add a callback for error events.
        
        Args:
            callback: Function to call when an error occurs
        """
        self._on_error_callbacks.append(callback)
    
    def add_status_change_callback(self, callback: Callable[[str, InputStatus], None]) -> None:
        """
        Add a callback for status change events.
        
        Args:
            callback: Function to call when module status changes
        """
        self._on_status_change_callbacks.append(callback)
    
    def add_health_change_callback(self, callback: Callable[[HealthReport], None]) -> None:
        """
        Add a callback for health change events.
        
        Args:
            callback: Function to call when module health changes
        """
        self._on_health_change_callbacks.append(callback)
    
    def _emit_data_event(self, data: InputData) -> None:
        """
        Emit a data event to all registered callbacks.
        
        Args:
            data: Data that was received
        """
        for callback in self._on_data_callbacks:
            try:
                callback(data)
            except Exception as e:
                logger.error(f"Error in data callback: {e}")
    
    def _emit_error_event(self, error: InputError) -> None:
        """
        Emit an error event to all registered callbacks.
        
        Args:
            error: Error that occurred
        """
        for callback in self._on_error_callbacks:
            try:
                callback(error)
            except Exception as e:
                logger.error(f"Error in error callback: {e}")
    
    def _emit_status_change_event(self, module_id: str, status: InputStatus) -> None:
        """
        Emit a status change event to all registered callbacks.
        
        Args:
            module_id: ID of the module whose status changed
            status: New status
        """
        for callback in self._on_status_change_callbacks:
            try:
                callback(module_id, status)
            except Exception as e:
                logger.error(f"Error in status change callback: {e}")
    
    def _emit_health_change_event(self, health_report: HealthReport) -> None:
        """
        Emit a health change event to all registered callbacks.
        
        Args:
            health_report: Health report that changed
        """
        for callback in self._on_health_change_callbacks:
            try:
                callback(health_report)
            except Exception as e:
                logger.error(f"Error in health change callback: {e}")
    
    def get_module_status(self, module_id: str) -> Optional[InputStatus]:
        """
        Get the status of a specific module.
        
        Args:
            module_id: ID of the module
            
        Returns:
            Status of the module, or None if not found
        """
        if module_id in self._modules:
            return self._modules[module_id].status
        return None
    
    def get_module_health(self, module_id: str) -> Optional[HealthReport]:
        """
        Get the health report of a specific module.
        
        Args:
            module_id: ID of the module
            
        Returns:
            Health report of the module, or None if not found
        """
        if module_id in self._modules:
            return self._modules[module_id].health_report
        return None
    
    def get_recent_data(self, module_id: str, count: int = 1) -> List[InputData]:
        """
        Get recent data from a module's buffer.
        
        Args:
            module_id: ID of the module
            count: Number of recent items to retrieve
            
        Returns:
            List of recent data items
        """
        if module_id in self._data_buffer:
            buffer = self._data_buffer[module_id]
            return list(buffer)[-count:] if count > 0 else list(buffer)
        return []
    
    def get_recent_errors(self, module_id: str, count: int = 1) -> List[InputError]:
        """
        Get recent errors from a module's buffer.
        
        Args:
            module_id: ID of the module
            count: Number of recent items to retrieve
            
        Returns:
            List of recent error items
        """
        if module_id in self._error_buffer:
            buffer = self._error_buffer[module_id]
            return list(buffer)[-count:] if count > 0 else list(buffer)
        return []
    
    def get_all_modules(self) -> List[str]:
        """
        Get a list of all registered module IDs.
        
        Returns:
            List of module IDs
        """
        return list(self._modules.keys())
    
    def get_active_modules(self) -> List[str]:
        """
        Get a list of all active module IDs.
        
        Returns:
            List of active module IDs
        """
        return [mid for mid, config in self._module_configs.items() if config.is_active]
    
    def reload_config(self, config_file: str) -> None:
        """
        Reload configuration from a YAML file.
        
        Args:
            config_file: Path to the YAML configuration file
        """
        # Stop all currently running modules
        asyncio.run(self.stop_all())
        
        # Clear existing modules
        self._modules.clear()
        self._module_configs.clear()
        self._data_buffer.clear()
        self._error_buffer.clear()
        self._offline_buffer.clear()
        self._polling_tasks.clear()
        self._watchdog_tasks.clear()
        
        # Load new configuration
        self._load_config(config_file)
        
        # Start all modules
        asyncio.run(self.start_all())
    
    async def calibrate_module(self, module_id: str, calibration_data: Dict[str, Any]) -> bool:
        """
        Perform calibration on a specific module.
        
        Args:
            module_id: ID of the module to calibrate
            calibration_data: Calibration parameters
            
        Returns:
            True if calibration was successful, False otherwise
        """
        if module_id in self._modules:
            try:
                result = await self._modules[module_id].calibrate(calibration_data)
                if result:
                    logger.info(f"Successfully calibrated module {module_id}")
                else:
                    logger.warning(f"Failed to calibrate module {module_id}")
                return result
            except Exception as e:
                logger.error(f"Error during calibration of module {module_id}: {e}")
                return False
        return False
