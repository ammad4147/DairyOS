"""
Dashboard renderer for DairyOS.

This module provides a more comprehensive dashboard renderer
that integrates with existing modules and data sources.
"""

from typing import Any

from src.dairyos.core.inputs.manager import InputManager
from src.dairyos.herd.dashboard.components.dashboard import DashboardRenderer


class DashboardService:
    """Service for generating dashboard data from existing modules."""
    
    def __init__(self, input_manager: InputManager):
        """
        Initialize the dashboard service.
        
        Args:
            input_manager: Input manager for accessing sensor data
        """
        self.input_manager = input_manager
        self.renderer = DashboardRenderer()
    
    async def generate_dashboard_data(self) -> dict[str, Any]:
        """
        Generate complete dashboard data from all available sources.
        
        Returns:
            Dictionary containing all dashboard data
        """
        # Get basic farm data
        farm_data = await self._get_farm_data()
        
        # Get sensor data
        sensor_data = await self._get_sensor_data()
        
        # Get alerts
        alerts = await self._get_alerts()
        
        # Get production history
        production_history = await self._get_production_history()
        
        # Get health history
        health_history = await self._get_health_history()
        
        # Combine all data
        dashboard_data = {
            **farm_data,
            'sensors': sensor_data,
            'alerts': alerts,
            'production_history': production_history,
            'health_history': health_history
        }
        
        return dashboard_data
    
    async def _get_farm_data(self) -> dict[str, Any]:
        """Get basic farm data."""
        # This would typically come from inventory, health, and operations modules
        # For now, we'll simulate some data
        
        return {
            'total_animals': 120,
            'healthy_animals': 115,
            'milk_yield_today': 1250.5,
            'average_yield': 1100.0,
            'active_alerts': 3,
            'system_health': 'good'
        }
    
    async def _get_sensor_data(self) -> list[dict[str, Any]]:
        """Get sensor data from input modules."""
        sensors = []
        
        # Get data from all active modules
        active_modules = self.input_manager.get_active_modules()
        
        for module_id in active_modules:
            try:
                # Get recent data from module
                recent_data = self.input_manager.get_recent_data(module_id, 1)
                
                if recent_data:
                    data = recent_data[0]
                    sensors.append({
                        'name': module_id.replace('_', ' ').title(),
                        'value': data.data.get('value', 0),
                        'unit': data.data.get('unit', ''),
                        'location': data.data.get('source', ''),
                        'warning_threshold': 50,
                        'critical_threshold': 80
                    })
            except Exception as e:
                # Log error but continue
                print(f"Error getting sensor data for {module_id}: {e}")
        
        return sensors
    
    async def _get_alerts(self) -> list[dict[str, Any]]:
        """Get recent alerts."""
        # This would typically come from alerting systems
        # For now, we'll simulate some alerts
        
        return [
            {
                'title': 'Temperature Alert',
                'description': 'Temperature in barn 3 above threshold',
                'timestamp': '2023-05-15 08:30',
                'source': 'Temperature Sensor',
                'severity': 'high'
            },
            {
                'title': 'Milk Quality Issue',
                'description': 'Milk fat content below target',
                'timestamp': '2023-05-15 07:15',
                'source': 'Milk Analyzer',
                'severity': 'medium'
            },
            {
                'title': 'Equipment Maintenance',
                'description': 'Milking machine requires service',
                'timestamp': '2023-05-14 16:45',
                'source': 'Equipment Monitor',
                'severity': 'low'
            }
        ]
    
    async def _get_production_history(self) -> list[dict[str, Any]]:
        """Get milk production history."""
        # Simulate production history data
        return [
            {'date': 'Mon', 'yield': 1100},
            {'date': 'Tue', 'yield': 1250},
            {'date': 'Wed', 'yield': 1180},
            {'date': 'Thu', 'yield': 1320},
            {'date': 'Fri', 'yield': 1280},
            {'date': 'Sat', 'yield': 1400},
            {'date': 'Sun', 'yield': 1250}
        ]
    
    async def _get_health_history(self) -> list[dict[str, Any]]:
        """Get herd health history."""
        # Simulate health history data
        return [
            {'date': 'Mon', 'healthy_count': 115},
            {'date': 'Tue', 'healthy_count': 118},
            {'date': 'Wed', 'healthy_count': 116},
            {'date': 'Thu', 'healthy_count': 119},
            {'date': 'Fri', 'healthy_count': 120},
            {'date': 'Sat', 'healthy_count': 120},
            {'date': 'Sun', 'healthy_count': 118}
        ]
    
    def render_dashboard(self, dashboard_data: dict[str, Any]) -> str:
        """
        Render the dashboard as HTML.
        
        Args:
            dashboard_data: Dashboard data to render
            
        Returns:
            HTML string for the dashboard
        """
        return self.renderer.render_dashboard_html(dashboard_data)
    
    async def get_dashboard_html(self) -> str:
        """
        Get complete dashboard HTML.
        
        Returns:
            HTML string for the dashboard
        """
        dashboard_data = await self.generate_dashboard_data()
        return self.render_dashboard(dashboard_data)
    
    def get_health_status_color(self, health: str) -> str:
        """
        Get color for health status.
        
        Args:
            health: Health status string
            
        Returns:
            CSS color value
        """
        colors = {
            "good": "#4CAF50",
            "warning": "#FF9800",
            "critical": "#F44336"
        }
        return colors.get(health, "#9E9E9E")
    
    def get_severity_color(self, severity: str) -> str:
        """
        Get color for severity.
        
        Args:
            severity: Severity string
            
        Returns:
            CSS color value
        """
        colors = {
            "low": "#4CAF50",
            "medium": "#FF9800",
            "high": "#FF5722",
            "critical": "#F44336"
        }
        return colors.get(severity, "#9E9E9E")
    
    def get_status_indicator(self, status: str) -> str:
        """
        Get status indicator HTML.
        
        Args:
            status: Status string
            
        Returns:
            HTML for status indicator
        """
        status_colors = {
            "success": "status-success",
            "warning": "status-warning", 
            "critical": "status-critical",
            "normal": "status-normal"
        }
        
        color_class = status_colors.get(status, "status-normal")
        return f'<span class="status-indicator {color_class}"></span>'
