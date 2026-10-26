import React, { useState, useEffect } from 'react';
import {
  Play, Square, RefreshCw, AlertCircle, Camera, Zap,
  CheckCircle2, FolderCheck, Cloud, ExternalLink, Settings,
  Eye, EyeOff, Info, Check
} from 'lucide-react';
import { api } from '../services/api';

export default function VideoStream({ session, onStatusChange }) {
  const [streamError, setStreamError] = useState(false);
  const [loading, setLoading] = useState(false);
  const [captureLoading, setCaptureLoading] = useState(false);
  const [batchLoading, setBatchLoading] = useState(false);
  const [datasetToast, setDatasetToast] = useState(null);
  const [datasetSummary, setDatasetSummary] = useState(null);
  const [cloudinaryStatus, setCloudinaryStatus] = useState(null);
  const [showCloudModal, setShowCloudModal] = useState(false);
  const [cloudForm, setCloudForm] = useState({ cloud_name: 'djesc4hru', api_key: '', api_secret: '' });
  const [showSecret, setShowSecret] = useState(false);
  const [savingCloud, setSavingCloud] = useState(false);


  const isRunning = session?.status === 'running';
  const streamUrl = session ? api.getStreamUrl(session.id) : '';

  // Nạp thống kê dataset & Cloudinary status khi component mount
  const fetchDatasetSummary = async () => {
    try {
      const data = await api.getDatasetSummary();
      setDatasetSummary(data);
    } catch (e) {
      console.warn('Lỗi lấy thống kê dataset:', e);
    }
  };

  const fetchCloudStatus = async () => {
    try {
      const status = await api.getCloudinaryStatus();
      setCloudinaryStatus(status);
      if (status.cloud_name) {
        setCloudForm((prev) => ({ ...prev, cloud_name: status.cloud_name }));
      }
    } catch (e) {
      console.warn('Lỗi lấy trạng thái Cloudinary:', e);
    }
  };

  useEffect(() => {
    fetchDatasetSummary();
    fetchCloudStatus();
  }, [session?.id]);

  const handleStart = async () => {
    if (!session) return;
    setLoading(true);
    setStreamError(false);
    try {
      await api.startSession(session.id);
      if (onStatusChange) onStatusChange('running');
    } catch (err) {
      alert(err.message);
    } finally {
      setLoading(false);
    }
  };

  const handleStop = async () => {
    if (!session) return;
    setLoading(true);
    try {
      await api.stopSession(session.id);
      if (onStatusChange) onStatusChange('stopped');
    } catch (err) {
      alert(err.message);
    } finally {
      setLoading(false);
    }
  };

  const handleSaveCloudinary = async (e) => {
    e.preventDefault();
    if (!cloudForm.cloud_name || !cloudForm.api_key || !cloudForm.api_secret) {
      alert('Vui lòng điền đủ Cloud Name, API Key và API Secret');
      return;
    }
    setSavingCloud(true);
    try {
      const res = await api.configureCloudinary(cloudForm);
      alert(res.message);
      setShowCloudModal(false);
      await fetchCloudStatus();
    } catch (err) {
      alert(err.message);
    } finally {
      setSavingCloud(false);
    }
  };

  const handleCaptureSample = async () => {
    if (!session || !isRunning) {
      setDatasetToast({
        type: 'error',
        message: 'Vui lòng bấm Bắt Đầu Giám Sát trước khi chụp khung hình.'
      });
      return;
    }
    setCaptureLoading(true);
    setDatasetToast(null);
    try {
      const res = await api.captureLiveSample(session.id);
      setDatasetToast({
        type: 'success',
        message: res.sample.cloud_url
          ? `Đã chụp, tự động gán nhãn và tải trực tiếp lên Cloudinary!`
          : `Đã chụp và tự động gán nhãn thành công vào Dataset! (Tổng: ${res.summary.total_images} ảnh)`,
        cloudUrl: res.sample.cloud_url
      });
      setDatasetSummary(res.summary);
    } catch (err) {
      setDatasetToast({
        type: 'error',
        message: err.message || 'Lỗi khi chụp khung hình.'
      });
    } finally {
      setCaptureLoading(false);
    }
  };

  const handleBatchExtract = async () => {
    if (!session) return;
    setBatchLoading(true);
    setDatasetToast(null);
    try {
      const res = await api.autoExtractBatch(session.id, 50);
      setDatasetToast({
        type: 'success',
        message: `⚡ Đã trích xuất & tự động gán nhãn thành công 50 mẫu! (Tổng hiện có: ${res.summary.total_images} ảnh)`
      });
      setDatasetSummary(res.summary);
    } catch (err) {
      setDatasetToast({
        type: 'error',
        message: err.message || 'Lỗi khi trích xuất hàng loạt.'
      });
    } finally {
      setBatchLoading(false);
    }
  };



  return (
    <div className="card" style={{ padding: '1.25rem', position: 'relative' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
          <span style={{ fontWeight: 800, fontSize: '1rem', color: '#0f172a' }}>
            CAMERA GIÁM SÁT TRỰC TIẾP
          </span>
          <span
            className="live-badge"
            style={{
              backgroundColor: isRunning ? '#ecfdf5' : '#fef2f2',
              color: isRunning ? '#059669' : '#dc2626',
              borderColor: isRunning ? '#a7f3d0' : '#fecaca'
            }}
          >
            <span
              className="pulsing-dot"
              style={{
                backgroundColor: isRunning ? '#10b981' : '#ef4444',
                boxShadow: isRunning ? '0 0 8px rgba(16, 185, 129, 0.6)' : 'none'
              }}
            ></span>
            <span>{isRunning ? 'LIVE STREAMING' : 'OFFLINE'}</span>
          </span>
        </div>

        <div style={{ display: 'flex', gap: '0.5rem' }}>
          {!isRunning ? (
            <button
              id="start-stream-btn"
              className="btn btn-success"
              onClick={handleStart}
              disabled={loading || !session}
            >
              <Play size={16} />
              <span>Bắt Đầu Giám Sát</span>
            </button>
          ) : (
            <button
              id="stop-stream-btn"
              className="btn btn-danger"
              onClick={handleStop}
              disabled={loading}
            >
              <Square size={16} />
              <span>Dừng Giám Sát</span>
            </button>
          )}

          <button
            id="reload-stream-btn"
            className="btn btn-secondary"
            onClick={() => setStreamError(false)}
            title="Tải lại luồng"
          >
            <RefreshCw size={16} />
          </button>
        </div>
      </div>

      {/* Stream Viewer Container */}
      <div
        style={{
          width: '100%',
          aspectRatio: '16/9',
          background: isRunning && !streamError ? '#000000' : '#f1f5f9',
          borderRadius: '12px',
          overflow: 'hidden',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          position: 'relative',
          border: '1px solid #e2e8f0'
        }}
      >
        {isRunning && !streamError ? (
          <img
            id="live-stream-img"
            src={streamUrl}
            alt="Live Stream Camera"
            style={{ width: '100%', height: '100%', objectFit: 'contain' }}
            onError={() => setStreamError(true)}
          />
        ) : (
          <div style={{ textAlign: 'center', color: '#64748b', padding: '2rem' }}>
            <AlertCircle size={44} style={{ margin: '0 auto 0.75rem', color: '#94a3b8' }} />
            <p style={{ fontWeight: 700, fontSize: '1rem', color: '#1e293b', marginBottom: '0.375rem' }}>
              {streamError ? 'Không thể tải luồng video (Kiểm tra lại kết nối máy chủ)' : 'Camera đang ở trạng thái chờ'}
            </p>
            <p style={{ fontSize: '0.875rem', color: '#64748b', maxWidth: '380px', margin: '0 auto' }}>
              Bấm nút <strong>"Bắt Đầu Giám Sát"</strong> ở phía trên để nạp luồng video và nhận diện phương tiện.
            </p>
          </div>
        )}

        {/* Video Overlay Specs & AI Engine Info */}
        {isRunning && (
          <div
            style={{
              position: 'absolute',
              bottom: '12px',
              left: '12px',
              display: 'flex',
              gap: '8px',
              alignItems: 'center',
              flexWrap: 'wrap'
            }}
          >
            <div
              style={{
                padding: '5px 10px',
                background: 'rgba(15, 23, 42, 0.85)',
                backdropFilter: 'blur(8px)',
                borderRadius: '6px',
                fontSize: '0.75rem',
                color: '#38bdf8',
                fontFamily: 'monospace',
                border: '1px solid rgba(56, 189, 248, 0.35)',
                fontWeight: 700
              }}
            >
              🧠 AI: YOLOv8-Traffic-VN (Fine-tuned)
            </div>
            <div
              style={{
                padding: '5px 10px',
                background: 'rgba(15, 23, 42, 0.85)',
                backdropFilter: 'blur(8px)',
                borderRadius: '6px',
                fontSize: '0.75rem',
                color: '#34d399',
                fontFamily: 'monospace',
                border: '1px solid rgba(255, 255, 255, 0.2)'
              }}
            >
              {session?.camera_url?.startsWith('rtsp')
                ? '📹 RTSP Live IP @ 30fps'
                : session?.camera_url?.endsWith('.avi')
                ? '🎞️ File AVI @ 30fps'
                : '📁 File MP4 @ 30fps'}
            </div>
          </div>
        )}
      </div>

      {/* Thông báo kết quả chụp / gán nhãn */}
      {datasetToast && (
        <div
          style={{
            marginTop: '0.875rem',
            padding: '0.75rem 1rem',
            borderRadius: '8px',
            backgroundColor: datasetToast.type === 'success' ? '#ecfdf5' : '#fef2f2',
            color: datasetToast.type === 'success' ? '#065f46' : '#991b1b',
            border: `1px solid ${datasetToast.type === 'success' ? '#a7f3d0' : '#fecaca'}`,
            fontSize: '0.8125rem',
            fontWeight: 600,
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            boxShadow: '0 1px 2px rgba(0,0,0,0.05)'
          }}
        >
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', flexWrap: 'wrap' }}>
            {datasetToast.type === 'success' ? (
              <CheckCircle2 size={17} style={{ color: '#059669', flexShrink: 0 }} />
            ) : (
              <AlertCircle size={17} style={{ color: '#dc2626', flexShrink: 0 }} />
            )}
            <span>{datasetToast.message}</span>
            {datasetToast.cloudUrl && (
              <a
                href={datasetToast.cloudUrl}
                target="_blank"
                rel="noreferrer"
                style={{
                  color: '#0284c7',
                  textDecoration: 'underline',
                  display: 'inline-flex',
                  alignItems: 'center',
                  gap: '0.25rem',
                  fontWeight: 700,
                  fontSize: '0.8125rem'
                }}
              >
                <ExternalLink size={13} />
                <span>Xem ảnh trực tiếp trên Cloudinary</span>
              </a>
            )}
          </div>
          <button
            onClick={() => setDatasetToast(null)}
            style={{
              background: 'transparent',
              border: 'none',
              cursor: 'pointer',
              color: 'inherit',
              fontWeight: 800,
              fontSize: '0.875rem',
              padding: '0 4px'
            }}
          >
            ✕
          </button>
        </div>
      )}

      {/* Thanh công cụ Thu thập & Tự động gán nhãn Dataset */}
      <div
        style={{
          marginTop: '0.875rem',
          padding: '0.875rem 1rem',
          backgroundColor: '#f8fafc',
          border: '1px solid #e2e8f0',
          borderRadius: '10px',
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          flexWrap: 'wrap',
          gap: '0.75rem'
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.625rem' }}>
          <div
            style={{
              width: '34px',
              height: '34px',
              borderRadius: '8px',
              backgroundColor: '#eff6ff',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              color: '#2563eb'
            }}
          >
            <FolderCheck size={18} />
          </div>
          <div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', flexWrap: 'wrap' }}>
              <span style={{ fontSize: '0.8125rem', fontWeight: 800, color: '#0f172a' }}>
                BỘ DỮ LIỆU ĐÃ GÁN NHÃN
              </span>
              <span
                style={{
                  display: 'inline-flex',
                  alignItems: 'center',
                  gap: '0.25rem',
                  fontSize: '0.6875rem',
                  padding: '1px 7px',
                  borderRadius: '9999px',
                  backgroundColor: cloudinaryStatus?.is_configured ? '#ecfdf5' : '#f1f5f9',
                  color: cloudinaryStatus?.is_configured ? '#059669' : '#64748b',
                  border: `1px solid ${cloudinaryStatus?.is_configured ? '#a7f3d0' : '#cbd5e1'}`,
                  fontWeight: 700
                }}
              >
                <Cloud size={11} />
                {cloudinaryStatus?.is_configured ? `Cloudinary: ${cloudinaryStatus.cloud_name}` : 'Local Disk'}
              </span>
              <button
                onClick={() => setShowCloudModal(true)}
                style={{
                  background: 'none',
                  border: 'none',
                  cursor: 'pointer',
                  color: '#2563eb',
                  fontSize: '0.75rem',
                  fontWeight: 700,
                  display: 'inline-flex',
                  alignItems: 'center',
                  gap: '3px',
                  padding: '1px 4px',
                  textDecoration: 'underline'
                }}
                title="Cấu hình Cloud Name, API Key, API Secret"
              >
                <Settings size={12} />
                {cloudinaryStatus?.is_configured ? 'Đổi Cloudinary' : 'Cấu hình Cloudinary'}
              </button>
            </div>
            <div style={{ fontSize: '0.75rem', color: '#64748b', marginTop: '2px' }}>
              {datasetSummary ? (
                <>
                  <strong style={{ color: '#1e293b' }}>{datasetSummary.total_images}</strong> ảnh |{' '}
                  <strong style={{ color: '#1e293b' }}>{datasetSummary.total_boxes}</strong> nhãn xe{' '}
                  <span style={{ color: '#94a3b8' }}>
                    (Ô tô: {datasetSummary.class_totals?.car || 0}, Xe máy: {datasetSummary.class_totals?.motorcycle || 0}, Buýt: {datasetSummary.class_totals?.bus || 0}, Tải: {datasetSummary.class_totals?.truck || 0})
                  </span>
                </>
              ) : (
                'Đang kiểm tra thư mục data/dataset/...'
              )}
            </div>
          </div>
        </div>

        <div style={{ display: 'flex', gap: '0.5rem', flexWrap: 'wrap' }}>
          <button
            id="capture-frame-btn"
            className="btn btn-primary"
            onClick={handleCaptureSample}
            disabled={!isRunning || captureLoading || batchLoading}
            title="Chụp khung hình thời gian thực, tải lên Cloudinary & sinh file nhãn YOLO (.txt)"
            style={{ fontSize: '0.8125rem', padding: '0.45rem 0.85rem' }}
          >
            <Camera size={15} />
            <span>{captureLoading ? 'Đang gán nhãn...' : 'Chụp & Gán nhãn vào Dataset'}</span>
          </button>

          <button
            id="auto-extract-btn"
            className="btn"
            onClick={handleBatchExtract}
            disabled={!session || captureLoading || batchLoading}
            title="Tự động trích xuất và gán nhãn 50 khung hình từ video giao thông"
            style={{
              fontSize: '0.8125rem',
              padding: '0.45rem 0.85rem',
              backgroundColor: '#fffbeb',
              borderColor: '#fde68a',
              color: '#b45309'
            }}
          >
            <Zap size={15} />
            <span>{batchLoading ? 'Đang trích xuất 50 mẫu...' : '⚡ Tự động trích xuất 50 mẫu'}</span>
          </button>
        </div>
      </div>

      {/* Modal Cấu hình Cloudinary */}
      {showCloudModal && (
        <div
          className="modal-overlay"
          onClick={(e) => {
            if (e.target === e.currentTarget) setShowCloudModal(false);
          }}
        >
          <div className="modal-content" style={{ maxWidth: '520px', padding: '1.75rem' }}>
            {/* Header */}
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '1.25rem' }}>
              <div style={{ display: 'flex', gap: '0.875rem', alignItems: 'center' }}>
                <div
                  style={{
                    width: '44px',
                    height: '44px',
                    borderRadius: '12px',
                    background: 'linear-gradient(135deg, #eff6ff, #dbeafe)',
                    border: '1px solid #bfdbfe',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    color: '#2563eb',
                    flexShrink: 0
                  }}
                >
                  <Cloud size={24} />
                </div>
                <div>
                  <h3 style={{ fontSize: '1.0625rem', fontWeight: 800, color: '#0f172a', letterSpacing: '-0.01em' }}>
                    Cấu Hình Tải Ảnh Cloudinary
                  </h3>
                  <p style={{ fontSize: '0.8125rem', color: '#64748b', marginTop: '2px' }}>
                    Tự động đẩy ảnh lên Cloud CDN & lưu link HTTPS về CSDL
                  </p>
                </div>
              </div>

              <button
                type="button"
                onClick={() => setShowCloudModal(false)}
                style={{
                  width: '32px',
                  height: '32px',
                  borderRadius: '8px',
                  border: '1px solid #e2e8f0',
                  background: '#f8fafc',
                  cursor: 'pointer',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  color: '#64748b',
                  fontSize: '1rem',
                  fontWeight: 700,
                  transition: 'all 0.15s ease'
                }}
                onMouseEnter={(e) => { e.currentTarget.style.background = '#fee2e2'; e.currentTarget.style.color = '#ef4444'; }}
                onMouseLeave={(e) => { e.currentTarget.style.background = '#f8fafc'; e.currentTarget.style.color = '#64748b'; }}
                title="Đóng"
              >
                ✕
              </button>
            </div>

            {/* Hộp giải thích thông tin */}
            <div
              style={{
                display: 'flex',
                alignItems: 'flex-start',
                gap: '0.625rem',
                padding: '0.875rem 1rem',
                borderRadius: '10px',
                background: '#f0f9ff',
                border: '1px solid #bae6fd',
                marginBottom: '1.25rem',
                fontSize: '0.8125rem',
                color: '#0369a1',
                lineHeight: '1.45'
              }}
            >
              <Info size={17} style={{ flexShrink: 0, marginTop: '2px', color: '#0284c7' }} />
              <div>
                Ảnh chụp từ luồng camera sẽ được nén tối ưu (chỉ ~70KB) và tải trực tiếp lên Cloudinary. CSDL chỉ lưu đường link URL để mã nguồn luôn nhẹ và không bị đầy bộ nhớ.
              </div>
            </div>

            {/* Form cấu hình */}
            <form onSubmit={handleSaveCloudinary} style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
              <div>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.375rem' }}>
                  <label style={{ fontSize: '0.8125rem', fontWeight: 700, color: '#334155' }}>
                    Cloud Name
                  </label>
                  <span style={{ fontSize: '0.6875rem', color: '#dc2626', fontWeight: 700, background: '#fef2f2', padding: '1px 6px', borderRadius: '4px' }}>
                    Bắt buộc
                  </span>
                </div>
                <input
                  type="text"
                  className="input-field"
                  placeholder="Ví dụ: djesc4hru"
                  value={cloudForm.cloud_name}
                  onChange={(e) => setCloudForm({ ...cloudForm, cloud_name: e.target.value })}
                  required
                />
              </div>

              <div>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.375rem' }}>
                  <label style={{ fontSize: '0.8125rem', fontWeight: 700, color: '#334155' }}>
                    API Key
                  </label>
                  <span style={{ fontSize: '0.6875rem', color: '#dc2626', fontWeight: 700, background: '#fef2f2', padding: '1px 6px', borderRadius: '4px' }}>
                    Bắt buộc
                  </span>
                </div>
                <input
                  type="text"
                  className="input-field"
                  placeholder="Dán API Key (Ví dụ: 123456789012345)"
                  value={cloudForm.api_key}
                  onChange={(e) => setCloudForm({ ...cloudForm, api_key: e.target.value })}
                  required
                />
              </div>

              <div>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.375rem' }}>
                  <label style={{ fontSize: '0.8125rem', fontWeight: 700, color: '#334155' }}>
                    API Secret
                  </label>
                  <span style={{ fontSize: '0.6875rem', color: '#dc2626', fontWeight: 700, background: '#fef2f2', padding: '1px 6px', borderRadius: '4px' }}>
                    Bắt buộc
                  </span>
                </div>
                <div style={{ position: 'relative' }}>
                  <input
                    type={showSecret ? 'text' : 'password'}
                    className="input-field"
                    placeholder="Dán API Secret của bạn"
                    value={cloudForm.api_secret}
                    onChange={(e) => setCloudForm({ ...cloudForm, api_secret: e.target.value })}
                    required
                    style={{ paddingRight: '2.5rem' }}
                  />
                  <button
                    type="button"
                    onClick={() => setShowSecret(!showSecret)}
                    style={{
                      position: 'absolute',
                      right: '10px',
                      top: '50%',
                      transform: 'translateY(-50%)',
                      background: 'none',
                      border: 'none',
                      cursor: 'pointer',
                      color: '#94a3b8',
                      display: 'flex',
                      alignItems: 'center',
                      padding: '4px'
                    }}
                    title={showSecret ? 'Ẩn mật khẩu' : 'Hiện mật khẩu'}
                  >
                    {showSecret ? <EyeOff size={16} /> : <Eye size={16} />}
                  </button>
                </div>
              </div>

              {/* Action Buttons */}
              <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '0.625rem', marginTop: '0.5rem', paddingTop: '1rem', borderTop: '1px solid #f1f5f9' }}>
                <button
                  type="button"
                  className="btn btn-secondary"
                  onClick={() => setShowCloudModal(false)}
                  style={{ minWidth: '90px' }}
                >
                  Hủy Bỏ
                </button>
                <button
                  type="submit"
                  className="btn btn-primary"
                  disabled={savingCloud}
                  style={{ minWidth: '160px', gap: '0.5rem' }}
                >
                  <Cloud size={16} />
                  <span>{savingCloud ? 'Đang lưu cấu hình...' : 'Lưu & Kích Hoạt Cloud'}</span>
                </button>
              </div>
            </form>
          </div>
        </div>
      )}


    </div>
  );
}

