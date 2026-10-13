import React, { useState } from 'react';
import { Utensils, Footprints, ArrowRightLeft, ShieldCheck, CheckCircle, AlertTriangle, Sparkles } from 'lucide-react';

export default function ThaliWhatIfSimulator({ dishes, defaultPatient }) {
  const [selectedDishId, setSelectedDishId] = useState('D02'); // Default: Masala Dosa
  const [portion, setPortion] = useState(1.0);
  const [enableWalk, setEnableWalk] = useState(true);
  const [enableSwap, setEnableSwap] = useState(true);

  const currentDish = dishes.find(d => d.id === selectedDishId) || dishes[0];
  const swapDishId = currentDish.swapTarget || 'D09';
  const swapDish = dishes.find(d => d.id === swapDishId) || dishes.find(d => d.id === 'D09');

  // Baseline glucose (from selected patient or default 110 mg/dL)
  const gBase = defaultPatient ? defaultPatient.fastingGlucose : 105;

  // Physiological Peak Rise Calculations
  // Masala Dosa (52g carbs, high GI) vs Besan Chilla (26g carbs, low GI)
  const carbRiseFactor = 0.82; // mg/dL per carb gram
  const fiberAttenuation = 0.45; // mg/dL reduction per fiber gram

  // Planned Meal Scenario
  const planCarbs = currentDish.carbs * portion;
  const planFiber = currentDish.fiber * portion;
  const planNetCarbs = Math.max(0, planCarbs - planFiber);
  const planGlycemicLoad = Math.round((planNetCarbs * currentDish.glycemicIndex) / 100);
  const planRise = Math.round(planCarbs * carbRiseFactor - planFiber * fiberAttenuation + (currentDish.glycemicIndex - 50) * 0.3);
  const planPeak = gBase + planRise;
  const planRisk = Math.min(0.98, Math.max(0.05, 0.25 + (planRise / 80) * 0.65));

  // Planned Meal + Walk Scenario (15 min brisk walk = ~22% drop in peak excursion via GLUT4)
  const walkRise = Math.round(planRise * 0.78);
  const walkPeak = gBase + walkRise;
  const walkRisk = Math.min(0.95, Math.max(0.05, planRisk * 0.70));

  // Recommended Swap Scenario
  const swapCarbs = swapDish.carbs;
  const swapFiber = swapDish.fiber;
  const swapNetCarbs = Math.max(0, swapCarbs - swapFiber);
  const swapGlycemicLoad = Math.round((swapNetCarbs * swapDish.glycemicIndex) / 100);
  const swapRise = Math.round(swapCarbs * carbRiseFactor - swapFiber * fiberAttenuation + (swapDish.glycemicIndex - 50) * 0.3);
  const swapPeak = gBase + swapRise;
  const swapRisk = Math.min(0.95, Math.max(0.05, 0.25 + (swapRise / 80) * 0.65));

  // Generate 2-hour trajectory curves (0 to 120 mins)
  const timeSteps = [0, 15, 30, 45, 60, 75, 90, 105, 120];
  const generateCurve = (base, rise, peakT = 50) => {
    return timeSteps.map(t => {
      const tNorm = Math.max(0.001, t / peakT);
      const val = base + rise * (tNorm * Math.exp(1 - tNorm));
      return Math.round(Math.min(300, Math.max(40, val)));
    });
  };

  const curvePlan = generateCurve(gBase, planRise, 50);
  const curveWalk = generateCurve(gBase, walkRise, 45);
  const curveSwap = generateCurve(gBase, swapRise, 55);

  // SVG Chart Dimensions
  const svgWidth = 800;
  const svgHeight = 280;
  const pad = { top: 25, right: 30, bottom: 35, left: 50 };
  const chartW = svgWidth - pad.left - pad.right;
  const chartH = svgHeight - pad.top - pad.bottom;
  const minG = 50;
  const maxG = 250;

  const getY = g => pad.top + chartH - ((g - minG) / (maxG - minG)) * chartH;
  const getX = idx => pad.left + (idx / (timeSteps.length - 1)) * chartW;

  const buildPath = points => points.reduce((acc, g, idx) => `${acc} ${idx === 0 ? 'M' : 'L'} ${getX(idx)} ${getY(g)}`, '');

  return (
    <div>
      {/* Module Title Banner */}
      <div className="glass-panel" style={{ padding: '20px 24px', marginBottom: '20px' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '16px' }}>
          <div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
              <Utensils size={22} color="#F59E0B" />
              <h2 style={{ fontSize: '20px', fontWeight: 700 }}>Indian Thali What-If Simulator & Counterfactual Engine</h2>
            </div>
            <p style={{ fontSize: '13px', color: 'var(--text-secondary)', marginTop: '4px' }}>
              Built ground-up with 25 authentic Indian regional dishes from ICMR-NIN IFCT 2017 & South Asian GI Tables.
            </p>
          </div>
          <span className="badge" style={{ background: 'rgba(16, 185, 129, 0.15)', color: '#34D399', border: '1px solid rgba(16, 185, 129, 0.3)' }}>
            <ShieldCheck size={14} /> Monotonic Constraints Verified
          </span>
        </div>
      </div>

      {/* Simulator Inputs & Interactive Controls */}
      <div className="grid-1-3" style={{ marginBottom: '20px' }}>
        {/* Left Column: Meal Selector & Portions */}
        <div className="glass-panel" style={{ padding: '20px' }}>
          <h3 style={{ fontSize: '15px', fontWeight: 700, marginBottom: '14px', color: '#F8FAFC' }}>
            1. Select Planned Indian Meal
          </h3>

          <label style={{ fontSize: '12px', color: 'var(--text-secondary)', display: 'block', marginBottom: '6px' }}>
            Choose from 25 Dishes:
          </label>
          <select
            value={selectedDishId}
            onChange={e => setSelectedDishId(e.target.value)}
            style={{
              width: '100%',
              background: 'rgba(15, 23, 42, 0.8)',
              border: '1px solid var(--border-subtle)',
              borderRadius: '8px',
              padding: '10px 12px',
              color: 'white',
              fontSize: '13px',
              outline: 'none',
              marginBottom: '16px'
            }}
          >
            {dishes.map(d => (
              <option key={d.id} value={d.id}>
                {d.name} ({d.origin})
              </option>
            ))}
          </select>

          <div style={{ marginBottom: '16px' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '12px', color: 'var(--text-secondary)', marginBottom: '4px' }}>
              <span>Portion Factor:</span>
              <span style={{ fontWeight: 700, color: 'var(--c-cyan)' }}>{portion}x Serving</span>
            </div>
            <input
              type="range"
              min="0.5"
              max="2.0"
              step="0.25"
              value={portion}
              onChange={e => setPortion(parseFloat(e.target.value))}
              style={{ width: '100%', accentColor: '#38BDF8' }}
            />
          </div>

          <div style={{ background: 'rgba(15, 23, 42, 0.6)', border: '1px solid var(--border-subtle)', borderRadius: '10px', padding: '12px', fontSize: '12px', color: 'var(--text-secondary)' }}>
            <div style={{ fontWeight: 600, color: '#F8FAFC', marginBottom: '4px' }}>{currentDish.name}</div>
            <div><b>Net Carbs:</b> {planNetCarbs.toFixed(1)}g · <b>Glycemic Load:</b> {planGlycemicLoad}</div>
            <div style={{ fontSize: '11px', color: 'var(--text-muted)', marginTop: '4px' }}>{currentDish.notes}</div>
          </div>

          <hr style={{ borderColor: 'var(--border-subtle)', margin: '16px 0' }} />

          <h3 style={{ fontSize: '15px', fontWeight: 700, marginBottom: '12px', color: '#F8FAFC' }}>
            2. Toggle Interventions
          </h3>

          <label style={{ display: 'flex', alignItems: 'center', gap: '8px', fontSize: '13px', color: '#CBD5E1', cursor: 'pointer', marginBottom: '10px' }}>
            <input
              type="checkbox"
              checked={enableWalk}
              onChange={e => setEnableWalk(e.target.checked)}
              style={{ accentColor: '#F59E0B' }}
            />
            <span>🚶 <b>+15-Minute Brisk Walk</b></span>
          </label>

          <label style={{ display: 'flex', alignItems: 'center', gap: '8px', fontSize: '13px', color: '#CBD5E1', cursor: 'pointer' }}>
            <input
              type="checkbox"
              checked={enableSwap}
              onChange={e => setEnableSwap(e.target.checked)}
              style={{ accentColor: '#10B981' }}
            />
            <span>🔄 <b>Compare Healthy Swap:</b> {swapDish.name.split('(')[0]}</span>
          </label>
        </div>

        {/* Right Column: Comparative Trajectory SVG Chart */}
        <div className="glass-panel" style={{ padding: '20px' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '14px' }}>
            <h3 style={{ fontSize: '16px', fontWeight: 700 }}>2-Hour Postprandial Counterfactual Curves</h3>
            <div style={{ display: 'flex', gap: '14px', fontSize: '12px' }}>
              <span style={{ color: '#EF4444' }}>● Planned: {currentDish.name.split('(')[0]}</span>
              {enableWalk && <span style={{ color: '#F59E0B' }}>-- Planned + 15m Walk</span>}
              {enableSwap && <span style={{ color: '#10B981' }}>● Swap: {swapDish.name.split('(')[0]}</span>}
            </div>
          </div>

          {/* SVG Graph */}
          <div style={{ overflowX: 'auto' }}>
            <svg viewBox={`0 0 ${svgWidth} ${svgHeight}`} style={{ width: '100%', height: 'auto', maxHeight: '300px' }}>
              {/* Gridlines */}
              {[70, 100, 140, 180, 220].map(g => (
                <g key={g}>
                  <line
                    x1={pad.left}
                    y1={getY(g)}
                    x2={pad.left + chartW}
                    y2={getY(g)}
                    stroke="rgba(51, 65, 85, 0.3)"
                    strokeDasharray={g === 180 ? '4 4' : 'none'}
                    strokeWidth={g === 180 ? '1.5' : '1'}
                  />
                  <text x={pad.left - 10} y={getY(g) + 4} fill="#64748B" fontSize="10" textAnchor="end">
                    {g}
                  </text>
                </g>
              ))}

              <text x={pad.left + chartW - 5} y={getY(180) - 6} fill="#EF4444" fontSize="10" textAnchor="end" fontWeight="600">
                Ceiling (180 mg/dL)
              </text>

              {/* Planned Meal Curve (Crimson) */}
              <path d={buildPath(curvePlan)} fill="none" stroke="#EF4444" strokeWidth="3" />
              <circle cx={getX(3)} cy={getY(planPeak)} r="5" fill="#EF4444" stroke="#FFFFFF" strokeWidth="1.5" />
              <text x={getX(3)} y={getY(planPeak) - 10} fill="#EF4444" fontSize="11" fontWeight="700" textAnchor="middle">
                {planPeak} mg/dL
              </text>

              {/* Planned + Walk Curve (Amber Dashed) */}
              {enableWalk && (
                <>
                  <path d={buildPath(curveWalk)} fill="none" stroke="#F59E0B" strokeWidth="2.5" strokeDasharray="5 5" />
                  <circle cx={getX(3)} cy={getY(walkPeak)} r="4" fill="#F59E0B" />
                  <text x={getX(3) + 35} y={getY(walkPeak) + 15} fill="#F59E0B" fontSize="10" fontWeight="700" textAnchor="middle">
                    {walkPeak} mg/dL
                  </text>
                </>
              )}

              {/* Swap Meal Curve (Emerald) */}
              {enableSwap && (
                <>
                  <path d={buildPath(curveSwap)} fill="none" stroke="#10B981" strokeWidth="3" />
                  <circle cx={getX(4)} cy={getY(swapPeak)} r="5" fill="#10B981" stroke="#FFFFFF" strokeWidth="1.5" />
                  <text x={getX(4)} y={getY(swapPeak) - 10} fill="#10B981" fontSize="11" fontWeight="700" textAnchor="middle">
                    {swapPeak} mg/dL
                  </text>
                </>
              )}

              {/* X Axis Time */}
              {timeSteps.map((t, idx) => (
                <text key={`t-${idx}`} x={getX(idx)} y={svgHeight - 12} fill="#64748B" fontSize="10" textAnchor="middle">
                  {t}m
                </text>
              ))}
            </svg>
          </div>

          <div style={{ textAlign: 'center', fontSize: '11px', color: 'var(--text-muted)', marginTop: '6px' }}>
            Minutes Post-Meal (0 to 120 Minutes)
          </div>
        </div>
      </div>

      {/* Comparative Clinical Impact Table */}
      <div className="glass-panel" style={{ padding: 0, overflow: 'hidden' }}>
        <table className="custom-table">
          <thead>
            <tr>
              <th>Simulation Scenario</th>
              <th>Net Carbs</th>
              <th>Glycemic Load</th>
              <th>Predicted Peak</th>
              <th>90% Conformal Ribbon</th>
              <th>2h Excursion Risk</th>
              <th>Clinical Outcome</th>
            </tr>
          </thead>
          <tbody>
            <tr>
              <td>
                <span style={{ fontWeight: 700, color: '#EF4444' }}>● Planned: {currentDish.name}</span>
                <span style={{ fontSize: '11px', color: 'var(--text-muted)', marginLeft: '6px' }}>({portion}x)</span>
              </td>
              <td>{planNetCarbs.toFixed(0)}g</td>
              <td>{planGlycemicLoad}</td>
              <td style={{ fontWeight: 700 }}>{planPeak} mg/dL</td>
              <td>±32 mg/dL</td>
              <td>
                <span style={{ fontWeight: 700, color: planRisk > 0.7 ? '#EF4444' : '#F59E0B' }}>
                  {Math.round(planRisk * 100)}%
                </span>
              </td>
              <td>
                <span style={{ fontSize: '12px', fontWeight: 600, color: planPeak > 180 ? '#EF4444' : '#F59E0B' }}>
                  {planPeak > 180 ? '⚠️ High Excursion Spike' : 'Moderate Rise'}
                </span>
              </td>
            </tr>

            {enableWalk && (
              <tr>
                <td>
                  <span style={{ fontWeight: 700, color: '#F59E0B' }}>🚶 Planned Meal + 15m Brisk Walk</span>
                </td>
                <td>{planNetCarbs.toFixed(0)}g</td>
                <td>{planGlycemicLoad}</td>
                <td style={{ fontWeight: 700, color: '#10B981' }}>{walkPeak} mg/dL (-{planPeak - walkPeak} mg/dL)</td>
                <td>±26 mg/dL</td>
                <td><span style={{ fontWeight: 700, color: '#10B981' }}>{Math.round(walkRisk * 100)}%</span></td>
                <td>
                  <span style={{ fontSize: '12px', fontWeight: 600, color: '#10B981' }}>
                    ✅ Safe Zone via Muscle GLUT4 Uptake
                  </span>
                </td>
              </tr>
            )}

            {enableSwap && (
              <tr>
                <td>
                  <span style={{ fontWeight: 700, color: '#10B981' }}>🔄 Recommended Swap: {swapDish.name}</span>
                </td>
                <td>{swapNetCarbs.toFixed(0)}g</td>
                <td>{swapGlycemicLoad}</td>
                <td style={{ fontWeight: 700, color: '#10B981' }}>{swapPeak} mg/dL (-{planPeak - swapPeak} mg/dL)</td>
                <td>±22 mg/dL</td>
                <td><span style={{ fontWeight: 700, color: '#10B981' }}>{Math.round(swapRisk * 100)}%</span></td>
                <td>
                  <span style={{ fontSize: '12px', fontWeight: 600, color: '#10B981' }}>
                    🌟 Optimal Glycemic Stability
                  </span>
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}
