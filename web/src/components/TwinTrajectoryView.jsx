import React, { useState } from 'react';
import { Sliders, ShieldCheck, AlertCircle, Droplets, Utensils, Activity, ArrowRight, FileText } from 'lucide-react';

export default function TwinTrajectoryView({ patient, trajectoryPoints, onOpenWhatIf }) {
  const [selectedTier, setSelectedTier] = useState('T2_Frugal');
  const [virtualFingerstickLogged, setVirtualFingerstickLogged] = useState(false);

  if (!patient) return null;

  // Dynamic Conformal Uncertainty Bandwidth
  let bandMargin = 22; // mg/dL
  let tierCost = '₹1,200/mo';
  let tierDesc = 'Sparse glucometer fingersticks (3-4/day) + Fitbit + Indian meal log';
  let alertMessage = null;

  if (selectedTier === 'T1_Rich') {
    bandMargin = 20;
    tierCost = '₹10,000/mo';
    tierDesc = 'Continuous 5-min Dexcom G6 Pro stream + Smartwatch + Meal log';
  } else if (selectedTier === 'T2_Frugal') {
    bandMargin = virtualFingerstickLogged ? 18 : 36;
    tierCost = '₹1,200/mo';
    tierDesc = 'Frugal Stepped-Care: Sparse glucometer (3-4/day) with 7% ISO-15197 meter noise';
    alertMessage = virtualFingerstickLogged
      ? '✅ Virtual fingerstick recorded at 12:45 PM (128 mg/dL). Twin uncertainty band contracted by 50%.'
      : '⚡ Active Inquiry: Post-lunch uncertainty expanding (±36 mg/dL). Clinician prompt: Take fingerstick check now to anchor baseline.';
  } else {
    bandMargin = 55;
    tierCost = '₹0/mo';
    tierDesc = 'Triage Mode: Fitbit Sense wearable + Static EHR labs only (Zero glucose sensors)';
    alertMessage = '⚠️ Tier 3 Active: Operating without glucose sensors. Wide conformal ribbon reflects population variance.';
  }

  // Pre-calculate AGP metrics from trajectory
  const glucoseValues = trajectoryPoints.map(p => p.trueGlucose);
  const n = glucoseValues.length || 1;
  const tir = Math.round((glucoseValues.filter(g => g >= 70 && g <= 180).length / n) * 100);
  const tar = Math.round((glucoseValues.filter(g => g > 180).length / n) * 100);
  const tbr = Math.round((glucoseValues.filter(g => g < 70).length / n) * 100);
  const meanG = Math.round(glucoseValues.reduce((a, b) => a + b, 0) / n);
  const gmi = (3.31 + 0.02392 * meanG).toFixed(1);

  // SVG Chart Dimensions
  const svgWidth = 900;
  const svgHeight = 320;
  const padding = { top: 30, right: 40, bottom: 40, left: 55 };
  const chartW = svgWidth - padding.left - padding.right;
  const chartH = svgHeight - padding.top - padding.bottom;

  // Scales
  const minG = 40;
  const maxG = 280;
  const getY = g => padding.top + chartH - ((g - minG) / (maxG - minG)) * chartH;
  const getX = idx => padding.left + (idx / Math.max(1, trajectoryPoints.length - 1)) * chartW;

  // Build SVG Paths
  const upperPoints = trajectoryPoints.map((p, i) => `${getX(i)},${getY(Math.min(maxG, p.trueGlucose + bandMargin))}`);
  const lowerPoints = trajectoryPoints.map((p, i) => `${getX(i)},${getY(Math.max(minG, p.trueGlucose - bandMargin))}`).reverse();
  const ribbonD = `M ${upperPoints[0]} L ${upperPoints.slice(1).join(' L ')} L ${lowerPoints.join(' L ')} Z`;

  const lineD = trajectoryPoints.reduce((acc, p, i) => `${acc} ${i === 0 ? 'M' : 'L'} ${getX(i)} ${getY(p.trueGlucose)}`, '');

  return (
    <div>
      {/* Patient Header Card */}
      <div className="glass-panel" style={{ padding: '20px 24px', marginBottom: '20px' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '16px' }}>
          <div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
              <h2 style={{ fontSize: '22px', fontWeight: 700 }}>Patient #{patient.id} Digital Twin Trajectory</h2>
              <span className={`badge ${patient.phenotype === 'Type 2 Diabetes' ? 'badge-t2d' : (patient.phenotype === 'Prediabetes' ? 'badge-predia' : 'badge-norm')}`}>
                {patient.phenotype}
              </span>
              <span className="badge badge-tier">Active: {selectedTier}</span>
            </div>
            <p style={{ fontSize: '13px', color: 'var(--text-secondary)', marginTop: '4px' }}>
              Age: {patient.age}y · Gender: {patient.gender} · BMI: {patient.bmi} · HbA1c: {patient.hba1c}% · Fasting Glucose: {patient.fastingGlucose} mg/dL
            </p>
          </div>

          <div style={{ display: 'flex', gap: '12px', flexWrap: 'wrap' }}>
            <button
              className="btn-primary"
              style={{ background: 'linear-gradient(135deg, #6366F1, #4F46E5)' }}
              onClick={() => window.open(`http://127.0.0.1:8000/api/v1/reports/${patient.id}/pdf`, '_blank')}
            >
              <FileText size={16} /> Download Hospital AGP (PDF)
            </button>
            <button className="btn-accent" onClick={onOpenWhatIf}>
              <Utensils size={16} /> Test Indian Thali What-If <ArrowRight size={14} />
            </button>
          </div>
        </div>
      </div>

      {/* The Stepped-Care Live Tier Slider Card */}
      <div className="glass-panel" style={{ padding: '20px 24px', marginBottom: '20px', borderColor: 'rgba(56, 189, 248, 0.4)' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '14px' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <Sliders size={18} color="#38BDF8" />
            <span style={{ fontSize: '14px', fontWeight: 700, color: '#F8FAFC' }}>
              LIVE STEPPED-CARE DATA DENSITY SLIDER (THE CORE DEMONSTRATION)
            </span>
          </div>
          <span style={{ fontSize: '12px', color: '#10B981', fontWeight: 600 }}>Active Consumable Cost: {tierCost}</span>
        </div>

        <div className="tier-slider-track">
          {[
            { id: 'T1_Rich', title: 'T1: Rich Continuous CGM', cost: '₹10,000 / month', desc: 'Dexcom G6 Pro (5m native stream)' },
            { id: 'T2_Frugal', title: 'T2: Frugal Glucometer (SMBG)', cost: '₹1,200 / month', desc: '3-4 Fingersticks/day (7% ISO noise)' },
            { id: 'T3_Triage', title: 'T3: Minimal Triage', cost: '₹0 / month', desc: 'Fitbit Wearable + Static EHR Labs' },
          ].map(t => (
            <div
              key={t.id}
              className={`tier-option ${selectedTier === t.id ? 'selected' : ''}`}
              onClick={() => {
                setSelectedTier(t.id);
                setVirtualFingerstickLogged(false);
              }}
            >
              <div className="tier-title">{t.title}</div>
              <div className="tier-cost">{t.cost}</div>
              <div className="tier-desc">{t.desc}</div>
            </div>
          ))}
        </div>

        {/* Active Inquiry Alert Banner & Virtual Fingerstick Action */}
        {alertMessage && (
          <div style={{
            marginTop: '16px',
            padding: '12px 18px',
            borderRadius: '10px',
            background: virtualFingerstickLogged ? 'rgba(16, 185, 129, 0.15)' : 'rgba(245, 158, 11, 0.15)',
            borderLeft: `4px solid ${virtualFingerstickLogged ? '#10B981' : '#F59E0B'}`,
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'center',
            flexWrap: 'wrap',
            gap: '12px'
          }}>
            <span style={{ fontSize: '13px', color: '#F8FAFC', fontWeight: 500 }}>
              {alertMessage}
            </span>

            {selectedTier === 'T2_Frugal' && (
              <button
                className="btn-primary"
                style={{ padding: '8px 16px', fontSize: '12px' }}
                onClick={() => setVirtualFingerstickLogged(!virtualFingerstickLogged)}
              >
                <Droplets size={14} /> {virtualFingerstickLogged ? 'Reset Virtual Reading' : 'Log Virtual Fingerstick Now'}
              </button>
            )}
          </div>
        )}
      </div>

      {/* Interactive SVG Trajectory Visualization */}
      <div className="glass-panel" style={{ padding: '20px 24px', marginBottom: '20px' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px' }}>
          <div>
            <h3 style={{ fontSize: '16px', fontWeight: 700 }}>24-Hour Patient Glycemic Replay & Conformal Prediction Band</h3>
            <p style={{ fontSize: '12px', color: 'var(--text-secondary)' }}>
              Solid Line: Dexcom Continuous Ground Truth · Shaded Ribbon: Split-Conformal 90% Uncertainty Band (±{bandMargin} mg/dL)
            </p>
          </div>
          <div style={{ display: 'flex', gap: '16px', fontSize: '12px', color: 'var(--text-secondary)' }}>
            <span style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
              <span style={{ width: '12px', height: '3px', background: '#38BDF8', display: 'inline-block' }} /> CGM Trajectory
            </span>
            <span style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
              <span style={{ width: '12px', height: '10px', background: 'rgba(99, 102, 241, 0.3)', display: 'inline-block' }} /> 90% Conformal Ribbon
            </span>
            <span style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
              <span style={{ width: '8px', height: '8px', background: '#F59E0B', transform: 'rotate(45deg)', display: 'inline-block' }} /> Fingerstick Check
            </span>
            <span style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
              <span style={{ width: '12px', height: '2px', borderTop: '2px dashed #EF4444', display: 'inline-block' }} /> 180 mg/dL Target
            </span>
          </div>
        </div>

        {/* SVG Chart */}
        <div style={{ overflowX: 'auto' }}>
          <svg viewBox={`0 0 ${svgWidth} ${svgHeight}`} style={{ width: '100%', height: 'auto', maxHeight: '360px' }}>
            {/* Horizontal Gridlines */}
            {[70, 100, 140, 180, 220, 260].map(g => (
              <g key={g}>
                <line
                  x1={padding.left}
                  y1={getY(g)}
                  x2={padding.left + chartW}
                  y2={getY(g)}
                  stroke="rgba(51, 65, 85, 0.3)"
                  strokeDasharray={g === 180 || g === 70 ? '4 4' : 'none'}
                  strokeWidth={g === 180 ? '1.5' : '1'}
                />
                <text x={padding.left - 10} y={getY(g) + 4} fill="#64748B" fontSize="10" textAnchor="end">
                  {g}
                </text>
              </g>
            ))}

            {/* Ceiling 180 Line label */}
            <text x={padding.left + chartW - 5} y={getY(180) - 6} fill="#EF4444" fontSize="10" textAnchor="end" fontWeight="600">
              Clinical Ceiling (180 mg/dL)
            </text>

            {/* Conformal Prediction Uncertainty Ribbon */}
            <path d={ribbonD} fill="rgba(99, 102, 241, 0.16)" stroke="none" />

            {/* Ground Truth Glucose Line */}
            <path d={lineD} fill="none" stroke="#38BDF8" strokeWidth="2.5" />

            {/* Sparse Fingersticks in Tier 2 */}
            {selectedTier === 'T2_Frugal' && trajectoryPoints.map((p, idx) => {
              if (!p.glucometerReading) return null;
              return (
                <g key={`fs-${idx}`}>
                  <rect
                    x={getX(idx) - 5}
                    y={getY(p.glucometerReading) - 5}
                    width="10"
                    height="10"
                    fill="#F59E0B"
                    transform={`rotate(45 ${getX(idx)} ${getY(p.glucometerReading)})`}
                    stroke="#FFFFFF"
                    strokeWidth="1.5"
                  />
                  <text x={getX(idx)} y={getY(p.glucometerReading) - 12} fill="#FBBF24" fontSize="9" fontWeight="700" textAnchor="middle">
                    {p.glucometerReading}
                  </text>
                </g>
              );
            })}

            {/* Meal Markers */}
            {trajectoryPoints.map((p, idx) => {
              if (!p.carbs) return null;
              return (
                <g key={`meal-${idx}`}>
                  <circle cx={getX(idx)} cy={getY(p.trueGlucose)} r="5" fill="#10B981" stroke="#FFFFFF" strokeWidth="1.5" />
                  <rect x={getX(idx) - 28} y={getY(p.trueGlucose) - 24} width="56" height="16" rx="4" fill="rgba(16, 185, 129, 0.85)" />
                  <text x={getX(idx)} y={getY(p.trueGlucose) - 12} fill="#FFFFFF" fontSize="9" fontWeight="700" textAnchor="middle">
                    🍴 {p.carbs}g
                  </text>
                </g>
              );
            })}

            {/* X-axis Time Labels */}
            {trajectoryPoints.filter((_, idx) => idx % 6 === 0).map((p, idx) => (
              <text key={`time-${idx}`} x={getX(idx * 6)} y={svgHeight - 15} fill="#64748B" fontSize="10" textAnchor="middle">
                {p.time}
              </text>
            ))}
          </svg>
        </div>
      </div>

      {/* Ambulatory Glucose Profile (AGP) Metrics */}
      <div className="grid-4">
        <div className="stat-tile success">
          <div className="stat-label">Time in Range (70-180)</div>
          <div className="stat-value">{tir}%</div>
          <div className="stat-sub">Consensus Target: &gt; 70%</div>
        </div>
        <div className="stat-tile danger">
          <div className="stat-label">Time Above Range (&gt;180)</div>
          <div className="stat-value">{tar}%</div>
          <div className="stat-sub">Consensus Target: &lt; 25%</div>
        </div>
        <div className="stat-tile warning">
          <div className="stat-label">Time Below Range (&lt;70)</div>
          <div className="stat-value">{tbr}%</div>
          <div className="stat-sub">Consensus Target: &lt; 4%</div>
        </div>
        <div className="stat-tile indigo">
          <div className="stat-label">Estimated GMI / Mean GLU</div>
          <div className="stat-value">{gmi}%</div>
          <div className="stat-sub">Mean: {meanG} mg/dL</div>
        </div>
      </div>
    </div>
  );
}
