import React, { useState, useEffect } from 'react';

export default function ThiWidget() {
  const [telemetry, setTelemetry] = useState({
    temperature: '--',
    humidity: '--',
    thi: '--',
    status: 'Connecting...'
  });

  useEffect(() => {
    // Connect to the FastAPI WebSocket endpoint
    const ws = new WebSocket('ws://localhost:8000/ws/thi');

    ws.onopen = () => {
      setTelemetry(prev => ({ ...prev, status: 'Connected' }));
    };

    ws.onmessage = (event) => {
      const data = JSON.parse(event.data);
      setTelemetry(data);
    };

    ws.onclose = () => {
      setTelemetry(prev => ({ ...prev, status: 'Disconnected' }));
    };

    // Clean up the connection when the widget is removed from the screen
    return () => {
      ws.close();
    };
  }, []);

  const getStatusColor = (status) => {
    if (status.includes('Stress') || status === 'Deadly') return 'text-red-600';
    if (status === 'Normal') return 'text-green-600';
    return 'text-gray-600';
  };

  return (
    <div className="p-4 bg-white rounded shadow-md w-80 border-l-4 border-blue-500">
      <h2 className="text-xl font-bold mb-4 text-gray-800">Live Shed Environment</h2>
      
      <div className="space-y-3">
        <div className="flex justify-between items-center">
          <span className="text-gray-600">Temperature</span>
          <strong className="text-lg">{telemetry.temperature} °C</strong>
        </div>
        
        <div className="flex justify-between items-center">
          <span className="text-gray-600">Humidity</span>
          <strong className="text-lg">{telemetry.humidity} %</strong>
        </div>
        
        <div className="flex justify-between items-center border-t pt-3 mt-2">
          <span className="font-bold text-gray-800">THI Index</span>
          <strong className="text-2xl">{telemetry.thi}</strong>
        </div>
        
        <div className={mt-2 pt-2 text-sm font-bold text-right uppercase tracking-wider }>
          {telemetry.status}
        </div>
      </div>
    </div>
  );
}
