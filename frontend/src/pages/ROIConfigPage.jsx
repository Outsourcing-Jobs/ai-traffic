import React from 'react';
import ROIEditor from '../components/ROIEditor';
import { HelpCircle, ShieldCheck } from 'lucide-react';

export default function ROIConfigPage({ session, onSaved }) {
  return (
    <div>
      <div style={{ display: 'grid', gridTemplateColumns: 'minmax(0, 2fr) minmax(0, 1.15fr)', gap: '1.5rem' }}>
        <div>
          <ROIEditor session={session} onSaved={onSaved} />
        </div>

        <div style={{ display: 'flex', flexDirection: 'column', gap: '1.25rem' }}>
          {/* Card 1: Nguyên Lý Biến Đổi Homography */}
          <div className="card">
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '0.875rem', color: '#d97706' }}>
              <HelpCircle size={20} />
              <h3 style={{ fontSize: '0.9375rem', fontWeight: 800 }}>NGUYÊN LÝ BIẾN ĐỔI HOMOGRAPHY (3x3)</h3>
            </div>
            <p style={{ fontSize: '0.8125rem', color: '#475569', lineHeight: '1.6', marginBottom: '0.75rem' }}>
              Do camera quan sát đặt ở góc chéo, xuất hiện hiện tượng <strong>Biến dạng phối cảnh (Perspective Distortion)</strong>: xe ở xa trông nhỏ hơn nhiều so với xe ở gần.
            </p>
            <div style={{ background: '#f8fafc', padding: '0.75rem', borderRadius: '8px', border: '1px solid var(--border-color)', fontSize: '0.8125rem', color: '#0369a1', fontFamily: 'monospace', fontWeight: 600, marginBottom: '0.75rem' }}>
              [X, Y, 1]ᵀ = H · [u, v, 1]ᵀ
            </div>
            <ul style={{ fontSize: '0.8125rem', color: '#475569', paddingLeft: '1.15rem', lineHeight: '1.7' }}>
              <li><strong>4 Điểm Màu Cam:</strong> Chọn 4 góc của 1 đoạn mặt đường (2 điểm phía xa, 2 điểm phía gần).</li>
              <li><strong>Kích Thước $W \times L$:</strong> Nhập chiều rộng mặt làn $W$ (mét) và chiều dài đoạn đường $L$ (mét).</li>
              <li>Hệ thống tự động giải ma trận $H$ bằng <code>cv2.getPerspectiveTransform</code> để chuyển đổi chính xác từ <strong>pixel sang mét</strong>.</li>
            </ul>
          </div>

          {/* Card 2: Nghiệm Pháp Khắc Phục Các Thách Thức */}
          <div className="card">
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '0.875rem', color: '#059669' }}>
              <ShieldCheck size={20} />
              <h3 style={{ fontSize: '0.9375rem', fontWeight: 800 }}>XỬ LÝ 4 THÁCH THỨC VIDEO GIAO THÔNG</h3>
            </div>
            <ul style={{ fontSize: '0.8125rem', color: '#475569', paddingLeft: '1.15rem', lineHeight: '1.75' }}>
              <li>
                <strong>Che khuất (Occlusion):</strong> Thuật toán <em>ByteTrack</em> liên kết 2 tầng và giữ bộ đệm 30 frame giúp xe không bị mất ID khi bị che khuất tạm thời.
              </li>
              <li>
                <strong>Rung lắc camera (Shake / Jitter):</strong> Lấy điểm đáy tiếp xúc mặt đường (bottom-center) kết hợp bộ lọc trung bình di động (Moving Average) để làm mịn vận tốc.
              </li>
              <li>
                <strong>Biến dạng phối cảnh:</strong> Triệt tiêu 100% sai số khoảng cách nhờ ma trận chiếu phối cảnh Homography phía trên.
              </li>
              <li>
                <strong>Ánh sáng / Thời tiết:</strong> Mạng YOLOv8n tiền huấn luyện với dữ liệu tăng cường (Mosaic / HSV) nhận diện xe bền vững cả ngày và chập tối.
              </li>
            </ul>
          </div>
        </div>
      </div>
    </div>
  );
}
