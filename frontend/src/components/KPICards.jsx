import React from 'react';
import { Car, Gauge, Activity, ArrowDownRight, ArrowUpRight } from 'lucide-react';

export default function KPICards({ summary, liveCounts }) {
  const total = liveCounts?.total || summary?.total_vehicles || 0;
  const inCount = liveCounts?.in || 0;
  const outCount = liveCounts?.out || 0;
  const avgSpeed = summary?.avg_speed || 0;
  const vpm = summary?.vehicles_per_minute || 0;

  return (
    <div className="kpi-grid">
      <div className="kpi-card blue">
        <div>
          <div className="kpi-title">Tổng Phương Tiện Đã Đếm</div>
          <div className="kpi-val">
            {total} <span className="kpi-unit">xe</span>
          </div>
        </div>
        <div className="kpi-icon" style={{ color: '#60a5fa' }}>
          <Car size={24} />
        </div>
      </div>

      <div className="kpi-card emerald">
        <div>
          <div className="kpi-title">Tốc Độ Trung Bình</div>
          <div className="kpi-val">
            {avgSpeed > 0 ? avgSpeed.toFixed(1) : '--'}
            <span className="kpi-unit">km/h</span>
          </div>
        </div>
        <div className="kpi-icon" style={{ color: '#34d399' }}>
          <Gauge size={24} />
        </div>
      </div>

      <div className="kpi-card amber">
        <div>
          <div className="kpi-title">Lưu Lượng Tức Thời</div>
          <div className="kpi-val">
            {vpm > 0 ? vpm.toFixed(1) : '--'}
            <span className="kpi-unit">xe/phút</span>
          </div>
        </div>
        <div className="kpi-icon" style={{ color: '#fbbf24' }}>
          <Activity size={24} />
        </div>
      </div>

      <div className="kpi-card cyan">
        <div>
          <div className="kpi-title">Hướng IN / OUT</div>
          <div className="kpi-val" style={{ fontSize: '1.5rem', display: 'flex', gap: '1rem', alignItems: 'center' }}>
            <span style={{ color: '#34d399', display: 'flex', alignItems: 'center', gap: '0.25rem' }}>
              <ArrowDownRight size={18} /> {inCount}
            </span>
            <span style={{ color: '#f43f5e', display: 'flex', alignItems: 'center', gap: '0.25rem' }}>
              <ArrowUpRight size={18} /> {outCount}
            </span>
          </div>
        </div>
        <div className="kpi-icon" style={{ color: '#06b6d4' }}>
          <Car size={24} />
        </div>
      </div>
    </div>
  );
}
