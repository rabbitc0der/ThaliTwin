import React, { useState } from 'react';
import clinicalData from './data/clinicalData.json';
import TriageWorklist from './components/TriageWorklist';
import TwinTrajectoryView from './components/TwinTrajectoryView';
import ThaliWhatIfSimulator from './components/ThaliWhatIfSimulator';
import SteppedCareEconomics from './components/SteppedCareEconomics';
import TrustAndEvidence from './components/TrustAndEvidence';
import RegulatorySaMDView from './components/RegulatorySaMDView';

import { Users, Activity, Utensils, IndianRupee, ShieldCheck, ShieldAlert } from 'lucide-react';

export default function App() {
  const [activeTab, setActiveTab] = useState('triage');
  const [selectedPatientId, setSelectedPatientId] = useState(1);
  const [activeTier, setActiveTier] = useState('T2_Frugal');

  const { patients, sampleTrajectories, dishes, economics, evidence } = clinicalData;

  const currentPatient = patients.find(p => p.id === selectedPatientId) || patients[0];
  const currentTrajectory = sampleTrajectories[selectedPatientId.toString()] || sampleTrajectories['1'] || [];

  const handleSelectPatientFromTriage = (pid) => {
    setSelectedPatientId(pid);
    setActiveTab('twin');
  };

  const handleOpenWhatIfForPatient = () => {
    setActiveTab('whatif');
  };

  return (
    <>
      <div className="ambient-glow" />

      <div className="app-container">
        {/* Top Header */}
        <header className="app-header">
          <div className="brand-section">
            <div className="brand-logo">🩺</div>
            <div className="brand-text">
              <h1>ThaliTwin Clinical Console</h1>
              <p>Stepped-Care Frugal Digital Twin for India · Happiest Health Digital Twin Challenge 2026</p>
            </div>
          </div>

          <div className="header-badges">
            <span className="badge badge-norm">Live Trial Data (45 Adults)</span>
            <span className="badge badge-tier">Stepped-Care Mode: Active</span>
          </div>
        </header>

        {/* Navigation Tabs */}
        <nav className="nav-tabs">
          <button
            className={`nav-tab-btn ${activeTab === 'triage' ? 'active' : ''}`}
            onClick={() => setActiveTab('triage')}
          >
            <Users size={16} /> 1. Patient Ward Triage
          </button>

          <button
            className={`nav-tab-btn ${activeTab === 'twin' ? 'active' : ''}`}
            onClick={() => setActiveTab('twin')}
          >
            <Activity size={16} /> 2. Digital Twin & Live Tier Slider
          </button>

          <button
            className={`nav-tab-btn ${activeTab === 'whatif' ? 'active' : ''}`}
            onClick={() => setActiveTab('whatif')}
          >
            <Utensils size={16} /> 3. Indian Thali What-If Simulator
          </button>

          <button
            className={`nav-tab-btn ${activeTab === 'economics' ? 'active' : ''}`}
            onClick={() => setActiveTab('economics')}
          >
            <IndianRupee size={16} /> 4. Stepped-Care Health Economics
          </button>

          <button
            className={`nav-tab-btn ${activeTab === 'trust' ? 'active' : ''}`}
            onClick={() => setActiveTab('trust')}
          >
            <ShieldCheck size={16} /> 5. Scientific Evidence & Trust Pack
          </button>

          <button
            className={`nav-tab-btn ${activeTab === 'samd' ? 'active' : ''}`}
            onClick={() => setActiveTab('samd')}
          >
            <ShieldAlert size={16} /> 6. Regulatory SaMD & Audit
          </button>
        </nav>

        {/* Tab Views */}
        <main>
          {activeTab === 'triage' && (
            <TriageWorklist
              patients={patients}
              onSelectPatient={handleSelectPatientFromTriage}
              activeTier={activeTier}
            />
          )}

          {activeTab === 'twin' && (
            <TwinTrajectoryView
              patient={currentPatient}
              trajectoryPoints={currentTrajectory}
              onOpenWhatIf={handleOpenWhatIfForPatient}
            />
          )}

          {activeTab === 'whatif' && (
            <ThaliWhatIfSimulator
              dishes={dishes}
              defaultPatient={currentPatient}
            />
          )}

          {activeTab === 'economics' && (
            <SteppedCareEconomics
              economicsData={economics}
            />
          )}

          {activeTab === 'trust' && (
            <TrustAndEvidence
              evidenceData={evidence}
            />
          )}

          {activeTab === 'samd' && (
            <RegulatorySaMDView />
          )}
        </main>
      </div>
    </>
  );
}

