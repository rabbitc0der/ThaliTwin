import React, { useState } from 'react';
import { Search, AlertTriangle, CheckCircle, Clock, Activity, ArrowUpDown } from 'lucide-react';

export default function TriageWorklist({ patients, onSelectPatient, activeTier }) {
  const [phenotypeFilter, setPhenotypeFilter] = useState('ALL');
  const [searchQuery, setSearchQuery] = useState('');
  const [sortBy, setSortBy] = useState('risk'); // 'risk' or 'id' or 'hba1c'

  const filteredPatients = patients
    .filter(p => {
      if (phenotypeFilter !== 'ALL' && p.phenotype !== phenotypeFilter) return false;
      if (searchQuery.trim() !== '') {
        const q = searchQuery.toLowerCase();
        return p.id.toString().includes(q) || p.phenotype.toLowerCase().includes(q);
      }
      return true;
    })
    .sort((a, b) => {
      if (sortBy === 'risk') return b.estimatedRisk - a.estimatedRisk;
      if (sortBy === 'hba1c') return b.hba1c - a.hba1c;
      return a.id - b.id;
    });

  const criticalCount = patients.filter(p => p.triageStatus === 'CRITICAL').length;
  const elevatedCount = patients.filter(p => p.triageStatus === 'ELEVATED').length;
  const stableCount = patients.filter(p => p.triageStatus === 'STABLE').length;

  return (
    <div>
      {/* KPI Overview */}
      <div className="grid-4" style={{ marginBottom: '24px' }}>
        <div className="stat-tile danger">
          <div className="stat-label">Critical Priority (2h Spike &gt;75%)</div>
          <div className="stat-value">{criticalCount} Patients</div>
          <div className="stat-sub">Requires Immediate Nutrition Review</div>
        </div>
        <div className="stat-tile warning">
          <div className="stat-label">Elevated Risk (50-75%)</div>
          <div className="stat-value">{elevatedCount} Patients</div>
          <div className="stat-sub">Moderate Glycemic Excursion Risk</div>
        </div>
        <div className="stat-tile success">
          <div className="stat-label">Stable Homeostasis</div>
          <div className="stat-value">{stableCount} Patients</div>
          <div className="stat-sub">Within Target Glycemic Range</div>
        </div>
        <div className="stat-tile indigo">
          <div className="stat-label">Active Stepped Tier</div>
          <div className="stat-value">{activeTier}</div>
          <div className="stat-sub">Cost: {activeTier === 'T1_Rich' ? '₹10,000/mo' : (activeTier === 'T2_Frugal' ? '₹1,200/mo' : '₹0/mo')}</div>
        </div>
      </div>

      {/* Filter and Search Bar */}
      <div className="glass-panel" style={{ padding: '16px 20px', marginBottom: '20px' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '16px' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
            <span style={{ fontSize: '13px', color: 'var(--text-secondary)', fontWeight: 600 }}>FILTER:</span>
            {['ALL', 'Type 2 Diabetes', 'Prediabetes', 'Normoglycemic'].map(ph => (
              <button
                key={ph}
                onClick={() => setPhenotypeFilter(ph)}
                style={{
                  padding: '6px 14px',
                  borderRadius: '20px',
                  border: phenotypeFilter === ph ? '1px solid var(--c-cyan)' : '1px solid var(--border-subtle)',
                  background: phenotypeFilter === ph ? 'rgba(56, 189, 248, 0.2)' : 'rgba(15, 23, 42, 0.4)',
                  color: phenotypeFilter === ph ? '#38BDF8' : 'var(--text-secondary)',
                  fontSize: '12px',
                  fontWeight: 600,
                  cursor: 'pointer'
                }}
              >
                {ph === 'ALL' ? 'All (45 Adults)' : ph}
              </button>
            ))}
          </div>

          <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
            <div style={{ position: 'relative' }}>
              <Search size={16} style={{ position: 'absolute', left: '12px', top: '10px', color: 'var(--text-muted)' }} />
              <input
                type="text"
                placeholder="Search Subject ID..."
                value={searchQuery}
                onChange={e => setSearchQuery(e.target.value)}
                style={{
                  background: 'rgba(15, 23, 42, 0.6)',
                  border: '1px solid var(--border-subtle)',
                  borderRadius: '8px',
                  padding: '8px 12px 8px 36px',
                  color: 'white',
                  fontSize: '13px',
                  outline: 'none',
                  width: '180px'
                }}
              />
            </div>
            <button
              onClick={() => setSortBy(sortBy === 'risk' ? 'id' : 'risk')}
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: '6px',
                background: 'rgba(30, 41, 59, 0.6)',
                border: '1px solid var(--border-subtle)',
                borderRadius: '8px',
                padding: '8px 12px',
                color: 'var(--text-secondary)',
                fontSize: '12px',
                cursor: 'pointer'
              }}
            >
              <ArrowUpDown size={14} /> Sort: {sortBy.toUpperCase()}
            </button>
          </div>
        </div>
      </div>

      {/* Patient Table */}
      <div className="glass-panel" style={{ padding: 0, overflow: 'hidden' }}>
        <div className="table-container">
          <table className="custom-table">
          <thead>
            <tr>
              <th>Patient</th>
              <th>Phenotype</th>
              <th>HbA1c / Fasting</th>
              <th>BMI</th>
              <th>2h Excursion Risk</th>
              <th>Status</th>
              <th>Primary Physiological Driver</th>
              <th>Action</th>
            </tr>
          </thead>
          <tbody>
            {filteredPatients.map(p => {
              const badgeClass = p.phenotype === 'Type 2 Diabetes' ? 'badge-t2d' : (p.phenotype === 'Prediabetes' ? 'badge-predia' : 'badge-norm');
              const isCrit = p.triageStatus === 'CRITICAL';
              return (
                <tr key={p.id}>
                  <td>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                      {isCrit && <div className="pulse-dot" />}
                      <span style={{ fontWeight: 700, color: 'var(--c-cyan)' }}>Patient #{p.id}</span>
                      <span style={{ fontSize: '11px', color: 'var(--text-muted)' }}>({p.age}y, {p.gender})</span>
                    </div>
                  </td>
                  <td><span className={`badge ${badgeClass}`}>{p.phenotype}</span></td>
                  <td>
                    <span style={{ fontWeight: 600 }}>{p.hba1c}%</span>
                    <span style={{ fontSize: '11px', color: 'var(--text-muted)', marginLeft: '6px' }}>({p.fastingGlucose} mg/dL)</span>
                  </td>
                  <td>{p.bmi}</td>
                  <td>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                      <div style={{ width: '60px', height: '6px', background: 'rgba(51, 65, 85, 0.4)', borderRadius: '3px', overflow: 'hidden' }}>
                        <div style={{
                          width: `${p.estimatedRisk * 100}%`,
                          height: '100%',
                          background: p.estimatedRisk > 0.7 ? '#EF4444' : (p.estimatedRisk > 0.45 ? '#F59E0B' : '#10B981')
                        }} />
                      </div>
                      <span style={{ fontWeight: 700, fontSize: '13px' }}>{Math.round(p.estimatedRisk * 100)}%</span>
                    </div>
                  </td>
                  <td>
                    <span style={{
                      fontSize: '11px',
                      fontWeight: 700,
                      color: isCrit ? '#EF4444' : (p.triageStatus === 'ELEVATED' ? '#F59E0B' : '#10B981')
                    }}>
                      {p.triageStatus}
                    </span>
                  </td>
                  <td style={{ fontSize: '12px', color: 'var(--text-secondary)' }}>{p.primaryDriver}</td>
                  <td>
                    <button
                      className="btn-primary"
                      style={{ padding: '6px 14px', fontSize: '12px' }}
                      onClick={() => onSelectPatient(p.id)}
                    >
                      Open Twin
                    </button>
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
        </div>
      </div>
    </div>
  );
}
