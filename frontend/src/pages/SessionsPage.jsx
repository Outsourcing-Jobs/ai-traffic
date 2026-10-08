import React, { useState, useEffect } from 'react';
import { Plus, Trash2, Check, Play, Square, Cloud, Film, ExternalLink } from 'lucide-react';
import { api } from '../services/api';

export default function SessionsPage({ currentSession, onSelectSession }) {
  const [sessions, setSessions] = useState([]);
  const [videoSources, setVideoSources] = useState([]);
  const [loading, setLoading] = useState(false);

  // Form tạo phiên
  const [name, setName] = useState('');
  const [selectedVideoUrl, setSelectedVideoUrl] = useState('');
  const [customUrl, setCustomUrl] = useState('');

  // Form thêm link video mới vào CSDL
  const [showAddModal, setShowAddModal] = useState(false);
  const [newTitle, setNewTitle] = useState('');
  const [newUrl, setNewUrl] = useState('');
  const [newDesc, setNewDesc] = useState('');

  const loadData = async () => {
    setLoading(true);
    try {
      const [sessData, videoData] = await Promise.all([
        api.getSessions(),
        api.getVideoSources()
      ]);
      setSessions(sessData);
      setVideoSources(videoData);
      if (videoData.length > 0 && !selectedVideoUrl) {
        setSelectedVideoUrl(videoData[0].url);
      }
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, []);

  const handleCreateSession = async (e) => {
    e.preventDefault();
    if (!name.trim()) return;

    const finalUrl = selectedVideoUrl === 'custom' ? customUrl.trim() : selectedVideoUrl;
    if (!finalUrl) {
      alert('Vui lòng chọn hoặc nhập đường link video');
      return;
    }

    try {
      const newSess = await api.createSession({
        name,
        camera_url: finalUrl
      });
      setName('');
      await loadData();
      if (onSelectSession) onSelectSession(newSess);
    } catch (err) {
      alert(err.message);
    }
  };

  const handleSaveNewCloudVideo = async (e) => {
    e.preventDefault();
    if (!newTitle.trim() || !newUrl.trim()) return;

    try {
      const created = await api.addVideoSource({
        title: newTitle.trim(),
        url: newUrl.trim(),
        description: newDesc.trim() || null
      });
      setNewTitle('');
      setNewUrl('');
      setNewDesc('');
      setShowAddModal(false);
      await loadData();
      setSelectedVideoUrl(created.url);
      alert('Đã lưu link video vào CSDL thành công!');
    } catch (err) {
      alert(err.message);
    }
  };

  const handleDeleteVideoSource = async (id) => {
    if (!confirm('Bạn có chắc muốn xóa link video này khỏi CSDL?')) return;
    try {
      await api.deleteVideoSource(id);
      loadData();
    } catch (err) {
      alert(err.message);
    }
  };

  const handleDeleteSession = async (id) => {
    if (!confirm('Bạn có chắc muốn xóa phiên này và toàn bộ dữ liệu thống kê liên quan?')) return;
    try {
      await api.deleteSession(id);
      loadData();
    } catch (err) {
      alert(err.message);
    }
  };

  const handleStartSession = async (id) => {
    try {
      await api.startSession(id);
      loadData();
    } catch (err) {
      alert(err.message);
    }
  };

  const handleStopSession = async (id) => {
    try {
      await api.stopSession(id);
      loadData();
    } catch (err) {
      alert(err.message);
    }
  };

  return (
    <div style={{ maxWidth: '1280px', margin: '0 auto', display: 'flex', flexDirection: 'column', gap: '1.75rem' }}>
      <div style={{ display: 'grid', gridTemplateColumns: 'minmax(0, 1.25fr) minmax(0, 2fr)', gap: '1.5rem' }}>
        {/* Form Tạo Phiên Mới */}
        <div className="card">
          <h2 style={{ fontSize: '1.15rem', fontWeight: 800, color: '#0f172a', marginBottom: '0.375rem' }}>
            TẠO PHIÊN GIÁM SÁT MỚI
          </h2>
          <p style={{ fontSize: '0.875rem', color: '#64748b', marginBottom: '1.25rem' }}>
            Chọn nguồn video từ Cloud đã lưu trong CSDL hoặc dán link URL mới.
          </p>

          <form onSubmit={handleCreateSession} style={{ display: 'flex', flexDirection: 'column', gap: '1.15rem' }}>
            <div>
              <label style={{ display: 'block', fontSize: '0.8125rem', fontWeight: 700, color: '#475569', marginBottom: '0.375rem' }}>
                Tên Phiên Giám Sát:
              </label>
              <input
                id="session-name-input"
                type="text"
                placeholder="VD: Cao tốc Hà Nội - Giờ cao điểm"
                value={name}
                onChange={(e) => setName(e.target.value)}
                required
                style={{
                  width: '100%',
                  padding: '0.625rem 0.875rem',
                  borderRadius: '8px',
                  background: '#ffffff',
                  border: '1px solid #cbd5e1',
                  color: '#0f172a',
                  fontSize: '0.875rem'
                }}
              />
            </div>

            <div>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.375rem' }}>
                <label style={{ fontSize: '0.8125rem', fontWeight: 700, color: '#475569' }}>
                  Nguồn Video (Chọn từ CSDL):
                </label>
                <button
                  type="button"
                  onClick={() => setShowAddModal(!showAddModal)}
                  style={{
                    background: 'transparent',
                    border: 'none',
                    color: '#2563eb',
                    fontSize: '0.8125rem',
                    fontWeight: 700,
                    cursor: 'pointer',
                    display: 'flex',
                    alignItems: 'center',
                    gap: '0.25rem'
                  }}
                >
                  <Plus size={14} />
                  <span>Lưu link Cloud mới</span>
                </button>
              </div>

              <select
                id="video-source-select"
                value={selectedVideoUrl}
                onChange={(e) => setSelectedVideoUrl(e.target.value)}
                style={{
                  width: '100%',
                  padding: '0.625rem 0.875rem',
                  borderRadius: '8px',
                  background: '#ffffff',
                  border: '1px solid #cbd5e1',
                  color: '#0f172a',
                  fontSize: '0.875rem',
                  fontWeight: 600
                }}
              >
                {videoSources.map((v) => (
                  <option key={v.id} value={v.url}>
                    {v.url.startsWith('http') ? '☁️ [Cloud] ' : '📁 [Local] '}
                    {v.title}
                  </option>
                ))}
                <option value="custom">➕ Nhập link URL khác trực tiếp...</option>
              </select>
            </div>

            {selectedVideoUrl === 'custom' && (
              <div>
                <label style={{ display: 'block', fontSize: '0.8125rem', fontWeight: 700, color: '#475569', marginBottom: '0.375rem' }}>
                  Dán đường dẫn Cloud / RTSP URL:
                </label>
                <input
                  type="text"
                  placeholder="https://res.cloudinary.com/.../traffic.mp4"
                  value={customUrl}
                  onChange={(e) => setCustomUrl(e.target.value)}
                  required
                  style={{
                    width: '100%',
                    padding: '0.625rem 0.875rem',
                    borderRadius: '8px',
                    background: '#ffffff',
                    border: '1px solid #cbd5e1',
                    color: '#0f172a',
                    fontSize: '0.875rem',
                    fontFamily: 'monospace'
                  }}
                />
              </div>
            )}

            <button id="create-session-btn" type="submit" className="btn btn-primary" style={{ marginTop: '0.25rem' }}>
              <Plus size={16} />
              <span>Tạo & Bắt Đầu Phiên Này</span>
            </button>
          </form>
        </div>

        {/* Danh Sách Các Phiên Giám Sát */}
        <div className="card">
          <h2 style={{ fontSize: '1.15rem', fontWeight: 800, color: '#0f172a', marginBottom: '1rem' }}>
            DANH SÁCH PHIÊN GIÁM SÁT ĐÃ LƯU
          </h2>
          <table className="custom-table">
            <thead>
              <tr>
                <th>ID</th>
                <th>Tên Phiên</th>
                <th>Trạng Thái</th>
                <th>Thời Gian</th>
                <th>Thao Tác</th>
              </tr>
            </thead>
            <tbody>
              {sessions.map((s) => {
                const isSelected = currentSession?.id === s.id;
                const isRunning = s.status === 'running';

                return (
                  <tr key={s.id} style={{ background: isSelected ? '#eff6ff' : 'transparent' }}>
                    <td className="font-mono">#{s.id}</td>
                    <td>
                      <div style={{ fontWeight: 700, color: isSelected ? '#1d4ed8' : '#0f172a' }}>{s.name}</div>
                      <div style={{ fontSize: '0.75rem', color: '#64748b', fontFamily: 'monospace', maxWidth: '280px', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }} title={s.camera_url}>
                        {s.camera_url?.startsWith('http') ? '☁️ ' : '📁 '}
                        {s.camera_url}
                      </div>
                    </td>
                    <td>
                      <span
                        className="live-badge"
                        style={{
                          backgroundColor: isRunning ? '#ecfdf5' : '#f1f5f9',
                          color: isRunning ? '#059669' : '#64748b',
                          borderColor: isRunning ? '#a7f3d0' : '#e2e8f0'
                        }}
                      >
                        {s.status.toUpperCase()}
                      </span>
                    </td>
                    <td style={{ fontSize: '0.75rem', color: '#64748b' }}>
                      {new Date(s.started_at).toLocaleTimeString('vi-VN', { hour12: false })}
                    </td>
                    <td>
                      <div style={{ display: 'flex', gap: '0.4rem' }}>
                        <button
                          className="btn btn-secondary"
                          style={{ padding: '0.35rem 0.6rem', fontSize: '0.75rem' }}
                          onClick={() => onSelectSession(s)}
                          title="Chọn phiên này làm phiên hiển thị"
                        >
                          <Check size={14} />
                          <span>{isSelected ? 'Đang Xem' : 'Xem'}</span>
                        </button>

                        {!isRunning ? (
                          <button
                            className="btn btn-success"
                            style={{ padding: '0.35rem 0.6rem', fontSize: '0.75rem' }}
                            onClick={() => handleStartSession(s.id)}
                            title="Bắt đầu phân tích"
                          >
                            <Play size={14} />
                          </button>
                        ) : (
                          <button
                            className="btn btn-danger"
                            style={{ padding: '0.35rem 0.6rem', fontSize: '0.75rem' }}
                            onClick={() => handleStopSession(s.id)}
                            title="Dừng phân tích"
                          >
                            <Square size={14} />
                          </button>
                        )}

                        <button
                          className="btn btn-secondary"
                          style={{ padding: '0.35rem 0.6rem', fontSize: '0.75rem', color: '#e11d48' }}
                          onClick={() => handleDeleteSession(s.id)}
                          title="Xóa phiên"
                        >
                          <Trash2 size={14} />
                        </button>
                      </div>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </div>

      {/* Khu vực Quản lý Kho Link Video Cloud (Lưu trong CSDL) */}
      <div className="card">
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
            <Cloud size={20} style={{ color: '#2563eb' }} />
            <h3 style={{ fontSize: '1.05rem', fontWeight: 800, color: '#0f172a' }}>
              KHO LINK VIDEO ĐÃ LƯU TRONG CSDL (VIDEO_SOURCES TABLE)
            </h3>
          </div>

          <button
            className="btn btn-secondary"
            onClick={() => setShowAddModal(!showAddModal)}
          >
            <Plus size={16} />
            <span>{showAddModal ? 'Đóng Form' : '+ Lưu Link Video Cloud Mới Vào DB'}</span>
          </button>
        </div>

        {/* Form Thêm Link Video */}
        {showAddModal && (
          <form
            onSubmit={handleSaveNewCloudVideo}
            style={{
              background: '#f8fafc',
              padding: '1.25rem',
              borderRadius: '10px',
              border: '1px solid #e2e8f0',
              marginBottom: '1.25rem',
              display: 'grid',
              gridTemplateColumns: '1fr 2fr 1fr auto',
              gap: '1rem',
              alignItems: 'end'
            }}
          >
            <div>
              <label style={{ display: 'block', fontSize: '0.8125rem', fontWeight: 700, color: '#475569', marginBottom: '0.25rem' }}>
                Tên Video:
              </label>
              <input
                type="text"
                placeholder="VD: Cầu Nhật Tân - Chiều tối"
                value={newTitle}
                onChange={(e) => setNewTitle(e.target.value)}
                required
                style={{ width: '100%', padding: '0.5rem', borderRadius: '6px', border: '1px solid #cbd5e1' }}
              />
            </div>

            <div>
              <label style={{ display: 'block', fontSize: '0.8125rem', fontWeight: 700, color: '#475569', marginBottom: '0.25rem' }}>
                Đường Dẫn URL (Cloudinary / S3 / CDN / Link MP4):
              </label>
              <input
                type="text"
                placeholder="https://.../video.mp4"
                value={newUrl}
                onChange={(e) => setNewUrl(e.target.value)}
                required
                style={{ width: '100%', padding: '0.5rem', borderRadius: '6px', border: '1px solid #cbd5e1', fontFamily: 'monospace' }}
              />
            </div>

            <div>
              <label style={{ display: 'block', fontSize: '0.8125rem', fontWeight: 700, color: '#475569', marginBottom: '0.25rem' }}>
                Mô tả (tùy chọn):
              </label>
              <input
                type="text"
                placeholder="Góc nhìn trên cao"
                value={newDesc}
                onChange={(e) => setNewDesc(e.target.value)}
                style={{ width: '100%', padding: '0.5rem', borderRadius: '6px', border: '1px solid #cbd5e1' }}
              />
            </div>

            <button type="submit" className="btn btn-primary" style={{ height: '38px' }}>
              <Plus size={16} />
              <span>Lưu Vào DB</span>
            </button>
          </form>
        )}

        {/* Danh sách Video Sources */}
        <table className="custom-table">
          <thead>
            <tr>
              <th>ID</th>
              <th>Tên Video Nguồn</th>
              <th>Đường Link URL</th>
              <th>Phân Loại</th>
              <th>Mô Tả</th>
              <th>Thao Tác</th>
            </tr>
          </thead>
          <tbody>
            {videoSources.map((v) => (
              <tr key={v.id}>
                <td className="font-mono">#{v.id}</td>
                <td style={{ fontWeight: 700, color: '#0f172a' }}>{v.title}</td>
                <td>
                  <a
                    href={v.url}
                    target="_blank"
                    rel="noreferrer"
                    style={{ color: '#2563eb', display: 'flex', alignItems: 'center', gap: '0.25rem', fontFamily: 'monospace', fontSize: '0.8125rem', textDecoration: 'none' }}
                  >
                    <span style={{ maxWidth: '320px', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                      {v.url}
                    </span>
                    <ExternalLink size={13} />
                  </a>
                </td>
                <td>
                  {v.url.startsWith('http') ? (
                    <span className="badge-vehicle" style={{ background: '#dbeafe', color: '#1e40af' }}>Cloud Link</span>
                  ) : (
                    <span className="badge-vehicle" style={{ background: '#f1f5f9', color: '#475569' }}>Local File</span>
                  )}
                </td>
                <td style={{ fontSize: '0.8125rem', color: '#64748b' }}>{v.description || '--'}</td>
                <td>
                  <button
                    className="btn btn-secondary"
                    style={{ padding: '0.3rem 0.5rem', fontSize: '0.75rem', color: '#e11d48' }}
                    onClick={() => handleDeleteVideoSource(v.id)}
                    title="Xóa link khỏi DB"
                  >
                    <Trash2 size={13} />
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
