import React, { useState, useEffect } from 'react';
import { api } from '../services/api';
import { 
  AlertTriangle, 
  Gauge, 
  Activity, 
  Car, 
  Camera, 
  Download, 
  RefreshCw, 
  Trash2, 
  ExternalLink, 
  Eye, 
  X,
  FileSpreadsheet,
  CheckCircle2,
  Clock
} from 'lucide-react';

export default function ViolationsPage({ session }) {
  const [violations, setViolations] = useState([]);
  const [summary, setSummary] = useState(null);
  const [loading, setLoading] = useState(false);
  const [selectedViolation, setSelectedViolation] = useState(null);
  const [deletingId, setDeletingId] = useState(null);

  const loadData = async () => {
    setLoading(true);
    try {
      const sessionId = session ? session.id : null;
      const [violationsData, summaryData] = await Promise.all([
        api.getViolations(sessionId, 100, 0),
        api.getViolationsSummary(sessionId)
      ]);
      setViolations(violationsData);
      setSummary(summaryData);
    } catch (e) {
      console.error('Lỗi khi tải dữ liệu vi phạm:', e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
    const interval = setInterval(loadData, 4000);
    return () => clearInterval(interval);
  }, [session?.id]);

  const handleDelete = async (id) => {
    if (!window.confirm('Bạn có chắc chắn muốn xóa bản ghi vi phạm này?')) return;
    setDeletingId(id);
    try {
      await api.deleteViolation(id);
      await loadData();
    } catch (e) {
      alert(e.message || 'Lỗi khi xóa bản ghi');
    } finally {
      setDeletingId(null);
    }
  };

  const getVehicleName = (type) => {
    const map = {
      car: 'Ô tô con',
      motorcycle: 'Xe máy',
      bus: 'Xe buýt / Khách',
      truck: 'Xe tải'
    };
    return map[type] || type || 'Phương tiện';
  };

  const getTopViolatorType = () => {
    if (!summary || !summary.by_type) return 'Không có';
    let maxType = null;
    let maxCount = -1;
    for (const [vtype, count] of Object.entries(summary.by_type)) {
      if (count > maxCount && count > 0) {
        maxCount = count;
        maxType = vtype;
      }
    }
    return maxType ? `${getVehicleName(maxType)} (${maxCount} lượt)` : 'Chưa ghi nhận';
  };

  return (
    <div>
      {/* Header & Actions */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1.5rem', flexWrap: 'wrap', gap: '1rem' }}>
        <div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.625rem' }}>
            <div style={{
              width: '36px',
              height: '36px',
              borderRadius: '10px',
              backgroundColor: '#fee2e2',
              color: '#dc2626',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center'
            }}>
              <AlertTriangle size={22} />
            </div>
            <h2 style={{ fontSize: '1.375rem', fontWeight: 800, color: '#0f172a', margin: 0 }}>
              GIÁM SÁT VI PHẠM TỐC ĐỘ & BIÊN BẢN PHẠT NGUỘI
            </h2>
          </div>
          <p style={{ fontSize: '0.875rem', color: '#64748b', marginTop: '0.25rem', marginBottom: 0 }}>
            Tự động phát hiện phương tiện vượt tốc độ quy định, chụp ảnh bằng chứng có Watermark và lưu trữ CSDL.
          </p>
        </div>

        <div style={{ display: 'flex', gap: '0.75rem', alignItems: 'center' }}>
          {session && (
            <a
              href={api.getExportViolationsCsvUrl(session.id)}
              download
              className="btn btn-secondary"
              style={{ textDecoration: 'none', display: 'flex', alignItems: 'center', gap: '0.5rem', color: '#059669', borderColor: '#a7f3d0' }}
            >
              <FileSpreadsheet size={16} />
              <span>Xuất CSV Biên Bản</span>
            </a>
          )}

          <button className="btn btn-secondary" onClick={loadData} disabled={loading}>
            <RefreshCw size={16} className={loading ? 'animate-spin' : ''} />
            <span>Làm Mới</span>
          </button>
        </div>
      </div>

      {/* KPI Cards Grid */}
      <div style={{
        display: 'grid',
        gridTemplateColumns: 'repeat(auto-fit, minmax(230px, 1fr))',
        gap: '1.25rem',
        marginBottom: '1.5rem'
      }}>
        {/* Card 1: Tổng vi phạm */}
        <div className="card" style={{ borderLeft: '4px solid #ef4444' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
            <div>
              <div style={{ fontSize: '0.8125rem', fontWeight: 700, color: '#64748b', textTransform: 'uppercase' }}>
                Tổng Số Vi Phạm
              </div>
              <div style={{ fontSize: '1.875rem', fontWeight: 900, color: '#dc2626', marginTop: '0.25rem' }}>
                {summary?.total_violations || 0}
              </div>
              <div style={{ fontSize: '0.75rem', color: '#94a3b8', marginTop: '0.25rem' }}>
                Đã lập biên bản & chụp ảnh
              </div>
            </div>
            <div style={{ padding: '0.625rem', borderRadius: '10px', backgroundColor: '#fee2e2', color: '#dc2626' }}>
              <AlertTriangle size={22} />
            </div>
          </div>
        </div>

        {/* Card 2: Vận tốc cao nhất */}
        <div className="card" style={{ borderLeft: '4px solid #f59e0b' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
            <div>
              <div style={{ fontSize: '0.8125rem', fontWeight: 700, color: '#64748b', textTransform: 'uppercase' }}>
                Tốc Độ Vi Phạm Max
              </div>
              <div style={{ fontSize: '1.875rem', fontWeight: 900, color: '#d97706', marginTop: '0.25rem' }}>
                {summary?.highest_speed ? `${summary.highest_speed.toFixed(1)}` : '0.0'} <span style={{ fontSize: '1rem', fontWeight: 600 }}>km/h</span>
              </div>
              <div style={{ fontSize: '0.75rem', color: '#94a3b8', marginTop: '0.25rem' }}>
                Vận tốc vi phạm đỉnh điểm
              </div>
            </div>
            <div style={{ padding: '0.625rem', borderRadius: '10px', backgroundColor: '#fef3c7', color: '#d97706' }}>
              <Gauge size={22} />
            </div>
          </div>
        </div>

        {/* Card 3: Tỷ lệ vi phạm */}
        <div className="card" style={{ borderLeft: '4px solid #3b82f6' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
            <div>
              <div style={{ fontSize: '0.8125rem', fontWeight: 700, color: '#64748b', textTransform: 'uppercase' }}>
                Tỷ Lệ Vi Phạm
              </div>
              <div style={{ fontSize: '1.875rem', fontWeight: 900, color: '#2563eb', marginTop: '0.25rem' }}>
                {summary?.violation_rate_pct ? `${summary.violation_rate_pct.toFixed(1)}%` : '0.0%'}
              </div>
              <div style={{ fontSize: '0.75rem', color: '#94a3b8', marginTop: '0.25rem' }}>
                Trên tổng lưu lượng qua trạm
              </div>
            </div>
            <div style={{ padding: '0.625rem', borderRadius: '10px', backgroundColor: '#dbeafe', color: '#2563eb' }}>
              <Activity size={22} />
            </div>
          </div>
        </div>

        {/* Card 4: Loại xe vi phạm nhiều nhất */}
        <div className="card" style={{ borderLeft: '4px solid #8b5cf6' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
            <div>
              <div style={{ fontSize: '0.8125rem', fontWeight: 700, color: '#64748b', textTransform: 'uppercase' }}>
                Nhóm Xe Vi Phạm Nhiều
              </div>
              <div style={{ fontSize: '1.125rem', fontWeight: 800, color: '#7c3aed', marginTop: '0.5rem' }}>
                {getTopViolatorType()}
              </div>
              <div style={{ fontSize: '0.75rem', color: '#94a3b8', marginTop: '0.25rem' }}>
                Phân loại theo YOLO Detection
              </div>
            </div>
            <div style={{ padding: '0.625rem', borderRadius: '10px', backgroundColor: '#ede9fe', color: '#7c3aed' }}>
              <Car size={22} />
            </div>
          </div>
        </div>
      </div>

      {/* Danh Sách Vi Phạm Table */}
      <div className="card">
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem' }}>
          <h3 style={{ fontSize: '1rem', fontWeight: 800, color: '#0f172a', margin: 0 }}>
            DANH SÁCH BIÊN BẢN VI PHẠM TỐC ĐỘ ({violations.length})
          </h3>
          <span style={{ fontSize: '0.8125rem', color: '#64748b' }}>
            {session ? `Đang xem phiên #${session.id} - ${session.name}` : 'Tất cả các phiên'}
          </span>
        </div>

        <div style={{ overflowX: 'auto' }}>
          <table className="custom-table">
            <thead>
              <tr>
                <th style={{ width: '50px' }}>STT</th>
                <th>Track ID</th>
                <th>Loại Xe</th>
                <th>Tốc Độ Đo</th>
                <th>Giới Hạn</th>
                <th>Vượt Quá</th>
                <th>Thời Điểm</th>
                <th>Ảnh Bằng Chứng</th>
                <th>Trạng Thái</th>
                <th style={{ textAlign: 'center' }}>Thao Tác</th>
              </tr>
            </thead>
            <tbody>
              {violations.length > 0 ? (
                violations.map((v, index) => {
                  const over = Math.max(0, v.speed_kmh - v.speed_limit);
                  const imageUrl = v.cloud_url || `/api/violations/image/${v.evidence_image_path}`;
                  return (
                    <tr key={v.id}>
                      <td style={{ color: '#94a3b8', fontWeight: 600 }}>{index + 1}</td>
                      <td>
                        <span style={{
                          padding: '0.2rem 0.5rem',
                          borderRadius: '6px',
                          backgroundColor: '#f1f5f9',
                          fontWeight: 700,
                          fontSize: '0.8125rem',
                          color: '#334155'
                        }}>
                          #{v.track_id}
                        </span>
                      </td>
                      <td style={{ fontWeight: 600 }}>{getVehicleName(v.vehicle_type)}</td>
                      <td>
                        <span style={{ fontSize: '0.9375rem', fontWeight: 800, color: '#dc2626' }}>
                          {v.speed_kmh.toFixed(1)} km/h
                        </span>
                      </td>
                      <td style={{ color: '#64748b' }}>{v.speed_limit.toFixed(1)} km/h</td>
                      <td>
                        <span style={{
                          padding: '0.2rem 0.5rem',
                          borderRadius: '6px',
                          backgroundColor: '#fee2e2',
                          color: '#b91c1c',
                          fontWeight: 800,
                          fontSize: '0.8125rem'
                        }}>
                          +{over.toFixed(1)} km/h
                        </span>
                      </td>
                      <td style={{ fontSize: '0.8125rem', color: '#64748b' }}>
                        {new Date(v.violated_at).toLocaleString('vi-VN')}
                      </td>
                      <td>
                        <button
                          className="btn btn-secondary"
                          style={{ padding: '0.35rem 0.75rem', fontSize: '0.75rem', gap: '0.35rem' }}
                          onClick={() => setSelectedViolation(v)}
                        >
                          <Camera size={14} color="#2563eb" />
                          <span>Xem Ảnh</span>
                        </button>
                      </td>
                      <td>
                        <span style={{
                          display: 'inline-flex',
                          alignItems: 'center',
                          gap: '0.3rem',
                          fontSize: '0.75rem',
                          fontWeight: 700,
                          padding: '0.2rem 0.55rem',
                          borderRadius: '9999px',
                          backgroundColor: '#fef3c7',
                          color: '#b45309'
                        }}>
                          <Clock size={12} />
                          Chờ xử phạt
                        </span>
                      </td>
                      <td style={{ textAlign: 'center' }}>
                        <button
                          onClick={() => handleDelete(v.id)}
                          disabled={deletingId === v.id}
                          style={{
                            border: 'none',
                            background: 'transparent',
                            color: '#ef4444',
                            cursor: 'pointer',
                            padding: '0.3rem',
                            borderRadius: '6px'
                          }}
                          title="Xóa biên bản"
                        >
                          <Trash2 size={16} />
                        </button>
                      </td>
                    </tr>
                  );
                })
              ) : (
                <tr>
                  <td colSpan="10" style={{ textAlign: 'center', color: '#94a3b8', padding: '2.5rem' }}>
                    <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '0.5rem' }}>
                      <CheckCircle2 size={36} color="#10b981" />
                      <div style={{ fontWeight: 600, color: '#334155' }}>Không có vi phạm tốc độ nào được ghi nhận</div>
                      <div style={{ fontSize: '0.8125rem', color: '#94a3b8' }}>
                        Các phương tiện trong vùng quan sát đều lưu thông dưới giới hạn tốc độ quy định.
                      </div>
                    </div>
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>

      {/* Modal Xem Bằng Chứng Hình Ảnh */}
      {selectedViolation && (
        <div style={{
          position: 'fixed',
          top: 0,
          left: 0,
          right: 0,
          bottom: 0,
          backgroundColor: 'rgba(15, 23, 42, 0.75)',
          backdropFilter: 'blur(4px)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          zIndex: 999,
          padding: '1.5rem'
        }}>
          <div style={{
            backgroundColor: '#ffffff',
            borderRadius: '16px',
            width: '100%',
            maxWidth: '900px',
            maxHeight: '90vh',
            display: 'flex',
            flexDirection: 'column',
            overflow: 'hidden',
            boxShadow: '0 25px 50px -12px rgba(0, 0, 0, 0.25)'
          }}>
            {/* Modal Header */}
            <div style={{
              padding: '1.25rem 1.5rem',
              borderBottom: '1px solid #e2e8f0',
              display: 'flex',
              justifyContent: 'space-between',
              alignItems: 'center'
            }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.625rem' }}>
                <div style={{
                  padding: '0.5rem',
                  borderRadius: '8px',
                  backgroundColor: '#fee2e2',
                  color: '#dc2626'
                }}>
                  <Camera size={20} />
                </div>
                <div>
                  <h3 style={{ margin: 0, fontSize: '1.125rem', fontWeight: 800, color: '#0f172a' }}>
                    BẰNG CHỨNG HÌNH ẢNH VI PHẠM TỐC ĐỘ (PHẠT NGUỘI)
                  </h3>
                  <div style={{ fontSize: '0.8125rem', color: '#64748b', marginTop: '0.15rem' }}>
                    Biên bản #{selectedViolation.id} • Phương tiện Track #{selectedViolation.track_id}
                  </div>
                </div>
              </div>
              <button
                onClick={() => setSelectedViolation(null)}
                style={{
                  border: 'none',
                  background: 'none',
                  cursor: 'pointer',
                  color: '#64748b',
                  padding: '0.5rem',
                  borderRadius: '8px'
                }}
              >
                <X size={20} />
              </button>
            </div>

            {/* Modal Body */}
            <div style={{ padding: '1.5rem', overflowY: 'auto', display: 'flex', flexDirection: 'column', gap: '1.25rem' }}>
              {/* Snapshot Image Container */}
              <div style={{
                position: 'relative',
                borderRadius: '12px',
                overflow: 'hidden',
                border: '2px solid #e2e8f0',
                backgroundColor: '#0f172a',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                minHeight: '380px'
              }}>
                <img
                  src={selectedViolation.cloud_url || `/api/violations/image/${selectedViolation.evidence_image_path}`}
                  alt="Ảnh bằng chứng vi phạm"
                  style={{ width: '100%', height: 'auto', display: 'block', objectFit: 'contain' }}
                  onError={(e) => {
                    e.target.onerror = null;
                    e.target.src = 'https://via.placeholder.com/800x450?text=Ảnh+Bằng+Chứng+Đang+Tải';
                  }}
                />
              </div>

              {/* Thông tin chi tiết */}
              <div style={{
                display: 'grid',
                gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))',
                gap: '1rem',
                backgroundColor: '#f8fafc',
                padding: '1rem',
                borderRadius: '12px',
                border: '1px solid #e2e8f0'
              }}>
                <div>
                  <span style={{ fontSize: '0.75rem', color: '#64748b', textTransform: 'uppercase', fontWeight: 700 }}>Loại Xe</span>
                  <div style={{ fontWeight: 800, color: '#0f172a', fontSize: '0.9375rem' }}>
                    {getVehicleName(selectedViolation.vehicle_type)}
                  </div>
                </div>

                <div>
                  <span style={{ fontSize: '0.75rem', color: '#64748b', textTransform: 'uppercase', fontWeight: 700 }}>Tốc Độ Đo Được</span>
                  <div style={{ fontWeight: 900, color: '#dc2626', fontSize: '1.125rem' }}>
                    {selectedViolation.speed_kmh.toFixed(1)} km/h
                  </div>
                </div>

                <div>
                  <span style={{ fontSize: '0.75rem', color: '#64748b', textTransform: 'uppercase', fontWeight: 700 }}>Giới Hạn Tốc Độ</span>
                  <div style={{ fontWeight: 700, color: '#334155', fontSize: '0.9375rem' }}>
                    {selectedViolation.speed_limit.toFixed(1)} km/h
                  </div>
                </div>

                <div>
                  <span style={{ fontSize: '0.75rem', color: '#64748b', textTransform: 'uppercase', fontWeight: 700 }}>Mức Vượt Quá</span>
                  <div style={{ fontWeight: 800, color: '#b91c1c', fontSize: '0.9375rem' }}>
                    +{(selectedViolation.speed_kmh - selectedViolation.speed_limit).toFixed(1)} km/h
                  </div>
                </div>

                <div style={{ gridColumn: 'span 2' }}>
                  <span style={{ fontSize: '0.75rem', color: '#64748b', textTransform: 'uppercase', fontWeight: 700 }}>Thời Điểm Vi Phạm</span>
                  <div style={{ fontWeight: 600, color: '#334155', fontSize: '0.875rem' }}>
                    {new Date(selectedViolation.violated_at).toLocaleString('vi-VN')}
                  </div>
                </div>

                {selectedViolation.cloud_url && (
                  <div style={{ gridColumn: 'span 2' }}>
                    <span style={{ fontSize: '0.75rem', color: '#64748b', textTransform: 'uppercase', fontWeight: 700 }}>Cloud CDN Storage</span>
                    <div style={{ fontSize: '0.8125rem', wordBreak: 'break-all', color: '#2563eb' }}>
                      <a href={selectedViolation.cloud_url} target="_blank" rel="noreferrer" style={{ color: '#2563eb', display: 'flex', alignItems: 'center', gap: '0.35rem' }}>
                        <span>{selectedViolation.cloud_url}</span>
                        <ExternalLink size={14} />
                      </a>
                    </div>
                  </div>
                )}
              </div>
            </div>

            {/* Modal Footer */}
            <div style={{
              padding: '1rem 1.5rem',
              borderTop: '1px solid #e2e8f0',
              display: 'flex',
              justifyContent: 'flex-end',
              gap: '0.75rem'
            }}>
              <a
                href={selectedViolation.cloud_url || `/api/violations/image/${selectedViolation.evidence_image_path}`}
                download={`bien_ban_vi_pham_${selectedViolation.id}.jpg`}
                target="_blank"
                rel="noreferrer"
                className="btn btn-primary"
                style={{ textDecoration: 'none', display: 'flex', alignItems: 'center', gap: '0.5rem' }}
              >
                <Download size={16} />
                <span>Tải Ảnh Bằng Chứng</span>
              </a>
              <button className="btn btn-secondary" onClick={() => setSelectedViolation(null)}>
                Đóng
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
