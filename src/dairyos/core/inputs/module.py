"""
Input module base class for DairyOS.

This module defines the interface for all input modules in the system.
"""

from abc import ABC, abstractmethod
from typing import Any, Optional, Dict, List
from enum import Enum
import asyncio
from dataclasses import dataclass
from datetime import datetime
import time


class InputStatus(Enum):
    """Enumeration of input module statuses."""
    IDLE = "idle"
    CONNECTED = "connected"
    DISCONNECTED = "disconnected"
    ERROR = "error"
    OFFLINE = "offline"


class DataQuality(Enum):
    """Enumeration of data quality flags."""
    GOOD = "good"
    SUSPECT = "suspect"
    INVALID = "invalid"


@dataclass
class InputData:
    """Represents input data from a module."""
    module_id: str
    data: Any
    timestamp: datetime
    quality: DataQuality = DataQuality.GOOD
    metadata: Optional[Dict[str, Any]] = None


@dataclass
class InputError:
    """Represents an error from an input module."""
    module_id: str
    error: str
    timestamp: datetime
    details: Optional[Dict[str, Any]] = None


@dataclass
class HealthReport:
    """Represents health status of an input module."""
    module_id: str
    status: InputStatus
    last_seen: datetime
    connection_attempts: int
    consecutive_failures: int
    uptime: float
    last_error: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


class InputModule(ABC):
    """
    Abstract base class for all input modules in DairyOS.
    
    This class defines the standard interface that all input modules must implement.
    It supports both synchronous and asynchronous operations and provides
    standardized event handling.
    """
    
    def __init__(self, module_id: str, config: Optional[Dict[str, Any]] = None):
        """
        Initialize the input module.
        
        Args:
            module_id: Unique identifier for this module
            config: Configuration parameters for the module
        """
        self.module_id = module_id
        self.config = config or {}
        self._status = InputStatus.IDLE
        self._is_running = False
        self._connection_attempts = 0
        self._consecutive_failures = 0
        self._last_seen = datetime.now()
        self._start_time = datetime.now()
        self._last_error = None
        
    @abstractmethod
    async def connect(self) -> bool:
        """
        Establish connection to the input source.
        
        Returns:
            True if connection was successful, False otherwise
        """
        pass
    
    @abstractmethod
    async def disconnect(self) -> bool:
        """
        Close connection to the input source.
        
        Returns:
            True if disconnection was successful, False otherwise
        """
        pass
    
    @abstractmethod
    async def read(self) -> Any:
        """
        Read data from the input source.
        
        Returns:
            The data read from the source
        """
        pass
    
    @abstractmethod
    async def validate(self, data: Any) -> bool:
        """
        Validate the input data.
        
        Args:
            data: Data to validate
            
        Returns:
            True if data is valid, False otherwise
        """
        pass
    
    @abstractmethod
    async def health_check(self) -> Dict[str, Any]:
        """
        Perform a health check on the input module.
        
        Returns:
            Dictionary containing health status information
        """
        pass
    
    @property
    def status(self) -> InputStatus:
        """Get the current status of the module."""
        return self._status
    
    @status.setter
    def status(self, value: InputStatus) -> None:
        """Set the status of the module."""
        self._status = value
    
    @property
    def is_running(self) -> bool:
        """Check if the module is currently running."""
        return self._is_running
    
    @property
    def health_report(self) -> HealthReport:
        """Get the current health report for this module."""
        return HealthReport(
            module_id=self.module_id,
            status=self._status,
            last_seen=self._last_seen,
            connection_attempts=self._connection_attempts,
            consecutive_failures=self._consecutive_failures,
            uptime=(datetime.now() - self._start_time).total_seconds(),
            last_error=self._last_error
        )
    
    async def start(self) -> None:
        """Start the input module."""
        self._is_running = True
        await self.connect()
    
    async def stop(self) -> None:
        """Stop the input module."""
        self._is_running = False
        await self.disconnect()
    
    async def poll(self) -> Optional[InputData]:
        """
        Perform a complete polling cycle.
        
        Returns:
            InputData object if successful, None if failed
        """
        try:
            if not self._is_running:
                return None
                
            data = await self.read()
            is_valid = await self.validate(data)
            
            # Determine quality based on validation result
            quality = DataQuality.GOOD if is_valid else DataQuality.INVALID
            
            # If validation failed, we might still want to return the data with suspect quality
            if not is_valid:
                quality = DataQuality.SUSPECT
            
            result = InputData(
                module_id=self.module_id,
                data=data,
                timestamp=datetime.now(),
                quality=quality
            )
            
            # Update health tracking
            self._last_seen = datetime.now()
            self._consecutive_failures = 0
            self._last_error = None
            
            return result
            
        except Exception as e:
            # Handle read error
            self._consecutive_failures += 1
            self._last_error = str(e)
            self.status = InputStatus.ERROR
            return None
    
    async def calibrate(self, calibration_data: Dict[str, Any]) -> bool:
        """
        Perform a calibration routine for this module.
        
        Args:
            calibration_data: Calibration parameters
            
        Returns:
            True if calibration was successful, False otherwise
        """
        try:
            # This is a placeholder for actual calibration logic
            # Each module implementation can override this with specific calibration logic
            return True
        except Exception as e:
            self._last_error = str(e)
            return False
