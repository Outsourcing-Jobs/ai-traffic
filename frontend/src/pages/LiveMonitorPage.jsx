import React, { useState, useEffect } from 'react';
import KPICards from '../components/KPICards';
import VideoStream from '../components/VideoStream';
import { api } from '../services/api';

export default function LiveMonitorPage({ session, onStatusChange }) {
  const [summary, setSummary] = useState(null);
  const [liveCounts, setLiveCounts] = useState(null);
  const [crossings, setCrossings] = useState([]);

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
  }, [session?.id]);

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

  return (
    <div>
      {/* 4 Thẻ KPI trên cùng */}
      <KPICards summary={summary} liveCounts={liveCounts} />

      {/* Grid 2 cột: Cột trái phát Video, Cột phải Bảng sự kiện Real-time */}
      <div style={{ display: 'grid', gridTemplateColumns: 'minmax(0, 1.7fr) minmax(0, 1.1fr)', gap: '1.5rem', marginTop: '1.25rem' }}>
        <div>
          <VideoStream session={session} onStatusChange={onStatusChange} />
        </div>

        {/* Cột Phải: Bảng Sự Kiện Qua Vạch */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '1.25rem' }}>

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
                    crossings.map((c) => (
                      <tr key={c.id}>
                        <td className="font-mono" style={{ color: '#2563eb', fontWeight: 700 }}>
                          #{c.track_id}
                        </td>
                        <td>{getVehicleBadge(c.vehicle_type)}</td>
                        <td className="font-mono" style={{ fontWeight: 700 }}>
                          {c.speed_kmh ? `${c.speed_kmh.toFixed(1)} km/h` : '--'}
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
                    ))
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

