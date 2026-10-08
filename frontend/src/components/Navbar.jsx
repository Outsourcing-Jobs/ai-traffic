import React from 'react';
import { Video, Settings2, BarChart3, Radio, Layers } from 'lucide-react';

export default function Navbar({ activeTab, setActiveTab, currentSession }) {
  return (
    <header className="header-nav">
      <div className="brand-logo">
        <Radio style={{ color: '#2563eb' }} size={24} />
        <span>AI TRAFFIC MONITOR</span>
      </div>

      <nav className="nav-links">
        <button
          id="nav-live-btn"
          className={`nav-btn ${activeTab === 'live' ? 'active' : ''}`}
          onClick={() => setActiveTab('live')}
        >
          <Video size={18} />
          <span>Giám Sát Live</span>
        </button>

        <button
          id="nav-roi-btn"
          className={`nav-btn ${activeTab === 'roi' ? 'active' : ''}`}
          onClick={() => setActiveTab('roi')}
        >
          <Settings2 size={18} />
          <span>Cấu Hình Vạch & ROI</span>
        </button>

        <button
          id="nav-dashboard-btn"
          className={`nav-btn ${activeTab === 'dashboard' ? 'active' : ''}`}
          onClick={() => setActiveTab('dashboard')}
        >
          <BarChart3 size={18} />
          <span>Dashboard Thống Kê</span>
        </button>

        <button
          id="nav-sessions-btn"
          className={`nav-btn ${activeTab === 'sessions' ? 'active' : ''}`}
          onClick={() => setActiveTab('sessions')}
        >
          <Layers size={18} />
          <span>Quản Lý Phiên</span>
        </button>
      </nav>

      <div style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
        {currentSession && (
          <div style={{ fontSize: '0.8125rem', color: '#64748b' }}>
            Phiên: <strong style={{ color: '#1d4ed8' }}>#{currentSession.id} - {currentSession.name}</strong>
          </div>
        )}
        <div className="live-badge">
          <span className="pulsing-dot"></span>
          <span>SYSTEM READY</span>
        </div>
      </div>
    </header>
  );
}
