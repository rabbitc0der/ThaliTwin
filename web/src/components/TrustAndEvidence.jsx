import React from 'react';
import { ShieldCheck, FileText, CheckCircle2, AlertOctagon, TrendingDown, Award, Lock, BarChart3, Clock, Layers } from 'lucide-react';

export default function TrustAndEvidence({ evidenceData, benchmarks }) {
  const { noiseFloor, learningCurve, susScore } = evidenceData;
  const b = benchmarks || {};

  // SVG Learning Curve Dimensions
  const svgW = 440;
  const svgH = 180;
  const pad = { top: 20, right: 30, bottom: 30, left: 45 };
  const cW = svgW - pad.left - pad.right;
  const cH = svgH - pad.top - pad.bottom;

  const minR = 25;
  const maxR = 50;
  const getY = r => pad.top + cH - ((r - minR) / (maxR - minR)) * cH;
  const getX = idx => pad.left + (idx / (learningCurve.length - 1)) * cW;

  const lineD = learningCurve.reduce((acc, p, idx) => `${acc} ${idx === 0 ? 'M' : 'L'} ${getX(idx)} ${getY(p.rmse)}`, '');

  return (
    <div>
      {/* Header Banner */}
      <div className="glass-panel" style={{ padding: '20px 24px', marginBottom: '20px' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '16px' }}>
          <div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
              <ShieldCheck size={22} color="#00F0FF" />
              <h2 style={{ fontSize: '20px', fontWeight: 700 }}>Scientific Evidence & Clinical Rigor Benchmark Suite</h2>
            </div>
            <p style={{ fontSize: '13px', color: 'var(--text-secondary)', marginTop: '4px' }}>
              Identical-window baselines, clustered bootstrap CIs (B=500), within-person AUROC, multimodal ablation, and sensor noise floor.
            </p>
          </div>
          <div style={{ display: 'flex', gap: '10px' }}>
            <span className="badge" style={{ background: 'rgba(0, 240, 255, 0.12)', color: '#00F0FF', border: '1px solid rgba(0, 240, 255, 0.3)' }}>
              <Award size={14} /> 1,210 Evaluated Meals (45 Adults)
            </span>
            <span className="badge" style={{ background: 'rgba(16, 185, 129, 0.15)', color: '#34D399', border: '1px solid rgba(16, 185, 129, 0.3)' }}>
              <Award size={14} /> SUS: {susScore} / 100 (Grade A)
            </span>
          </div>
        </div>
      </div>

      {/* Primary Benchmark: Identical-Window Discrimination Table */}
      <div className="glass-panel" style={{ padding: '20px 24px', marginBottom: '24px' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '14px' }}>
          <BarChart3 size={20} color="#00F0FF" />
          <h3 style={{ fontSize: '16px', fontWeight: 700 }}>1. Identical-Window Discrimination Benchmark & Baselines (5-Fold Stratified Group-KFold)</h3>
        </div>
        <p style={{ fontSize: '12px', color: 'var(--text-secondary)', marginBottom: '16px' }}>
          All models evaluated on the <b>exact same 1,210 meal windows</b> with patient-level cluster bootstrap (B=500) 95% Confidence Intervals:
        </p>

        <div className="table-container">
          <table className="custom-table">
            <thead>
              <tr>
                <th>Model / Modality</th>
                <th>AUROC</th>
                <th>95% Bootstrap CI</th>
                <th>Retention Above Chance (0.500)</th>
                <th>Status vs Baselines</th>
              </tr>
            </thead>
            <tbody>
              <tr style={{ background: 'rgba(0, 240, 255, 0.08)' }}>
                <td><b style={{ color: '#00F0FF' }}>Tier 1: Rich CGM (Full ThaliTwin)</b></td>
                <td><b style={{ fontSize: '14px', color: '#00F0FF' }}>0.765</b></td>
                <td style={{ fontSize: '12px', color: 'var(--text-secondary)' }}>[0.718, 0.803]</td>
                <td><b style={{ color: '#10B981' }}>100.0% (Baseline)</b></td>
                <td><span className="badge" style={{ background: 'rgba(16, 185, 129, 0.2)', color: '#10B981' }}>Beats All Baselines (p &lt; 0.01)</span></td>
              </tr>
              <tr style={{ background: 'rgba(16, 185, 129, 0.08)' }}>
                <td><b style={{ color: '#10B981' }}>Tier 2: Frugal SMBG (Stepped-Care)</b></td>
                <td><b style={{ fontSize: '14px', color: '#10B981' }}>0.748</b></td>
                <td style={{ fontSize: '12px', color: 'var(--text-secondary)' }}>[0.704, 0.786]</td>
                <td><b style={{ color: '#10B981' }}>93.5% Retained</b></td>
                <td><span className="badge" style={{ background: 'rgba(16, 185, 129, 0.2)', color: '#10B981' }}>Beats All Baselines (p &lt; 0.01)</span></td>
              </tr>
              <tr>
                <td><span style={{ color: '#F59E0B', fontWeight: 600 }}>Tier 3: Triage (No Glucose Sensors)</span></td>
                <td><b>0.693</b></td>
                <td style={{ fontSize: '12px', color: 'var(--text-secondary)' }}>[0.640, 0.741]</td>
                <td><span style={{ color: '#F59E0B' }}>72.7% Retained</span></td>
                <td><span>Equal to persistence, beats carbs/EHR</span></td>
              </tr>
              <tr style={{ opacity: 0.85 }}>
                <td><i>Baseline 1: Naive Persistence (Last Glucose)</i></td>
                <td>0.696</td>
                <td style={{ fontSize: '12px', color: 'var(--text-muted)' }}>[0.652, 0.735]</td>
                <td>74.0%</td>
                <td style={{ color: 'var(--text-muted)' }}>Static momentum; fails to anticipate meals</td>
              </tr>
              <tr style={{ opacity: 0.85 }}>
                <td><i>Baseline 2: Meal Carbs-Only Model</i></td>
                <td>0.628</td>
                <td style={{ fontSize: '12px', color: 'var(--text-muted)' }}>[0.596, 0.661]</td>
                <td>48.3%</td>
                <td style={{ color: 'var(--text-muted)' }}>Univariate logistic model on carbs (g)</td>
              </tr>
              <tr style={{ opacity: 0.85 }}>
                <td><i>Baseline 3: Static Patient HbA1c-Only</i></td>
                <td>0.572</td>
                <td style={{ fontSize: '12px', color: 'var(--text-muted)' }}>[0.476, 0.654]</td>
                <td>27.2%</td>
                <td style={{ color: 'var(--text-muted)' }}>Fails to predict acute postprandial timing</td>
              </tr>
            </tbody>
          </table>
        </div>
        <p style={{ fontSize: '11px', color: 'var(--text-muted)', marginTop: '10px' }}>
          * Paired Delta (Tier 1 − Tier 2) = <b>0.017 [95% CI: 0.002 to 0.034]</b>. Stepping down to frugal SMBG produces a clinically negligible delta while reducing annual monitoring expense by 77%.
        </p>
      </div>

      {/* Grid: Multimodal Feature Ablation & Within-Person Stratification */}
      <div className="grid-2" style={{ marginBottom: '24px' }}>
        {/* Feature Ablation */}
        <div className="glass-panel">
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '12px' }}>
            <Layers size={18} color="#A855F7" />
            <h3 style={{ fontSize: '16px', fontWeight: 700 }}>2. Multimodal Feature Ablation Study</h3>
          </div>
          <p style={{ fontSize: '12px', color: 'var(--text-secondary)', marginBottom: '14px' }}>
            Proves that fusing nutritional composition with dynamic sensors outperforms single modalities:
          </p>

          <div style={{ display: 'flex', flexDirection: 'column', gap: '8px', fontSize: '12px' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', padding: '8px 12px', background: 'rgba(0, 240, 255, 0.08)', borderRadius: '8px', border: '1px solid rgba(0, 240, 255, 0.2)' }}>
              <span><b>Full Fused ThaliTwin (35 features)</b></span>
              <span style={{ color: '#00F0FF', fontWeight: 700 }}>0.765 AUROC [0.718 - 0.803]</span>
            </div>
            <div style={{ display: 'flex', justifyContent: 'space-between', padding: '8px 12px', background: 'rgba(255, 255, 255, 0.03)', borderRadius: '8px' }}>
              <span>Glucose Dynamics Only (5 features)</span>
              <span>0.695 AUROC [0.650 - 0.732]</span>
            </div>
            <div style={{ display: 'flex', justifyContent: 'space-between', padding: '8px 12px', background: 'rgba(255, 255, 255, 0.03)', borderRadius: '8px' }}>
              <span>Meals Composition Only (12 features)</span>
              <span>0.677 AUROC [0.643 - 0.711]</span>
            </div>
            <div style={{ display: 'flex', justifyContent: 'space-between', padding: '8px 12px', background: 'rgba(255, 255, 255, 0.03)', borderRadius: '8px' }}>
              <span>EHR Demographics Only (11 features)</span>
              <span>0.530 AUROC [0.451 - 0.610]</span>
            </div>
            <div style={{ display: 'flex', justifyContent: 'space-between', padding: '8px 12px', background: 'rgba(255, 255, 255, 0.03)', borderRadius: '8px' }}>
              <span>Wearables Only / Fitbit (6 features)</span>
              <span>0.524 AUROC [0.478 - 0.569]</span>
            </div>
          </div>
        </div>

        {/* Within-Person & Phenotype Stratification */}
        <div className="glass-panel">
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '12px' }}>
            <Award size={18} color="#10B981" />
            <h3 style={{ fontSize: '16px', fontWeight: 700 }}>3. Within-Person AUROC & Diagnostic Stratification</h3>
          </div>
          <p style={{ fontSize: '12px', color: 'var(--text-secondary)', marginBottom: '14px' }}>
            Controls for patient identity to prove discrimination is not driven by between-subject confounding:
          </p>

          <div style={{ display: 'flex', flexDirection: 'column', gap: '8px', fontSize: '12px' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', padding: '8px 12px', background: 'rgba(16, 185, 129, 0.08)', borderRadius: '8px', border: '1px solid rgba(16, 185, 129, 0.2)' }}>
              <span><b>Within-Person AUROC (N=34 Participants)</b></span>
              <span style={{ color: '#10B981', fontWeight: 700 }}>T1: 0.794 · T2: 0.762 (vs Carbs: 0.651)</span>
            </div>
            <div style={{ display: 'flex', justifyContent: 'space-between', padding: '8px 12px', background: 'rgba(255, 255, 255, 0.03)', borderRadius: '8px' }}>
              <span>Type 2 Diabetes Cohort (333 meals)</span>
              <span>T1: 0.760 · T2: 0.751 (vs HbA1c: 0.515)</span>
            </div>
            <div style={{ display: 'flex', justifyContent: 'space-between', padding: '8px 12px', background: 'rgba(255, 255, 255, 0.03)', borderRadius: '8px' }}>
              <span>Prediabetes Cohort (426 meals)</span>
              <span>T1: 0.726 · T2: 0.693 (vs Carbs: 0.612)</span>
            </div>
            <div style={{ display: 'flex', justifyContent: 'space-between', padding: '8px 12px', background: 'rgba(255, 255, 255, 0.03)', borderRadius: '8px' }}>
              <span>Normoglycemic Cohort (451 meals)</span>
              <span>T1: 0.790 · T2: 0.769 (vs Carbs: 0.648)</span>
            </div>
          </div>
        </div>
      </div>

      {/* Clinical Alert Metrics (Alarm Fatigue) & Noise Floor */}
      <div className="grid-2" style={{ marginBottom: '24px' }}>
        {/* Clinical Alert Metrics */}
        <div className="glass-panel">
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '12px' }}>
            <Clock size={18} color="#F59E0B" />
            <h3 style={{ fontSize: '16px', fontWeight: 700 }}>4. Clinical Alert Feasibility & Alarm Fatigue Cap</h3>
          </div>
          <p style={{ fontSize: '12px', color: 'var(--text-secondary)', marginBottom: '14px' }}>
            Optimized across <b>468.0 patient-days</b> to prevent clinician and patient alert fatigue:
          </p>

          <div className="grid-2" style={{ marginBottom: '14px' }}>
            <div className="stat-tile success">
              <div className="stat-label">Sensitivity (Caught Spikes)</div>
              <div className="stat-value">86.2%</div>
              <div className="stat-sub">At ≤ 0.5 False Alert/Day</div>
            </div>
            <div className="stat-tile cyan">
              <div className="stat-label">Early Warning Lead Time</div>
              <div className="stat-value">46.0 min</div>
              <div className="stat-sub">Prior to Peak Excursion</div>
            </div>
          </div>

          <p style={{ fontSize: '11px', color: 'var(--text-muted)' }}>
            Operating at a strict budget of 1 false alarm per 48 hours flags 86.2% of postprandial excursions with 46 minutes of actionable lead time.
          </p>
        </div>

        {/* Empirical Noise Floor Tile */}
        <div className="glass-panel">
          <h3 style={{ fontSize: '16px', fontWeight: 700, marginBottom: '12px', display: 'flex', alignItems: 'center', gap: '8px' }}>
            <Award size={18} color="#F59E0B" /> 5. Empirical Sensor Noise Floor Benchmark
          </h3>
          <p style={{ fontSize: '12px', color: 'var(--text-secondary)', marginBottom: '14px' }}>
            Computed across <b>{noiseFloor.pairs.toLocaleString()} simultaneous measurement pairs</b> (Dexcom G6 on abdomen vs Abbott Libre on arm):
          </p>

          <div className="grid-2" style={{ marginBottom: '14px' }}>
            <div className="stat-tile danger">
              <div className="stat-label">Sensor Disagreement RMSE</div>
              <div className="stat-value">{noiseFloor.rmse} mg/dL</div>
              <div className="stat-sub">Physical Ground Truth Floor</div>
            </div>
            <div className="stat-tile warning">
              <div className="stat-label">Cohort MARD</div>
              <div className="stat-value">{noiseFloor.mard}%</div>
              <div className="stat-sub">FDA Sensor Discordance</div>
            </div>
          </div>

          <p style={{ fontSize: '11px', color: 'var(--text-muted)' }}>
            Proves that human CGM hardware carries an intrinsic ~38 mg/dL physical noise floor between simultaneous sensors.
          </p>
        </div>
      </div>
    </div>
  );
}
