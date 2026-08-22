import React, { useState } from 'react';
import { DollarSign, Thermometer, Wind, AlertTriangle, ArrowUpRight, ArrowDownRight, RefreshCw } from 'lucide-react';

interface FarmIntelligenceWidgetProps {
  milkYieldPerCow?: number; // Liters
  milkPricePKR?: number;    // PKR / Liter
  feedCostPerCow?: number;  // PKR / Cow / Day
  ambientTempC?: number;    // Celsius
  relativeHumidity?: number;// Percent (0-100)
}

export default function FarmIntelligenceWidget({
  milkYieldPerCow = 28.5,
  milkPricePKR = 195,
  feedCostPerCow = 2450,
  ambientTempC = 34.5,
  relativeHumidity = 65
}: FarmIntelligenceWidgetProps) {
  const [milkYield, setMilkYield] = useState(milkYieldPerCow);
  const [milkPrice, setMilkPrice] = useState(milkPricePKR);
  const [feedCost, setFeedCost] = useState(feedCostPerCow);

  // Calculate IOFC
  const dailyGrossRevenue = milkYield * milkPrice;
  const iofcValue = dailyGrossRevenue - feedCost;
  const iofcMarginPct = ((iofcValue / dailyGrossRevenue) * 100).toFixed(0);

  // Calculate THI: THI = (1.8*T + 32) - (0.55 - 0.0055*RH) * (1.8*T - 26)
  const thi = (1.8 * ambientTempC + 32) - (0.55 - 0.0055 * relativeHumidity) * (1.8 * ambientTempC - 26);
  const thiScore = parseFloat(thi.toFixed(0));

  let heatStressLevel = 'Normal';
  let heatStressColor = 'emerald';
  let coolingProtocol = 'Standard ventilation';

  if (thiScore >= 80) {
    heatStressLevel = 'Severe Stress';
    heatStressColor = 'red';
    coolingProtocol = 'Continuous fans + 3-min soaker cycles every 10 min';
  } else if (thiScore >= 72) {
    heatStressLevel = 'Moderate Stress';
    heatStressColor = 'amber';
    coolingProtocol = 'Continuous fans + 2-min soaker cycles every 15 min';
  } else if (thiScore >= 68) {
    heatStressLevel = 'Mild Stress';
    heatStressColor = 'yellow';
    coolingProtocol = 'Activate holding pen & feed bunk fans';
  }

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
      {/* 1. IOFC Intelligence Card */}
      <div className="bg-neutral-900 border border-neutral-800 rounded-2xl p-5 shadow-lg space-y-4">
        <div className="flex justify-between items-center border-b border-neutral-800 pb-3">
          <div className="flex items-center gap-2">
            <div className="p-2 rounded-lg bg-emerald-950/70 border border-emerald-500/30 text-emerald-400">
              <DollarSign className="w-4 h-4" />
            </div>
            <div>
              <h3 className="text-sm font-semibold text-white">Live IOFC Unit Economics</h3>
              <p className="text-[11px] text-neutral-400">Income Over Feed Cost per Cow/Day</p>
            </div>
          </div>
          <span className="text-xs font-mono font-semibold px-2 py-0.5 rounded bg-emerald-950 border border-emerald-500/40 text-emerald-300">
            {iofcMarginPct}% Margin
          </span>
        </div>

        <div className="flex items-baseline justify-between">
          <div>
            <span className="text-2xl font-bold font-mono text-white">
              PKR {iofcValue.toLocaleString('en-PK', { maximumFractionDigits: 0 })}
            </span>
            <span className="text-xs text-neutral-400 block mt-0.5">Net daily margin per milking cow</span>
          </div>
          <div className="text-right text-xs font-mono text-neutral-400 space-y-0.5">
            <div>Rev: <span className="text-neutral-200">PKR {dailyGrossRevenue.toFixed(0)}</span></div>
            <div>TMR: <span className="text-red-400">-PKR {feedCost.toFixed(0)}</span></div>
          </div>
        </div>

        <div className="grid grid-cols-3 gap-2 pt-2 border-t border-neutral-800/80 text-[11px]">
          <div>
            <span className="text-neutral-500 block">Avg Yield</span>
            <span className="text-neutral-200 font-mono font-medium">{milkYield} L/day</span>
          </div>
          <div>
            <span className="text-neutral-500 block">Milk Price</span>
            <span className="text-neutral-200 font-mono font-medium">PKR {milkPrice}/L</span>
          </div>
          <div>
            <span className="text-neutral-500 block">Feed Cost/Cow</span>
            <span className="text-neutral-200 font-mono font-medium">PKR {feedCost}</span>
          </div>
        </div>
      </div>

      {/* 2. THI Heat Stress Intelligence Card */}
      <div className="bg-neutral-900 border border-neutral-800 rounded-2xl p-5 shadow-lg space-y-4">
        <div className="flex justify-between items-center border-b border-neutral-800 pb-3">
          <div className="flex items-center gap-2">
            <div className={`p-2 rounded-lg ${
              heatStressColor === 'red' ? 'bg-red-950/70 border border-red-500/30 text-red-400' :
              heatStressColor === 'amber' ? 'bg-amber-950/70 border border-amber-500/30 text-amber-400' :
              heatStressColor === 'yellow' ? 'bg-yellow-950/70 border border-yellow-500/30 text-yellow-400' :
              'bg-emerald-950/70 border border-emerald-500/30 text-emerald-400'
            }`}>
              <Thermometer className="w-4 h-4" />
            </div>
            <div>
              <h3 className="text-sm font-semibold text-white">Thermal Comfort & THI Matrix</h3>
              <p className="text-[11px] text-neutral-400">Barki Herd Microclimate Sensing</p>
            </div>
          </div>
          <span className={`text-xs font-mono font-semibold px-2 py-0.5 rounded border ${
            heatStressColor === 'red' ? 'bg-red-950 border-red-500/40 text-red-300' :
            heatStressColor === 'amber' ? 'bg-amber-950 border-amber-500/40 text-amber-300' :
            heatStressColor === 'yellow' ? 'bg-yellow-950 border-yellow-500/40 text-yellow-300' :
            'bg-emerald-950 border-emerald-500/40 text-emerald-300'
          }`}>
            THI {thiScore} — {heatStressLevel}
          </span>
        </div>

        <div className="flex items-center justify-between">
          <div className="flex items-center gap-4 text-xs font-mono">
            <div>
              <span className="text-neutral-500 block">Ambient Temp</span>
              <span className="text-base font-bold text-white">{ambientTempC}°C</span>
            </div>
            <div>
              <span className="text-neutral-500 block">Humidity</span>
              <span className="text-base font-bold text-white">{relativeHumidity}% RH</span>
            </div>
          </div>
          <div className="flex items-center gap-1.5 text-xs text-neutral-400">
            <Wind className="w-4 h-4 text-sky-400" />
            <span>Active Shed Sensors</span>
          </div>
        </div>

        <div className="p-2.5 rounded-lg bg-neutral-950/80 border border-neutral-800 text-[11px] space-y-1">
          <div className="flex items-center gap-1.5 font-medium text-neutral-300">
            <AlertTriangle className="w-3.5 h-3.5 text-amber-400 shrink-0" />
            <span>Cooling Protocol Directive:</span>
          </div>
          <p className="text-neutral-400 pl-5">{coolingProtocol}</p>
        </div>
      </div>
    </div>
  );
}


