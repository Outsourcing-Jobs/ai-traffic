import React, { useState, useEffect } from 'react';
import KPICards from '../components/KPICards';
import VideoStream from '../components/VideoStream';
import { api } from '../services/api';
import { AlertTriangle, Gauge, ShieldAlert, CheckCircle, Info, Flame, Settings } from 'lucide-react';

export default function LiveMonitorPage({ session, onStatusChange }) {
  const [summary, setSummary] = useState(null);
  const [liveCounts, setLiveCounts] = useState(null);
  const [crossings, setCrossings] = useState([]);
  const [speedLimit, setSpeedLimit] = useState(50);
  const [isUpdatingSpeed, setIsUpdatingSpeed] = useState(false);

  // Polling dữ liệu thời gian thực mỗi 1.5 giây
  useEffect(() => {
    if (!session) return;

    let isMounted = true;
    const fetchData = async () => {
      try {
        const [sumData, countData, crossData] = await Promise.all([
          api.getSummary(session.id),
          api.getLiveCounts(session.id),
          api.getCrossings(session.id, 25)
        ]);
        if (isMounted) {
          setSummary(sumData);
          setLiveCounts(countData);
          setCrossings(crossData);
          if (sumData?.speed_limit != null && !isUpdatingSpeed) {
            setSpeedLimit(sumData.speed_limit);
          }
        }
      } catch (e) {
        // Tránh log spam khi server chưa start
      }
    };

    fetchData();
    const interval = setInterval(fetchData, 1500);
    return () => {
      isMounted = false;
      clearInterval(interval);
    };
  }, [session?.id, isUpdatingSpeed]);

  const handleSpeedLimitChange = async (newLimit) => {
    if (!session) return;
    const val = parseFloat(newLimit);
    if (isNaN(val) || val <= 0) return;
    setIsUpdatingSpeed(true);
    setSpeedLimit(val);
    try {
      await api.updateSpeedLimit(session.id, val);
      // Giữ cờ cập nhật thêm 1 chu kỳ để tránh polling cũ đè lên
      setTimeout(() => {
        setIsUpdatingSpeed(false);
      }, 1800);
    } catch (e) {
      console.error('Lỗi cập nhật giới hạn tốc độ:', e);
      setIsUpdatingSpeed(false);
    }
  };

  const getVehicleBadge = (type) => {
    switch (type) {
      case 'car':
        return <span className="badge-vehicle badge-car">Ô tô</span>;
      case 'truck':
        return <span className="badge-vehicle badge-truck">Xe tải</span>;
      case 'bus':
        return <span className="badge-vehicle badge-bus">Xe buýt</span>;
      case 'motorcycle':
        return <span className="badge-vehicle badge-motorcycle">Xe máy</span>;
      default:
        return <span className="badge-vehicle">{type}</span>;
    }
  };

  // Congestion Level Banner Styling
  const isRunning = session?.status === 'running';
  const congestionLevel = summary?.congestion_level || 'FLUID';
  const activeVehicles = summary?.active_vehicles || 0;

  const getCongestionBanner = () => {
    // 1. Khi phiên đang tạm dừng
    if (!isRunning) {
      return (
        <div style={{
          backgroundColor: '#f8fafc',
          border: '1px solid #e2e8f0',
          borderRadius: '12px',
          padding: '0.75rem 1.25rem',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          marginBottom: '1.25rem',
          color: '#475569'
        }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
            <Info size={20} color="#64748b" />
            <div>
              <strong>TRẠNG THÁI HỆ THỐNG:</strong> Phiên giám sát đang tạm dừng. Nhấn nút <strong>"Khởi Chạy"</strong> trên khung video để kích hoạt nhận diện AI thời gian thực.
            </div>
          </div>
          <span style={{
            backgroundColor: '#f1f5f9',
            color: '#64748b',
            border: '1px solid #cbd5e1',
            padding: '0.25rem 0.65rem',
            borderRadius: '9999px',
            fontSize: '0.75rem',
            fontWeight: 800
          }}>
            TẠM DỪNG ⏸️
          </span>
        </div>
      );
    }

    // 2. Khi đang chạy và có cảnh báo ùn tắc
    if (congestionLevel === 'CONGESTED') {
      return (
        <div style={{
          backgroundColor: '#fee2e2',
          border: '1px solid #f87171',
          borderRadius: '12px',
          padding: '0.75rem 1.25rem',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          marginBottom: '1.25rem',
          color: '#991b1b',
          animation: 'pulse 2s infinite'
        }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
            <Flame size={22} color="#dc2626" />
            <div>
              <strong>CẢNH BÁO ÙN TẮC GIAO THÔNG CỤC BỘ:</strong> Mật độ xe cao ({activeVehicles} xe trong khung hình) và vận tốc lưu thông giảm mạnh.
            </div>
          </div>
          <span style={{
            backgroundColor: '#dc2626',
            color: '#ffffff',
            padding: '0.25rem 0.65rem',
            borderRadius: '9999px',
            fontSize: '0.75rem',
            fontWeight: 800
          }}>
            ÙN TẮC 🔴
          </span>
        </div>
      );
    }
    if (congestionLevel === 'MODERATE') {
      return (
        <div style={{
          backgroundColor: '#fef3c7',
          border: '1px solid #fcd34d',
          borderRadius: '12px',
          padding: '0.75rem 1.25rem',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          marginBottom: '1.25rem',
          color: '#92400e'
        }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
            <AlertTriangle size={20} color="#d97706" />
            <div>
              <strong>MẬT ĐỘ PHƯƠNG TIỆN ĐÔNG:</strong> Lưu lượng xe tăng ({activeVehicles} xe), các phương tiện đang giảm tốc độ.
            </div>
          </div>
          <span style={{
            backgroundColor: '#d97706',
            color: '#ffffff',
            padding: '0.25rem 0.65rem',
            borderRadius: '9999px',
            fontSize: '0.75rem',
            fontWeight: 800
          }}>
            ĐÔNG ĐÚC 🟡
          </span>
        </div>
      );
    }
    return (
      <div style={{
        backgroundColor: '#ecfdf5',
        border: '1px solid #a7f3d0',
        borderRadius: '12px',
        padding: '0.75rem 1.25rem',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        marginBottom: '1.25rem',
        color: '#065f46'
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
          <CheckCircle size={20} color="#059669" />
          <div>
            <strong>GIAO THÔNG THÔNG THOÁNG:</strong> Tình trạng lưu thông ổn định, các phương tiện di chuyển với vận tốc cho phép ({activeVehicles} xe trong khung).
          </div>
        </div>
        <span style={{
          backgroundColor: '#059669',
          color: '#ffffff',
          padding: '0.25rem 0.65rem',
          borderRadius: '9999px',
          fontSize: '0.75rem',
          fontWeight: 800
        }}>
          THÔNG THOÁNG 🟢
        </span>
      </div>
    );
  };

  return (
    <div>
      {/* 4 Thẻ KPI trên cùng */}
      <KPICards summary={summary} liveCounts={liveCounts} />

      {/* Banner Đánh Giá Mật Độ / Ùn Tắc Giao Thông */}
      {getCongestionBanner()}

      {/* Grid 2 cột: Cột trái phát Video, Cột phải Bảng sự kiện Real-time & Cài đặt Tốc Độ */}
      <div style={{ display: 'grid', gridTemplateColumns: 'minmax(0, 1.7fr) minmax(0, 1.1fr)', gap: '1.5rem' }}>
        <div>
          <VideoStream session={session} onStatusChange={onStatusChange} />
        </div>

        {/* Cột Phải: Bảng Sự Kiện & Cài Đặt Giới Hạn Tốc Độ */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '1.25rem' }}>
          {/* Cài Đặt Giới Hạn Tốc Độ (Speed Limit Controller) */}
          <div className="card" style={{ padding: '1rem 1.25rem' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.75rem' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', color: '#1e293b' }}>
                <Gauge size={18} color="#2563eb" />
                <h4 style={{ margin: 0, fontSize: '0.875rem', fontWeight: 800 }}>GIỚI HẠN TỐC ĐỘ ĐOẠN ĐƯỜNG (PHẠT NGUỘI)</h4>
              </div>
              <span style={{
                fontSize: '0.8125rem',
                fontWeight: 800,
                color: '#dc2626',
                backgroundColor: '#fee2e2',
                padding: '0.15rem 0.5rem',
                borderRadius: '6px'
              }}>
                {speedLimit} km/h
              </span>
            </div>

            <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', flexWrap: 'wrap' }}>
              <span style={{ fontSize: '0.8125rem', color: '#64748b' }}>Mức quy định:</span>
              {[30, 40, 50, 60, 80].map((preset) => (
                <button
                  key={preset}
                  onClick={() => handleSpeedLimitChange(preset)}
                  className={`btn ${speedLimit === preset ? 'btn-primary' : 'btn-secondary'}`}
                  style={{
                    padding: '0.25rem 0.65rem',
                    fontSize: '0.8125rem',
                    borderRadius: '8px'
                  }}
                >
                  {preset} km/h
                </button>
              ))}
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.35rem', marginLeft: 'auto' }}>
                <input
                  type="number"
                  min="10"
                  max="150"
                  value={speedLimit}
                  onChange={(e) => handleSpeedLimitChange(e.target.value)}
                  style={{
                    width: '65px',
                    padding: '0.25rem 0.5rem',
                    fontSize: '0.8125rem',
                    border: '1px solid #cbd5e1',
                    borderRadius: '6px',
                    textAlign: 'center',
                    fontWeight: 700
                  }}
                />
                <span style={{ fontSize: '0.75rem', color: '#64748b' }}>km/h</span>
              </div>
            </div>
          </div>

          {/* Bảng Sự Kiện Xe Vừa Cắt Qua Vạch */}
          <div className="card" style={{ display: 'flex', flexDirection: 'column', flex: 1 }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem' }}>
              <h3 style={{ fontSize: '0.9375rem', fontWeight: 800, margin: 0 }}>SỰ KIỆN QUA VẠCH GẦN NHẤT</h3>
              <span style={{ fontSize: '0.75rem', color: '#94a3b8' }}>{crossings.length} lượt ghi nhận</span>
            </div>

            <div style={{ flex: 1, overflowY: 'auto', maxHeight: '410px' }}>
              <table className="custom-table">
                <thead>
                  <tr>
                    <th>Track ID</th>
                    <th>Loại Xe</th>
                    <th>Tốc Độ</th>
                    <th>Hướng</th>
                    <th>Thời Gian</th>
                  </tr>
                </thead>
                <tbody>
                  {crossings.length > 0 ? (
                    crossings.map((c) => {
                      const isViolation = c.speed_kmh && c.speed_kmh > speedLimit;
                      return (
                        <tr key={c.id} style={{ backgroundColor: isViolation ? 'rgba(254, 226, 226, 0.4)' : undefined }}>
                          <td className="font-mono" style={{ color: '#2563eb', fontWeight: 700 }}>
                            #{c.track_id}
                          </td>
                          <td>{getVehicleBadge(c.vehicle_type)}</td>
                          <td className="font-mono" style={{ fontWeight: 700 }}>
                            {c.speed_kmh ? (
                              <span style={{ color: isViolation ? '#dc2626' : '#0f172a' }}>
                                {c.speed_kmh.toFixed(1)} km/h
                                {isViolation && <span style={{ color: '#dc2626', marginLeft: '4px' }}>⚠️</span>}
                              </span>
                            ) : (
                              '--'
                            )}
                          </td>
                          <td>
                            <span style={{ color: c.direction === 'in' ? '#059669' : '#e11d48', fontWeight: 700 }}>
                              {c.direction?.toUpperCase()}
                            </span>
                          </td>
                          <td style={{ fontSize: '0.8125rem', color: '#475569', fontWeight: 600 }}>
                            {new Date(c.crossed_at).toLocaleTimeString('vi-VN', { hour12: false })}
                          </td>
                        </tr>
                      );
                    })
                  ) : (
                    <tr>
                      <td colSpan="5" style={{ textAlign: 'center', color: '#64748b', padding: '2rem' }}>
                        Chưa có xe nào đi qua vạch đếm. Khi video chạy và xe chạm vạch, dữ liệu sẽ tự động nhảy ở đây.
                      </td>
                    </tr>
                  )}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

