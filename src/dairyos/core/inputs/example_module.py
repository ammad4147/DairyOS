"""
Example input module implementation for DairyOS.

This module demonstrates how to implement a concrete input module.
"""

from typing import Any, Dict, Optional
import asyncio
import random
from datetime import datetime
import logging

from .module import InputModule, InputStatus, DataQuality


logger = logging.getLogger(__name__)


class ExampleInputModule(InputModule):
    """
    Example input module that simulates reading data.
    
    This module demonstrates how to implement a concrete input module
    that can be managed by the InputManager.
    """
    
    def __init__(self, module_id: str, config: Optional[Dict[str, Any]] = None):
        """
        Initialize the example input module.
        
        Args:
            module_id: Unique identifier for this module
            config: Configuration parameters for the module
        """
        super().__init__(module_id, config)
        self._connection_status = False
        self._data_source = config.get("data_source", "default")
        self._error_rate = config.get("error_rate", 0.1)
        self._calibration_offset = config.get("calibration_offset", 0.0)
        self._connection_params = config.get("connection_params", {})
        self._last_read_value = 0.0
    
    async def connect(self) -> bool:
        """
        Establish connection to the input source.
        
        Returns:
            True if connection was successful, False otherwise
        """
        try:
            # Simulate connection delay
            await asyncio.sleep(0.1)
            
            # Simulate connection success/failure based on connection params
            if random.random() > self._error_rate:
                self.status = InputStatus.CONNECTED
                self._connection_status = True
                self._connection_attempts += 1
                return True
            else:
                self.status = InputStatus.ERROR
                return False
                
        except Exception as e:
            self.status = InputStatus.ERROR
            self._last_error = str(e)
            return False
    
    async def disconnect(self) -> bool:
        """
        Close connection to the input source.
        
        Returns:
            True if disconnection was successful, False otherwise
        """
        try:
            # Simulate disconnection delay
            await asyncio.sleep(0.1)
            
            self.status = InputStatus.DISCONNECTED
            self._connection_status = False
            return True
            
        except Exception as e:
            self.status = InputStatus.ERROR
            self._last_error = str(e)
            return False
    
    async def read(self) -> Any:
        """
        Read data from the input source.
        
        Returns:
            The data read from the source
        """
        if not self._connection_status:
            raise Exception("Not connected to data source")
        
        # Simulate reading data
        await asyncio.sleep(0.05)
        
        # Generate some example data
        raw_value = random.uniform(0, 100)
        # Apply calibration offset
        calibrated_value = raw_value + self._calibration_offset
        
        # Add some noise to simulate real sensor behavior
        noise = random.uniform(-2, 2)
        final_value = calibrated_value + noise
        
        # Store last read value for potential calibration
        self._last_read_value = final_value
        
        data = {
            "timestamp": datetime.now().isoformat(),
            "source": self._data_source,
            "value": final_value,
            "unit": "units",
            "raw_value": raw_value,
            "calibration_offset": self._calibration_offset,
            "noise": noise
        }
        
        # Occasionally simulate an error
        if random.random() < self._error_rate:
            raise Exception("Simulated data reading error")
        
        return data
    
    async def validate(self, data: Any) -> bool:
        """
        Validate the input data.
        
        Args:
            data: Data to validate
            
        Returns:
            True if data is valid, False otherwise
        """
        try:
            # Simple validation - check if data is a dict with required fields
            if not isinstance(data, dict):
                return False
            
            required_fields = ["timestamp", "source", "value"]
            for field in required_fields:
                if field not in data:
                    return False
            
            # Validate value is numeric
            if not isinstance(data["value"], (int, float)):
                return False
            
            # Validate value is within reasonable range for dairy farm sensors
            if data["value"] < -100 or data["value"] > 200:
                return False
            
            return True
            
        except Exception:
            return False
    
    async def health_check(self) -> Dict[str, Any]:
        """
        Perform a health check on the input module.
        
        Returns:
            Dictionary containing health status information
        """
        return {
            "module_id": self.module_id,
            "status": self.status.value,
            "connection_status": self._connection_status,
            "data_source": self._data_source,
            "error_rate": self._error_rate,
            "calibration_offset": self._calibration_offset,
            "connection_params": self._connection_params,
            "timestamp": datetime.now().isoformat(),
            "last_read_value": self._last_read_value
        }
    
    async def calibrate(self, calibration_data: Dict[str, Any]) -> bool:
        """
        Perform a calibration routine for this module.
        
        Args:
            calibration_data: Calibration parameters
            
        Returns:
            True if calibration was successful, False otherwise
        """
        try:
            # Simple calibration - adjust offset based on calibration data
            if "offset" in calibration_data:
                self._calibration_offset = calibration_data["offset"]
                logger.info(f"Calibrated {self.module_id} with offset {self._calibration_offset}")
                return True
            
            # If no offset provided, try to determine offset from current reading
            if "reference_value" in calibration_data and "current_value" in calibration_data:
                offset = calibration_data["reference_value"] - self._last_read_value
                self._calibration_offset = offset
                logger.info(f"Calibrated {self.module_id} with offset {self._calibration_offset}")
                return True
            
            return False
            
        except Exception as e:
            self._last_error = str(e)
            return False
