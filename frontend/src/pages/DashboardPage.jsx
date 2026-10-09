import React, { useState, useEffect } from 'react';
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  BarElement,
  ArcElement,
  Title,
  Tooltip,
  Legend
} from 'chart.js';
import { Line, Doughnut } from 'react-chartjs-2';
import { api } from '../services/api';
import { PieChart, TrendingUp, RefreshCw, FileSpreadsheet, Download } from 'lucide-react';

ChartJS.register(
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  BarElement,
  ArcElement,
  Title,
  Tooltip,
  Legend
);

export default function DashboardPage({ session }) {
  const [stats, setStats] = useState([]);
  const [summary, setSummary] = useState(null);
  const [loading, setLoading] = useState(false);

  const loadData = async () => {
    if (!session) return;
    setLoading(true);
    try {
      const [statsData, sumData] = await Promise.all([
        api.getStats(session.id),
        api.getSummary(session.id)
      ]);
      setStats(statsData);
      setSummary(sumData);
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
    const interval = setInterval(loadData, 5000);
    return () => clearInterval(interval);
  }, [session?.id]);

  // Dữ liệu cho Biểu đồ Đường: Lưu lượng xe theo thời gian
  const lineLabels = stats.map((s) => new Date(s.timestamp).toLocaleTimeString('vi-VN'));
  const lineData = {
    labels: lineLabels.length > 0 ? lineLabels : ['00:00', '00:01', '00:02', '00:03'],
    datasets: [
      {
        label: 'Tổng số xe / phút',
        data: stats.length > 0 ? stats.map((s) => s.total_count) : [5, 12, 19, 15],
        borderColor: '#2563eb',
        backgroundColor: 'rgba(37, 99, 235, 0.12)',
        tension: 0.35,
        fill: true
      },
      {
        label: 'Tốc độ TB (km/h)',
        data: stats.length > 0 ? stats.map((s) => s.avg_speed) : [28, 32, 29, 31],
        borderColor: '#059669',
        borderDash: [5, 5],
        tension: 0.35,
        fill: false
      }
    ]
  };

  // Dữ liệu cho Biểu đồ Tròn: Tỷ trọng loại xe
  const byType = summary?.by_type || { car: 12, motorcycle: 8, truck: 4, bus: 2 };
  const doughnutData = {
    labels: ['Ô tô con', 'Xe máy', 'Xe tải', 'Xe buýt'],
    datasets: [
      {
        data: [byType.car || 0, byType.motorcycle || 0, byType.truck || 0, byType.bus || 0],
        backgroundColor: ['#2563eb', '#059669', '#d97706', '#7c3aed'],
        borderWidth: 2,
        borderColor: '#ffffff'
      }
    ]
  };

  const chartOptions = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: {
        labels: {
          color: '#334155',
          font: { family: 'Plus Jakarta Sans', weight: '600' }
        }
      }
    },
    scales: {
      x: {
        ticks: { color: '#64748b' },
        grid: { color: 'rgba(0, 0, 0, 0.05)' }
      },
      y: {
        ticks: { color: '#64748b' },
        grid: { color: 'rgba(0, 0, 0, 0.05)' }
      }
    }
  };

  return (
    <div>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1.5rem', flexWrap: 'wrap', gap: '1rem' }}>
        <div>
          <h2 style={{ fontSize: '1.25rem', fontWeight: 800, color: '#0f172a' }}>DASHBOARD PHÂN TÍCH LƯU LƯỢNG & TỐC ĐỘ</h2>
          <p style={{ fontSize: '0.875rem', color: '#64748b' }}>
            Biểu đồ trực quan hóa dữ liệu thống kê phục vụ đánh giá mật độ giao thông và tốc độ lưu thông.
          </p>
        </div>

        <div style={{ display: 'flex', gap: '0.75rem', alignItems: 'center' }}>
          {session && (
            <>
              <a
                href={api.getExportCsvUrl(session.id)}
                download
                className="btn btn-secondary"
                style={{ textDecoration: 'none', display: 'flex', alignItems: 'center', gap: '0.5rem', color: '#2563eb', borderColor: '#bfdbfe' }}
              >
                <FileSpreadsheet size={16} />
                <span>Xuất CSV Lưu Lượng</span>
              </a>
              <a
                href={api.getExportViolationsCsvUrl(session.id)}
                download
                className="btn btn-secondary"
                style={{ textDecoration: 'none', display: 'flex', alignItems: 'center', gap: '0.5rem', color: '#dc2626', borderColor: '#fecaca' }}
              >
                <Download size={16} />
                <span>Xuất CSV Vi Phạm</span>
              </a>
            </>
          )}

          <button className="btn btn-secondary" onClick={loadData} disabled={loading}>
            <RefreshCw size={16} className={loading ? 'animate-spin' : ''} />
            <span>Làm Mới</span>
          </button>
        </div>
      </div>

      {/* Grid biểu đồ chính */}
      <div style={{ display: 'grid', gridTemplateColumns: 'minmax(0, 2fr) minmax(0, 1fr)', gap: '1.5rem', marginBottom: '1.5rem' }}>
        {/* Biểu đồ đường */}
        <div className="card">
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '1rem', color: '#1d4ed8' }}>
            <TrendingUp size={20} />
            <h3 style={{ fontSize: '0.9375rem', fontWeight: 800 }}>DIỄN BIẾN LƯU LƯỢNG & VẬN TỐC THEO THỜI GIAN</h3>
          </div>
          <div style={{ height: '320px' }}>
            <Line data={lineData} options={chartOptions} />
          </div>
        </div>

        {/* Biểu đồ tròn cơ cấu loại xe */}
        <div className="card">
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '1rem', color: '#7c3aed' }}>
            <PieChart size={20} />
            <h3 style={{ fontSize: '0.9375rem', fontWeight: 800 }}>CƠ CẤU PHƯƠNG TIỆN GIAO THÔNG</h3>
          </div>
          <div style={{ height: '320px', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
            <Doughnut
              data={doughnutData}
              options={{
                maintainAspectRatio: false,
                plugins: { legend: { position: 'bottom', labels: { color: '#334155', font: { weight: '600' } } } }
              }}
            />
          </div>
        </div>
      </div>

      {/* Bảng Dữ Liệu Thống Kê Chi Tiết CSDL */}
      <div className="card">
        <h3 style={{ fontSize: '0.9375rem', fontWeight: 800, marginBottom: '1rem', color: '#0f172a' }}>
          BẢNG THỐNG KÊ CHI TIẾT (LƯU TRỮ CSDL TRAFFIC_STATS)
        </h3>
        <table className="custom-table">
          <thead>
            <tr>
              <th>Thời Điểm</th>
              <th>Chu Kỳ</th>
              <th>Ô tô Con</th>
              <th>Xe Máy</th>
              <th>Xe Tải</th>
              <th>Xe Buýt</th>
              <th>Tổng Số Xe</th>
              <th>Tốc Độ TB</th>
              <th>Tốc Độ Tối Đa</th>
            </tr>
          </thead>
          <tbody>
            {stats.length > 0 ? (
              stats.map((row) => (
                <tr key={row.id}>
                  <td style={{ color: '#64748b' }}>{new Date(row.timestamp).toLocaleString('vi-VN')}</td>
                  <td>{row.period_min} phút</td>
                  <td>{row.car_count}</td>
                  <td>{row.moto_count}</td>
                  <td>{row.truck_count}</td>
                  <td>{row.bus_count}</td>
                  <td style={{ fontWeight: 700, color: '#2563eb' }}>{row.total_count}</td>
                  <td className="font-mono">{row.avg_speed.toFixed(1)} km/h</td>
                  <td className="font-mono" style={{ color: '#e11d48', fontWeight: 600 }}>{row.max_speed.toFixed(1)} km/h</td>
                </tr>
              ))
            ) : (
              <tr>
                <td colSpan="9" style={{ textAlign: 'center', color: '#94a3b8', padding: '1.5rem' }}>
                  Hệ thống đang tích lũy dữ liệu thống kê (CSDL tổng hợp tự động mỗi chu kỳ 1 phút).
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}
