import React, { useState, useEffect } from 'react';
import Navbar from './components/Navbar';
import LoginPage from './pages/LoginPage';
import LiveMonitorPage from './pages/LiveMonitorPage';
import ROIConfigPage from './pages/ROIConfigPage';
import DashboardPage from './pages/DashboardPage';
import SessionsPage from './pages/SessionsPage';
import { api } from './services/api';
import { Layers } from 'lucide-react';

export default function App() {
  const [user, setUser] = useState(() => api.getStoredUser());
  const [activeTab, setActiveTab] = useState('sessions');
  const [currentSession, setCurrentSession] = useState(null);
  const [loading, setLoading] = useState(false);

  // Kiểm tra token khi khởi động
  useEffect(() => {
    const checkAuth = async () => {
      const u = await api.getMe();
      if (u) {
        setUser(u);
      } else {
        setUser(null);
      }
    };
    checkAuth();
  }, []);

  // Đồng bộ URL trình duyệt: khi chưa đăng nhập là /login, khi đã đăng nhập là /
  useEffect(() => {
    if (!user) {
      if (window.location.pathname !== '/login') {
        window.history.replaceState(null, '', '/login');
      }
    } else {
      if (window.location.pathname === '/login') {
        window.history.replaceState(null, '', '/');
      }
    }
  }, [user]);

  const handleLoginSuccess = (userData) => {
    setUser(userData);
    setActiveTab('sessions');
    window.history.replaceState(null, '', '/');
  };

  const handleLogout = () => {
    api.logout();
    setUser(null);
    setCurrentSession(null);
    window.history.replaceState(null, '', '/login');
  };

  const handleStatusChange = (newStatus) => {
    if (currentSession) {
      setCurrentSession((prev) => ({ ...prev, status: newStatus }));
    }
  };

  const handleConfigSaved = (newConfig) => {
    if (currentSession) {
      setCurrentSession((prev) => ({
        ...prev,
        config_json: JSON.stringify(newConfig)
      }));
    }
  };

  // Component thông báo khi chưa chọn phiên
  const renderNoSessionNotice = () => (
    <div style={{
      textAlign: 'center',
      padding: '4rem 2rem',
      maxWidth: '600px',
      margin: '2rem auto',
      backgroundColor: '#ffffff',
      borderRadius: '16px',
      border: '1px solid #e2e8f0',
      boxShadow: '0 4px 6px -1px rgba(0, 0, 0, 0.05)'
    }}>
      <div style={{
        width: '56px',
        height: '56px',
        borderRadius: '14px',
        backgroundColor: '#eff6ff',
        color: '#2563eb',
        display: 'inline-flex',
        alignItems: 'center',
        justifyContent: 'center',
        marginBottom: '1rem'
      }}>
        <Layers size={28} />
      </div>
      <h3 style={{ fontSize: '1.25rem', fontWeight: 800, color: '#0f172a', marginBottom: '0.5rem' }}>
        CHƯA CHỌN PHIÊN GIÁM SÁT
      </h3>
      <p style={{ fontSize: '0.875rem', color: '#64748b', marginBottom: '1.5rem', lineHeight: 1.5 }}>
        Vui lòng chọn một phiên giám sát có sẵn hoặc tạo phiên mới từ nguồn video để bắt đầu phân tích lưu lượng và đo vận tốc.
      </p>
      <button
        className="btn btn-primary"
        onClick={() => setActiveTab('sessions')}
        style={{ padding: '0.625rem 1.25rem', fontSize: '0.875rem' }}
      >
        <Layers size={16} />
        <span>Đi Tới Quản Lý Phiên</span>
      </button>
    </div>
  );

  // 1. Chưa đăng nhập -> Luôn hiển thị màn hình Login Portal chuyên nghiệp tại /login
  if (!user) {
    return <LoginPage onLoginSuccess={handleLoginSuccess} />;
  }

  // 2. Đã đăng nhập -> Hiển thị hệ thống nghiệp vụ
  return (
    <div className="app-container">
      <Navbar
        activeTab={activeTab}
        setActiveTab={setActiveTab}
        currentSession={currentSession}
        user={user}
        onLogout={handleLogout}
      />

      <main className="main-content">
        {loading ? (
          <div style={{ textAlign: 'center', padding: '4rem', color: '#94a3b8' }}>
            Đang kết nối tới Backend AI Traffic Service...
          </div>
        ) : (
          <>
            {activeTab === 'live' && (
              currentSession ? (
                <LiveMonitorPage
                  session={currentSession}
                  onStatusChange={handleStatusChange}
                />
              ) : renderNoSessionNotice()
            )}

            {activeTab === 'roi' && (
              currentSession ? (
                <ROIConfigPage
                  session={currentSession}
                  onSaved={handleConfigSaved}
                />
              ) : renderNoSessionNotice()
            )}

            {activeTab === 'dashboard' && (
              currentSession ? (
                <DashboardPage session={currentSession} />
              ) : renderNoSessionNotice()
            )}

            {activeTab === 'sessions' && (
              <SessionsPage
                currentSession={currentSession}
                onSelectSession={(sess) => {
                  setCurrentSession(sess);
                  setActiveTab('live');
                }}
              />
            )}
          </>
        )}
      </main>
    </div>
  );
}
