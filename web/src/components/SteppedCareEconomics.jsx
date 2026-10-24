import React, { useState } from 'react';
import { IndianRupee, TrendingUp, DollarSign, Award, CheckCircle, PieChart, Users } from 'lucide-react';

export default function SteppedCareEconomics({ economicsData }) {
  const [cohortSize, setCohortSize] = useState(50); // Default clinic size: 50 patients

  // Stepped-Care Economics: Tier 1 (₹10,000/mo = ₹1,20,000/yr) vs Tier 2 (₹2,296/mo = ₹27,560/yr all-in)
  // Net annual savings per patient = ₹92,440/year (77% net reduction)
  const monthlySavingsPerPatient = 7704;
  const annualSavingsPerPatient = 92440;
  const totalCohortAnnualSavings = annualSavingsPerPatient * cohortSize;

  return (
    <div>
      {/* Header Banner */}
      <div className="glass-panel" style={{ padding: '20px 24px', marginBottom: '20px' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '16px' }}>
          <div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
              <IndianRupee size={22} color="#10B981" />
              <h2 style={{ fontSize: '20px', fontWeight: 700 }}>Stepped-Care Health Economics & Cost-Effectiveness Frontier</h2>
            </div>
            <p style={{ fontSize: '13px', color: 'var(--text-secondary)', marginTop: '4px' }}>
              Quantitative evidence proving that stepping down from continuous CGM to frugal glucometers retains 93.5% above-chance discrimination while cutting out-of-pocket costs by 77%.
            </p>
          </div>
          <span className="badge" style={{ background: 'rgba(56, 189, 248, 0.15)', color: '#38BDF8', border: '1px solid rgba(56, 189, 248, 0.3)' }}>
            <Award size={14} /> ICMR-INDIAB Economic Alignment
          </span>
        </div>
      </div>

      {/* Cross-Tier Stepped-Care Table */}
      <div className="glass-panel" style={{ padding: 0, overflow: 'hidden', marginBottom: '24px' }}>
        <table className="custom-table">
          <thead>
            <tr>
              <th>Stepped-Care Tier</th>
              <th>Sensor Architecture</th>
              <th>Monthly Patient Cost</th>
              <th>Excursion AUROC</th>
              <th>Sensitivity</th>
              <th>RMSE (mg/dL)</th>
              <th>Accuracy Retained</th>
              <th>Cost Reduction</th>
            </tr>
          </thead>
          <tbody>
            {economicsData.map((t, idx) => (
              <tr key={idx} style={{ background: t.tier.includes('T2') ? 'rgba(16, 185, 129, 0.06)' : 'transparent' }}>
                <td>
                  <span style={{ fontWeight: 700, color: t.tier.includes('T1') ? '#6366F1' : (t.tier.includes('T2') ? '#10B981' : '#F59E0B') }}>
                    {t.tier}
                  </span>
                </td>
                <td style={{ fontSize: '12px', color: 'var(--text-secondary)' }}>{t.sensors}</td>
                <td>
                  <span style={{ fontWeight: 700, color: t.monthlyCost === 0 ? '#38BDF8' : 'var(--text-primary)' }}>
                    {t.monthlyCost === 0 ? '₹0 / mo' : `₹${t.monthlyCost.toLocaleString()} / mo`}
                  </span>
                </td>
                <td><span style={{ fontWeight: 700 }}>{t.auroc.toFixed(3)}</span></td>
                <td>{t.sensitivity.toFixed(3)}</td>
                <td>{t.peakRmse.toFixed(2)}</td>
                <td>
                  <span style={{ fontWeight: 700, color: t.retainedPct > 95 ? '#10B981' : '#38BDF8' }}>
                    {t.retainedPct.toFixed(1)}%
                  </span>
                </td>
                <td>
                  <span style={{ fontWeight: 700, color: t.savingsPct > 0 ? '#10B981' : 'var(--text-muted)' }}>
                    {t.savingsPct > 0 ? `-${t.savingsPct.toFixed(0)}%` : 'Baseline'}
                  </span>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* Interactive Clinic Out-of-Pocket Savings Calculator */}
      <div className="grid-2">
        <div className="glass-panel">
          <div style={{ display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '16px' }}>
            <Users size={20} color="#38BDF8" />
            <h3 style={{ fontSize: '16px', fontWeight: 700 }}>Clinic Cohort Direct Savings Calculator</h3>
          </div>

          <label style={{ fontSize: '12px', color: 'var(--text-secondary)', display: 'block', marginBottom: '6px' }}>
            Number of Active Diabetic Patients in Clinic Cohort:
          </label>
          <div style={{ display: 'flex', alignItems: 'center', gap: '16px', marginBottom: '20px' }}>
            <input
              type="range"
              min="10"
              max="500"
              step="10"
              value={cohortSize}
              onChange={e => setCohortSize(parseInt(e.target.value))}
              style={{ flex: 1, accentColor: '#10B981' }}
            />
            <span style={{ fontSize: '16px', fontWeight: 700, color: 'var(--c-cyan)', minWidth: '90px' }}>
              {cohortSize} Patients
            </span>
          </div>

          <div style={{ background: 'rgba(15, 23, 42, 0.6)', border: '1px solid var(--border-subtle)', borderRadius: '12px', padding: '16px' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '10px' }}>
              <span style={{ fontSize: '13px', color: 'var(--text-secondary)' }}>Monthly Net Savings per Patient:</span>
              <span style={{ fontSize: '14px', fontWeight: 700, color: '#10B981' }}>₹7,704 / month</span>
            </div>
            <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '10px' }}>
              <span style={{ fontSize: '13px', color: 'var(--text-secondary)' }}>Annual Net Savings per Patient:</span>
              <span style={{ fontSize: '14px', fontWeight: 700, color: '#10B981' }}>₹92,440 / year (77% save)</span>
            </div>
            <hr style={{ borderColor: 'var(--border-subtle)', margin: '12px 0' }} />
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <span style={{ fontSize: '14px', fontWeight: 600, color: '#F8FAFC' }}>Total Cohort Annual Out-of-Pocket Savings:</span>
              <span style={{ fontSize: '20px', fontWeight: 800, color: '#38BDF8' }}>
                ₹{(totalCohortAnnualSavings / 100000).toFixed(1)} Lakhs
              </span>
            </div>
          </div>
        </div>

        {/* The Frontier Plot */}
        <div className="glass-panel">
          <div style={{ display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '16px' }}>
            <TrendingUp size={20} color="#F59E0B" />
            <h3 style={{ fontSize: '16px', fontWeight: 700 }}>Cost-Effectiveness Frontier</h3>
          </div>

          {/* SVG Frontier Plot */}
          <svg viewBox="0 0 450 200" style={{ width: '100%', height: 'auto' }}>
            <line x1="60" y1="30" x2="60" y2="160" stroke="#334155" strokeWidth="1" />
            <line x1="60" y1="160" x2="420" y2="160" stroke="#334155" strokeWidth="1" />

            {/* Y axis labels (AUROC) */}
            <text x="50" y="35" fill="#64748B" fontSize="9" textAnchor="end">0.80</text>
            <text x="50" y="95" fill="#64748B" fontSize="9" textAnchor="end">0.72</text>
            <text x="50" y="155" fill="#64748B" fontSize="9" textAnchor="end">0.65</text>

            {/* X axis labels (Monthly Cost) */}
            <text x="80" y="175" fill="#64748B" fontSize="9" textAnchor="middle">₹0</text>
            <text x="210" y="175" fill="#64748B" fontSize="9" textAnchor="middle">₹2,296 (T2)</text>
            <text x="370" y="175" fill="#64748B" fontSize="9" textAnchor="middle">₹10,000 (T1)</text>

            {/* Connecting curve */}
            <path d="M 80 130 Q 210 60 370 52" fill="none" stroke="#38BDF8" strokeWidth="2.5" />

            {/* T3 point */}
            <circle cx="80" cy="130" r="5" fill="#F59E0B" />
            <text x="80" y="120" fill="#FBBF24" fontSize="9" fontWeight="700" textAnchor="middle">T3: 0.693</text>

            {/* T2 point (The Sweet Spot) */}
            <circle cx="210" cy="60" r="7" fill="#10B981" stroke="#FFFFFF" strokeWidth="1.5" />
            <text x="210" y="48" fill="#34D399" fontSize="10" fontWeight="800" textAnchor="middle">T2: 0.748 (93.5% ret.)</text>

            {/* T1 point */}
            <circle cx="370" cy="52" r="5" fill="#6366F1" />
            <text x="370" y="42" fill="#A5B4FC" fontSize="9" fontWeight="700" textAnchor="middle">T1: 0.765</text>
          </svg>

          <p style={{ fontSize: '11px', color: 'var(--text-muted)', textAlign: 'center', marginTop: '4px' }}>
            The Stepped-Care Frontier: Transitioning from perpetual CGM (₹10,000/mo) to frugal stepped-care (₹2,296/mo) retains 93.5% of above-chance discrimination while saving ₹92,440/patient/year.
          </p>
        </div>
      </div>
    </div>
  );
}
