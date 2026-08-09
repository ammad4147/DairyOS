"""
Dashboard component for DairyOS.

This module provides the main dashboard UI components for displaying
farm data in a modern, professional interface.
"""

from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from datetime import datetime
import json

from src.dairyos.herd.dashboard.models import (
    HerdDashboard,
    DailyOperatingBoard,
    IntelligenceBrief,
    ExecutiveAlert,
    AdaptiveLearning,
    DecisionAssistant,
    DecisionOptimization,
    DecisionLearning,
    Advisory,
    Escalation,
    PredictiveSignal,
    IntelligentAlert,
    KnowledgeEntry,
    MonitoringEvent,
    OwnerAction,
)
from src.dairyos.herd.dashboard.models.daily_operating_board import DailyOperatingBoard as DailyOperatingBoardModel
from src.dairyos.herd.dashboard.models.intelligence_brief import IntelligenceBrief as IntelligenceBriefModel
from src.dairyos.herd.dashboard.models.executive_alert import ExecutiveAlert as ExecutiveAlertModel
from src.dairyos.herd.dashboard.models.adaptive_learning import AdaptiveLearning as AdaptiveLearningModel
from src.dairyos.herd.dashboard.models.decision_assistant import DecisionAssistant as DecisionAssistantModel
from src.dairyos.herd.dashboard.models.decision_optimization import DecisionOptimization as DecisionOptimizationModel
from src.dairyos.herd.dashboard.models.decision_learning import DecisionLearning as DecisionLearningModel
from src.dairyos.herd.dashboard.models.advisory import Advisory as AdvisoryModel
from src.dairyos.herd.dashboard.models.escalation import Escalation as EscalationModel
from src.dairyos.herd.dashboard.models.predictive_signal import PredictiveSignal as PredictiveSignalModel
from src.dairyos.herd.dashboard.models.intelligent_alert import IntelligentAlert as IntelligentAlertModel
from src.dairyos.herd.dashboard.models.knowledge_entry import KnowledgeEntry as KnowledgeEntryModel
from src.dairyos.herd.dashboard.models.monitoring_event import MonitoringEvent as MonitoringEventModel
from src.dairyos.herd.dashboard.models.owner_action import OwnerAction as OwnerActionModel


@dataclass
class DashboardCard:
    """Represents a dashboard card with data and styling."""
    title: str
    value: str
    subtitle: Optional[str] = None
    status: str = "normal"  # normal, warning, critical, success
    icon: Optional[str] = None
    trend: Optional[str] = None  # up, down, flat
    data: Optional[Any] = None
    color: Optional[str] = None


@dataclass
class DashboardSummary:
    """Represents the summary section of the dashboard."""
    total_animals: int
    healthy_animals: int
    milk_yield_today: float
    average_yield: float
    active_alerts: int
    system_health: str  # good, warning, critical
    last_update: datetime


class DashboardRenderer:
    """Renders the DairyOS dashboard with modern UI components."""
    
    def __init__(self):
        """Initialize the dashboard renderer."""
        self.cards = []
        self.summary = None
    
    def render_summary(self, dashboard_data: Dict[str, Any]) -> DashboardSummary:
        """
        Render the summary section of the dashboard.
        
        Args:
            dashboard_data: Data for the dashboard
            
        Returns:
            DashboardSummary object with key metrics
        """
        # Extract data from dashboard_data
        total_animals = dashboard_data.get('total_animals', 0)
        healthy_animals = dashboard_data.get('healthy_animals', 0)
        milk_yield_today = dashboard_data.get('milk_yield_today', 0.0)
        average_yield = dashboard_data.get('average_yield', 0.0)
        active_alerts = dashboard_data.get('active_alerts', 0)
        
        # Determine system health based on alerts
        system_health = "good"
        if active_alerts > 5:
            system_health = "critical"
        elif active_alerts > 2:
            system_health = "warning"
        
        return DashboardSummary(
            total_animals=total_animals,
            healthy_animals=healthy_animals,
            milk_yield_today=milk_yield_today,
            average_yield=average_yield,
            active_alerts=active_alerts,
            system_health=system_health,
            last_update=datetime.now()
        )
    
    def render_kpi_cards(self, dashboard_data: Dict[str, Any]) -> List[DashboardCard]:
        """
        Render KPI cards for the dashboard.
        
        Args:
            dashboard_data: Data for the dashboard
            
        Returns:
            List of DashboardCard objects
        """
        cards = []
        
        # Milk yield card
        cards.append(DashboardCard(
            title="Milk Yield Today",
            value=f"{dashboard_data.get('milk_yield_today', 0.0):.1f} L",
            subtitle="vs average",
            status="success",
            icon="milk",
            trend="up" if dashboard_data.get('milk_yield_today', 0) > dashboard_data.get('average_yield', 0) else "down",
            data=dashboard_data.get('milk_yield_today', 0.0)
        ))
        
        # Herd health card
        healthy_percent = (dashboard_data.get('healthy_animals', 0) / max(dashboard_data.get('total_animals', 1), 1)) * 100
        cards.append(DashboardCard(
            title="Herd Health",
            value=f"{healthy_percent:.0f}%",
            subtitle="Healthy animals",
            status="success" if healthy_percent > 85 else "warning",
            icon="health",
            trend="up" if healthy_percent > 85 else "down",
            data=healthy_percent
        ))
        
        # Active alerts card
        cards.append(DashboardCard(
            title="Active Alerts",
            value=str(dashboard_data.get('active_alerts', 0)),
            subtitle="Critical issues",
            status="critical" if dashboard_data.get('active_alerts', 0) > 5 else "warning" if dashboard_data.get('active_alerts', 0) > 2 else "success",
            icon="alert",
            trend="up" if dashboard_data.get('active_alerts', 0) > 2 else "down",
            data=dashboard_data.get('active_alerts', 0)
        ))
        
        # System health card
        system_health = dashboard_data.get('system_health', 'good')
        cards.append(DashboardCard(
            title="System Health",
            value=system_health.title(),
            subtitle="Overall status",
            status="success" if system_health == "good" else "warning" if system_health == "warning" else "critical",
            icon="system",
            data=system_health
        ))
        
        return cards
    
    def render_sensor_cards(self, sensor_data: List[Dict[str, Any]]) -> List[DashboardCard]:
        """
        Render sensor cards for the dashboard.
        
        Args:
            sensor_data: List of sensor data
            
        Returns:
            List of DashboardCard objects for sensors
        """
        cards = []
        
        for sensor in sensor_data:
            status = "success"
            if sensor.get('value', 0) > sensor.get('warning_threshold', 0):
                status = "warning"
            if sensor.get('value', 0) > sensor.get('critical_threshold', 0):
                status = "critical"
            
            cards.append(DashboardCard(
                title=sensor.get('name', 'Sensor'),
                value=f"{sensor.get('value', 0):.1f} {sensor.get('unit', '')}",
                subtitle=sensor.get('location', ''),
                status=status,
                icon="sensor",
                data=sensor
            ))
        
        return cards
    
    def render_alerts_section(self, alerts: List[Dict[str, Any]]) -> List[DashboardCard]:
        """
        Render alerts section for the dashboard.
        
        Args:
            alerts: List of alert data
            
        Returns:
            List of DashboardCard objects for alerts
        """
        cards = []
        
        for alert in alerts[:5]:  # Show top 5 alerts
            status = "critical"
            if alert.get('severity', 'high') == 'medium':
                status = "warning"
            elif alert.get('severity', 'high') == 'low':
                status = "normal"
            
            cards.append(DashboardCard(
                title=alert.get('title', 'Alert'),
                value=alert.get('description', ''),
                subtitle=f"{alert.get('timestamp', '')} - {alert.get('source', '')}",
                status=status,
                icon="alert",
                data=alert
            ))
        
        return cards
    
    def render_production_chart(self, production_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Render production chart data.
        
        Args:
            production_data: Production data for chart
            
        Returns:
            Chart data structure
        """
        return {
            "labels": [day.get('date', '') for day in production_data],
            "datasets": [{
                "label": "Milk Yield",
                "data": [day.get('yield', 0) for day in production_data],
                "backgroundColor": "#4CAF50",
                "borderColor": "#2E7D32",
                "borderWidth": 1
            }]
        }
    
    def render_health_chart(self, health_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Render health chart data.
        
        Args:
            health_data: Health data for chart
            
        Returns:
            Chart data structure
        """
        return {
            "labels": [day.get('date', '') for day in health_data],
            "datasets": [{
                "label": "Healthy Animals",
                "data": [day.get('healthy_count', 0) for day in health_data],
                "backgroundColor": "#2196F3",
                "borderColor": "#0D47A1",
                "borderWidth": 1
            }]
        }
    
    def render_dashboard_html(self, dashboard_data: Dict[str, Any]) -> str:
        """
        Render the complete dashboard as HTML.
        
        Args:
            dashboard_data: Complete dashboard data
            
        Returns:
            HTML string for the dashboard
        """
        summary = self.render_summary(dashboard_data)
        kpi_cards = self.render_kpi_cards(dashboard_data)
        
        # Get sensor data
        sensor_data = dashboard_data.get('sensors', [])
        sensor_cards = self.render_sensor_cards(sensor_data)
        
        # Get alerts
        alerts = dashboard_data.get('alerts', [])
        alert_cards = self.render_alerts_section(alerts)
        
        # Get production data
        production_data = dashboard_data.get('production_history', [])
        production_chart = self.render_production_chart(production_data)
        
        # Get health data
        health_data = dashboard_data.get('health_history', [])
        health_chart = self.render_health_chart(health_data)
        
        # Generate HTML
        html = f"""
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>DairyOS Dashboard</title>
            <link href="https://fonts.googleapis.com/css2?family=Roboto:wght@300;400;500;700&display=swap" rel="stylesheet">
            <style>
                :root {{
                    --primary-color: #2196F3;
                    --success-color: #4CAF50;
                    --warning-color: #FF9800;
                    --critical-color: #F44336;
                    --normal-color: #9E9E9E;
                    --background-color: #f5f7fa;
                    --card-background: #ffffff;
                    --text-primary: #333333;
                    --text-secondary: #666666;
                    --border-color: #e0e0e0;
                    --shadow: 0 2px 10px rgba(0,0,0,0.05);
                    --spacing-xs: 4px;
                    --spacing-sm: 8px;
                    --spacing-md: 16px;
                    --spacing-lg: 24px;
                    --spacing-xl: 32px;
                }}
                
                .dark-mode {{
                    --background-color: #121212;
                    --card-background: #1e1e1e;
                    --text-primary: #ffffff;
                    --text-secondary: #b0b0b0;
                    --border-color: #333333;
                    --shadow: 0 2px 10px rgba(0,0,0,0.3);
                }}
                
                * {{
                    margin: 0;
                    padding: 0;
                    box-sizing: border-box;
                }}
                
                body {{
                    font-family: 'Roboto', sans-serif;
                    background-color: var(--background-color);
                    color: var(--text-primary);
                    line-height: 1.6;
                }}
                
                .dashboard-container {{
                    max-width: 1400px;
                    margin: 0 auto;
                    padding: var(--spacing-md);
                }}
                
                .dashboard-header {{
                    display: flex;
                    justify-content: space-between;
                    align-items: center;
                    margin-bottom: var(--spacing-lg);
                    padding-bottom: var(--spacing-md);
                    border-bottom: 1px solid var(--border-color);
                }}
                
                .dashboard-title {{
                    font-size: 2rem;
                    font-weight: 700;
                }}
                
                .dashboard-subtitle {{
                    font-size: 1rem;
                    color: var(--text-secondary);
                }}
                
                .dashboard-summary {{
                    display: grid;
                    grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
                    gap: var(--spacing-md);
                    margin-bottom: var(--spacing-lg);
                }}
                
                .summary-card {{
                    background: var(--card-background);
                    border-radius: 8px;
                    padding: var(--spacing-md);
                    box-shadow: var(--shadow);
                    display: flex;
                    flex-direction: column;
                    transition: transform 0.2s;
                }}
                
                .summary-card:hover {{
                    transform: translateY(-2px);
                }}
                
                .summary-card-title {{
                    font-size: 0.9rem;
                    color: var(--text-secondary);
                    margin-bottom: var(--spacing-xs);
                }}
                
                .summary-card-value {{
                    font-size: 1.8rem;
                    font-weight: 700;
                    margin-bottom: var(--spacing-xs);
                }}
                
                .summary-card-subtitle {{
                    font-size: 0.9rem;
                    color: var(--text-secondary);
                }}
                
                .dashboard-section {{
                    margin-bottom: var(--spacing-lg);
                }}
                
                .section-title {{
                    font-size: 1.4rem;
                    margin-bottom: var(--spacing-md);
                    display: flex;
                    align-items: center;
                }}
                
                .section-title::before {{
                    content: "";
                    display: inline-block;
                    width: 4px;
                    height: 20px;
                    background: var(--primary-color);
                    margin-right: var(--spacing-sm);
                    border-radius: 2px;
                }}
                
                .cards-grid {{
                    display: grid;
                    grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
                    gap: var(--spacing-md);
                    margin-bottom: var(--spacing-lg);
                }}
                
                .card {{
                    background: var(--card-background);
                    border-radius: 8px;
                    padding: var(--spacing-md);
                    box-shadow: var(--shadow);
                    transition: all 0.3s ease;
                }}
                
                .card:hover {{
                    box-shadow: 0 4px 15px rgba(0,0,0,0.1);
                }}
                
                .card-header {{
                    display: flex;
                    justify-content: space-between;
                    align-items: center;
                    margin-bottom: var(--spacing-md);
                }}
                
                .card-title {{
                    font-size: 1.1rem;
                    font-weight: 500;
                }}
                
                .card-icon {{
                    width: 32px;
                    height: 32px;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    border-radius: 6px;
                    font-size: 1.2rem;
                }}
                
                .card-value {{
                    font-size: 2rem;
                    font-weight: 700;
                    margin-bottom: var(--spacing-sm);
                }}
                
                .card-subtitle {{
                    font-size: 0.9rem;
                    color: var(--text-secondary);
                    margin-bottom: var(--spacing-sm);
                }}
                
                .card-trend {{
                    display: flex;
                    align-items: center;
                    font-size: 0.9rem;
                }}
                
                .trend-up {{
                    color: var(--success-color);
                }}
                
                .trend-down {{
                    color: var(--critical-color);
                }}
                
                .trend-flat {{
                    color: var(--normal-color);
                }}
                
                .chart-container {{
                    background: var(--card-background);
                    border-radius: 8px;
                    padding: var(--spacing-md);
                    box-shadow: var(--shadow);
                    margin-bottom: var(--spacing-lg);
                }}
                
                .chart-title {{
                    font-size: 1.2rem;
                    margin-bottom: var(--spacing-md);
                }}
                
                .chart {{
                    height: 300px;
                    display: flex;
                    align-items: flex-end;
                    gap: 10px;
                    padding: 20px 0;
                }}
                
                .chart-bar {{
                    flex: 1;
                    background: var(--primary-color);
                    border-radius: 4px 4px 0 0;
                    position: relative;
                    min-width: 20px;
                }}
                
                .chart-bar-label {{
                    position: absolute;
                    bottom: -25px;
                    left: 0;
                    right: 0;
                    text-align: center;
                    font-size: 0.8rem;
                    color: var(--text-secondary);
                }}
                
                .chart-bar-value {{
                    position: absolute;
                    top: -25px;
                    left: 0;
                    right: 0;
                    text-align: center;
                    font-size: 0.8rem;
                    font-weight: 500;
                }}
                
                .status-indicator {{
                    display: inline-block;
                    width: 10px;
                    height: 10px;
                    border-radius: 50%;
                    margin-right: var(--spacing-xs);
                }}
                
                .status-success {{
                    background-color: var(--success-color);
                }}
                
                .status-warning {{
                    background-color: var(--warning-color);
                }}
                
                .status-critical {{
                    background-color: var(--critical-color);
                }}
                
                .status-normal {{
                    background-color: var(--normal-color);
                }}
                
                .dark-mode-toggle {{
                    background: var(--card-background);
                    border: 1px solid var(--border-color);
                    border-radius: 20px;
                    padding: 8px 16px;
                    cursor: pointer;
                    display: flex;
                    align-items: center;
                    gap: 8px;
                    font-size: 0.9rem;
                }}
                
                .dark-mode-toggle:hover {{
                    background: rgba(255,255,255,0.1);
                }}
                
                @media (max-width: 768px) {{
                    .dashboard-container {{
                        padding: var(--spacing-sm);
                    }}
                    
                    .dashboard-summary {{
                        grid-template-columns: 1fr;
                    }}
                    
                    .cards-grid {{
                        grid-template-columns: 1fr;
                    }}
                }}
            </style>
        </head>
        <body>
            <div class="dashboard-container">
                <div class="dashboard-header">
                    <div>
                        <h1 class="dashboard-title">DairyOS Dashboard</h1>
                        <p class="dashboard-subtitle">Real-time farm monitoring and analytics</p>
                    </div>
                    <div class="dark-mode-toggle" id="darkModeToggle">
                        <span>🌙</span>
                        <span>Dark Mode</span>
                    </div>
                </div>
                
                <div class="dashboard-summary">
                    <div class="summary-card">
                        <div class="summary-card-title">Total Animals</div>
                        <div class="summary-card-value">{summary.total_animals}</div>
                        <div class="summary-card-subtitle">Healthy: {summary.healthy_animals}</div>
                    </div>
                    <div class="summary-card">
                        <div class="summary-card-title">Milk Yield Today</div>
                        <div class="summary-card-value">{summary.milk_yield_today:.1f} L</div>
                        <div class="summary-card-subtitle">vs average {summary.average_yield:.1f} L</div>
                    </div>
                    <div class="summary-card">
                        <div class="summary-card-title">Active Alerts</div>
                        <div class="summary-card-value">{summary.active_alerts}</div>
                        <div class="summary-card-subtitle">Critical issues</div>
                    </div>
                    <div class="summary-card">
                        <div class="summary-card-title">System Health</div>
                        <div class="summary-card-value">{summary.system_health.title()}</div>
                        <div class="summary-card-subtitle">Overall status</div>
                    </div>
                </div>
                
                <div class="dashboard-section">
                    <h2 class="section-title">Key Performance Indicators</h2>
                    <div class="cards-grid">
                        {self._render_cards_html(kpi_cards)}
                    </div>
                </div>
                
                <div class="dashboard-section">
                    <h2 class="section-title">Sensor Overview</h2>
                    <div class="cards-grid">
                        {self._render_cards_html(sensor_cards)}
                    </div>
                </div>
                
                <div class="dashboard-section">
                    <h2 class="section-title">Recent Alerts</h2>
                    <div class="cards-grid">
                        {self._render_cards_html(alert_cards)}
                    </div>
                </div>
                
                <div class="dashboard-section">
                    <h2 class="section-title">Production History</h2>
                    <div class="chart-container">
                        <h3 class="chart-title">Milk Yield Trend</h3>
                        <div class="chart">
                            {self._render_chart_html(production_chart)}
                        </div>
                    </div>
                </div>
                
                <div class="dashboard-section">
                    <h2 class="section-title">Herd Health Trend</h2>
                    <div class="chart-container">
                        <h3 class="chart-title">Healthy Animals</h3>
                        <div class="chart">
                            {self._render_chart_html(health_chart)}
                        </div>
                    </div>
                </div>
            </div>
            
            <script>
                document.getElementById('darkModeToggle').addEventListener('click', function() {{
                    document.body.classList.toggle('dark-mode');
                    var icon = this.querySelector('span:first-child');
                    if (document.body.classList.contains('dark-mode')) {{
                        icon.textContent = '☀️';
                        this.querySelector('span:last-child').textContent = 'Light Mode';
                    }} else {{
                        icon.textContent = '🌙';
                        this.querySelector('span:last-child').textContent = 'Dark Mode';
                    }}
                }});
            </script>
        </body>
        </html>
        """
        
        return html
    
    def _render_cards_html(self, cards: List[DashboardCard]) -> str:
        """Render cards as HTML."""
        html = ""
        for card in cards:
            status_class = f"status-{card.status}"
            trend_class = f"trend-{card.trend}" if card.trend else "trend-flat"
            
            html += f"""
            <div class="card">
                <div class="card-header">
                    <h3 class="card-title">{card.title}</h3>
                    <div class="card-icon" style="background-color: {self._get_status_color(card.status)}">
                        {self._get_icon(card.icon)}
                    </div>
                </div>
                <div class="card-value">{card.value}</div>
                <div class="card-subtitle">{card.subtitle}</div>
                <div class="card-trend {trend_class}">
                    {self._get_trend_icon(card.trend)}
                    <span>{card.trend}</span>
                </div>
            </div>
            """
        return html
    
    def _render_chart_html(self, chart_data: Dict[str, Any]) -> str:
        """Render chart as HTML."""
        if not chart_data.get('datasets'):
            return ""
        
        # Get max value for scaling
        max_value = max(chart_data['datasets'][0]['data'])
        
        html = ""
        for i, value in enumerate(chart_data['datasets'][0]['data']):
            height = (value / max_value) * 100 if max_value > 0 else 0
            html += f"""
            <div class="chart-bar" style="height: {height}%">
                <div class="chart-bar-value">{value:.0f}</div>
                <div class="chart-bar-label">{chart_data['labels'][i]}</div>
            </div>
            """
        return html
    
    def _get_status_color(self, status: str) -> str:
        """Get color for status."""
        colors = {
            "success": "#4CAF50",
            "warning": "#FF9800",
            "critical": "#F44336",
            "normal": "#9E9E9E"
        }
        return colors.get(status, "#9E9E9E")
    
    def _get_icon(self, icon_name: str) -> str:
        """Get icon for card."""
        icons = {
            "milk": "🥛",
            "health": "🏥",
            "alert": "⚠️",
            "system": "⚙️",
            "sensor": "📡",
        }
        return icons.get(icon_name, "📊")
    
    def _get_trend_icon(self, trend: str) -> str:
        """Get trend icon."""
        if trend == "up":
            return "↑"
        elif trend == "down":
            return "↓"
        else:
            return "→"
