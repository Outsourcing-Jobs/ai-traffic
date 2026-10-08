import React, { useState, useEffect } from 'react';
import Navbar from './components/Navbar';
import LiveMonitorPage from './pages/LiveMonitorPage';
import ROIConfigPage from './pages/ROIConfigPage';
import DashboardPage from './pages/DashboardPage';
import SessionsPage from './pages/SessionsPage';
import { api } from './services/api';

export default function App() {
  const [activeTab, setActiveTab] = useState('live');
  const [currentSession, setCurrentSession] = useState(null);
  const [loading, setLoading] = useState(true);

  // Khởi tạo: Lấy session đầu tiên hoặc tạo session mặc định
  useEffect(() => {
    const initSession = async () => {
      try {
        const sessions = await api.getSessions();
        if (sessions && sessions.length > 0) {
          setCurrentSession(sessions[0]);
        } else {
          // Tạo session mặc định ban đầu nếu chưa có
          const newSess = await api.createSession({
            name: 'Giám Sát Mặc Định 01',
            camera_url: 'data/videos/traffic.mp4'
          });
          setCurrentSession(newSess);
        }
      } catch (err) {
        console.error('Lỗi khởi tạo session:', err);
      } finally {
        setLoading(false);
      }
    };

    initSession();
  }, []);

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

  return (
    <div className="app-container">
      <Navbar
        activeTab={activeTab}
        setActiveTab={setActiveTab}
        currentSession={currentSession}
      />

      <main className="main-content">
        {loading ? (
          <div style={{ textAlign: 'center', padding: '4rem', color: '#94a3b8' }}>
            Đang kết nối tới Backend AI Traffic Service...
          </div>
        ) : (
          <>
            {activeTab === 'live' && (
              <LiveMonitorPage
                session={currentSession}
                onStatusChange={handleStatusChange}
              />
            )}

            {activeTab === 'roi' && (
              <ROIConfigPage
                session={currentSession}
                onSaved={handleConfigSaved}
              />
            )}

            {activeTab === 'dashboard' && (
              <DashboardPage session={currentSession} />
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
