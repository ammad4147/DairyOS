"""
Test file for the input system in DairyOS.

This file demonstrates how to use the input system components.
"""

import asyncio
from datetime import datetime
from typing import Any

from .manager import InputManager, ModuleConfig
from .example_module import ExampleInputModule
from .module import InputData, InputError


async def test_input_system():
    """Test the input system components."""
    print("Testing DairyOS Input System")
    print("=" * 40)
    
    # Create input manager
    manager = InputManager()
    
    # Register some example modules
    config1 = ModuleConfig(
        module_id="sensor_001",
        module_class=ExampleInputModule,
        config={"data_source": "temperature_sensor", "error_rate": 0.05},
        polling_interval=2.0,
        is_active=True
    )
    
    config2 = ModuleConfig(
        module_id="sensor_002",
        module_class=ExampleInputModule,
        config={"data_source": "humidity_sensor", "error_rate": 0.1},
        polling_interval=3.0,
        is_active=True
    )
    
    manager.register_module(config1)
    manager.register_module(config2)
    
    # Add event callbacks
    def on_data_received(data: InputData):
        print(f"Received data from {data.module_id}: {data.data}")
    
    def on_error_received(error: InputError):
        print(f"Error from {error.module_id}: {error.error}")
    
    def on_status_change(module_id: str, status: Any):
        print(f"Status change for {module_id}: {status.value}")
    
    manager.add_data_callback(on_data_received)
    manager.add_error_callback(on_error_received)
    manager.add_status_change_callback(on_status_change)
    
    # Start all modules
    print("Starting all modules...")
    await manager.start_all()
    
    # Let them run for a while
    print("Running for 10 seconds...")
    await asyncio.sleep(10)
    
    # Get recent data
    print("\nRecent data from sensor_001:")
    recent_data = manager.get_recent_data("sensor_001", 3)
    for data in recent_data:
        print(f"  {data.data}")
    
    # Get recent errors
    print("\nRecent errors from sensor_002:")
    recent_errors = manager.get_recent_errors("sensor_002", 3)
    for error in recent_errors:
        print(f"  {error.error}")
    
    # Stop all modules
    print("\nStopping all modules...")
    await manager.stop_all()
    
    print("\nTest completed!")


if __name__ == "__main__":
    asyncio.run(test_input_system())
