import React from 'react';
import { 
  Video, 
  Settings2, 
  BarChart3, 
  Radio, 
  Layers, 
  AlertTriangle, 
  LogOut, 
  UserCheck 
} from 'lucide-react';

export default function Navbar({ activeTab, setActiveTab, currentSession, user, onLogout }) {
  return (
    <header className="header-nav">
      <div 
        className="brand-logo" 
        style={{ cursor: user ? 'pointer' : 'default' }}
        onClick={() => user && setActiveTab('sessions')}
      >
        <Radio style={{ color: '#2563eb' }} size={24} />
        <span>AI TRAFFIC MONITOR</span>
      </div>

      <nav className="nav-links">
        {/* Các tab nghiệp vụ hiển thị khi ĐÃ ĐĂNG NHẬP */}
        {user && (
          <>
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
              id="nav-violations-btn"
              className={`nav-btn ${activeTab === 'violations' ? 'active' : ''}`}
              onClick={() => setActiveTab('violations')}
            >
              <AlertTriangle size={18} style={{ color: activeTab === 'violations' ? '#ef4444' : '#f87171' }} />
              <span>Vi Phạm Tốc Độ</span>
            </button>

            <button
              id="nav-sessions-btn"
              className={`nav-btn ${activeTab === 'sessions' ? 'active' : ''}`}
              onClick={() => setActiveTab('sessions')}
            >
              <Layers size={18} />
              <span>Quản Lý Phiên</span>
            </button>
          </>
        )}
      </nav>

      {/* Cột phải: Thông tin phiên & Tài khoản */}
      <div style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
        {user ? (
          <>
            {currentSession && (
              <div style={{ fontSize: '0.8125rem', color: '#64748b' }}>
                Phiên: <strong style={{ color: '#1d4ed8' }}>#{currentSession.id} - {currentSession.name}</strong>
              </div>
            )}

            <div style={{
              display: 'flex',
              alignItems: 'center',
              gap: '0.5rem',
              backgroundColor: '#f1f5f9',
              padding: '0.35rem 0.75rem',
              borderRadius: '9999px',
              fontSize: '0.8125rem',
              fontWeight: 700,
              color: '#334155'
            }}>
              <UserCheck size={16} color="#2563eb" />
              <span>{user.username}</span>
            </div>

            <button
              onClick={onLogout}
              className="btn btn-secondary"
              style={{
                padding: '0.35rem 0.65rem',
                fontSize: '0.75rem',
                display: 'flex',
                alignItems: 'center',
                gap: '0.35rem',
                color: '#e11d48',
                borderColor: '#fecaca'
              }}
              title="Đăng xuất khỏi hệ thống"
            >
              <LogOut size={14} />
              <span>Thoát</span>
            </button>
          </>
        ) : (
          <span style={{
            fontSize: '0.8125rem',
            color: '#64748b',
            backgroundColor: '#f1f5f9',
            padding: '0.35rem 0.75rem',
            borderRadius: '9999px',
            fontWeight: 600
          }}>
            Hệ Thống ITS
          </span>
        )}
      </div>
    </header>
  );
}
