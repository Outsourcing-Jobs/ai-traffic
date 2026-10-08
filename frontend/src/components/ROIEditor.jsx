import React, { useRef, useState, useEffect } from 'react';
import { MousePointer, Edit3, Save, RotateCcw, Camera, CheckCircle, Grid, Sliders } from 'lucide-react';
import { api } from '../services/api';

const V_WIDTH = 1280;
const V_HEIGHT = 720;

const DEFAULT_HOMOGRAPHY_POINTS = [
  [460, 260], // P1: Top-Left (Xa - Trái)
  [820, 260], // P2: Top-Right (Xa - Phải)
  [1060, 640], // P3: Bottom-Right (Gần - Phải)
  [220, 640]  // P4: Bottom-Left (Gần - Trái)
];

export default function ROIEditor({ session, onSaved }) {
  const canvasRef = useRef(null);
  const [snapshotImg, setSnapshotImg] = useState(null);
  const [loadingSnapshot, setLoadingSnapshot] = useState(false);
  const [saveSuccess, setSaveSuccess] = useState(false);

  // Chế độ chỉnh sửa: 'homography' (4 điểm phối cảnh), 'line' (vạch đếm), hoặc 'roi' (đa giác ROI)
  const [activeMode, setActiveMode] = useState('homography');

  // Tọa độ 4 Điểm Cân Chỉnh Homography (Top-Left, Top-Right, Bottom-Right, Bottom-Left)
  const [homoPoints, setHomoPoints] = useState(DEFAULT_HOMOGRAPHY_POINTS);
  const [roadWidthMeters, setRoadWidthMeters] = useState(10);
  const [roadLengthMeters, setRoadLengthMeters] = useState(25);
  const [draggingHomoIdx, setDraggingHomoIdx] = useState(null); // 0, 1, 2, 3

  // Tọa độ Vạch đếm P1, P2 (tỷ lệ chuẩn 1280x720)
  const [lineP1, setLineP1] = useState([150, 450]);
  const [lineP2, setLineP2] = useState([1130, 450]);
  const [draggingLinePoint, setDraggingLinePoint] = useState(null); // 'p1' hoặc 'p2'

  // Tọa độ Đa giác ROI: danh sách [[x, y], ...]
  const [roiPoints, setRoiPoints] = useState([]);

  // Load cấu hình sẵn có của session
  useEffect(() => {
    if (session?.config_json) {
      try {
        const cfg = JSON.parse(session.config_json);
        if (cfg.counting_lines && cfg.counting_lines.length > 0) {
          setLineP1(cfg.counting_lines[0].p1 || [150, 450]);
          setLineP2(cfg.counting_lines[0].p2 || [1130, 450]);
        }
        if (cfg.roi_polygon && cfg.roi_polygon.length >= 3) {
          setRoiPoints(cfg.roi_polygon);
        }
        if (cfg.homography) {
          const pts = cfg.homography.points || cfg.homography.source_pixels;
          if (pts && pts.length === 4) setHomoPoints(pts);
          if (cfg.homography.road_width_m) setRoadWidthMeters(cfg.homography.road_width_m);
          if (cfg.homography.road_length_m) setRoadLengthMeters(cfg.homography.road_length_m);
        }
      } catch (e) {
        console.error('Lỗi parse config_json:', e);
      }
    }
    loadSnapshot();
  }, [session?.id]);

  // Tải snapshot ảnh tĩnh từ camera/video
  const loadSnapshot = async () => {
    if (!session) return;
    setLoadingSnapshot(true);
    try {
      const img = new Image();
      img.crossOrigin = 'anonymous';
      img.src = api.getSnapshotUrl(session.id);
      img.onload = () => {
        setSnapshotImg(img);
        setLoadingSnapshot(false);
      };
      img.onerror = () => {
        setLoadingSnapshot(false);
      };
    } catch {
      setLoadingSnapshot(false);
    }
  };

  // Vẽ Canvas
  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext('2d');

    ctx.clearRect(0, 0, canvas.width, canvas.height);

    // 1. Vẽ ảnh snapshot nền
    if (snapshotImg) {
      ctx.drawImage(snapshotImg, 0, 0, canvas.width, canvas.height);
    } else {
      ctx.fillStyle = '#f1f5f9';
      ctx.fillRect(0, 0, canvas.width, canvas.height);
      ctx.fillStyle = '#64748b';
      ctx.font = '600 16px Plus Jakarta Sans';
      ctx.textAlign = 'center';
      ctx.fillText('Đang kết nối camera để lấy khung hình...', canvas.width / 2, canvas.height / 2);
    }

    const scaleX = canvas.width / V_WIDTH;
    const scaleY = canvas.height / V_HEIGHT;

    // 2. VẼ VÙNG 4 ĐIỂM HOMOGRAPHY (HÌNH THANG PHỐI CẢNH)
    if (homoPoints.length === 4) {
      const scaledH = homoPoints.map(([x, y]) => [x * scaleX, y * scaleY]);

      ctx.beginPath();
      ctx.moveTo(scaledH[0][0], scaledH[0][1]);
      ctx.lineTo(scaledH[1][0], scaledH[1][1]);
      ctx.lineTo(scaledH[2][0], scaledH[2][1]);
      ctx.lineTo(scaledH[3][0], scaledH[3][1]);
      ctx.closePath();

      // Nền bán trong suốt
      ctx.fillStyle = activeMode === 'homography' ? 'rgba(245, 158, 11, 0.22)' : 'rgba(245, 158, 11, 0.1)';
      ctx.fill();

      // Viền nét đứt phối cảnh
      ctx.setLineDash([6, 6]);
      ctx.strokeStyle = '#d97706';
      ctx.lineWidth = activeMode === 'homography' ? 3 : 2;
      ctx.stroke();

      // Vẽ các đường lưới phối cảnh bên trong (Perspective Grid)
      const steps = [0.33, 0.66];
      ctx.setLineDash([3, 4]);
      ctx.strokeStyle = 'rgba(217, 119, 6, 0.6)';
      ctx.lineWidth = 1.5;
      steps.forEach((t) => {
        // Đường ngang phối cảnh
        const lx = scaledH[0][0] + (scaledH[3][0] - scaledH[0][0]) * t;
        const ly = scaledH[0][1] + (scaledH[3][1] - scaledH[0][1]) * t;
        const rx = scaledH[1][0] + (scaledH[2][0] - scaledH[1][0]) * t;
        const ry = scaledH[1][1] + (scaledH[2][1] - scaledH[1][1]) * t;
        ctx.beginPath();
        ctx.moveTo(lx, ly);
        ctx.lineTo(rx, ry);
        ctx.stroke();

        // Đường dọc chia làn
        const tx = scaledH[0][0] + (scaledH[1][0] - scaledH[0][0]) * t;
        const ty = scaledH[0][1] + (scaledH[1][1] - scaledH[0][1]) * t;
        const bx = scaledH[3][0] + (scaledH[2][0] - scaledH[3][0]) * t;
        const by = scaledH[3][1] + (scaledH[2][1] - scaledH[3][1]) * t;
        ctx.beginPath();
        ctx.moveTo(tx, ty);
        ctx.lineTo(bx, by);
        ctx.stroke();
      });
      ctx.setLineDash([]); // Bỏ nét đứt

      // Vẽ 4 tay cầm điều khiển (Handles) cho 4 điểm Homography
      const pointLabels = [
        '1. Xa - Trái',
        '2. Xa - Phải',
        '3. Gần - Phải',
        '4. Gần - Trái'
      ];

      scaledH.forEach(([px, py], idx) => {
        ctx.beginPath();
        ctx.arc(px, py, activeMode === 'homography' ? 10 : 7, 0, Math.PI * 2);
        ctx.fillStyle = '#f59e0b';
        ctx.fill();
        ctx.strokeStyle = '#ffffff';
        ctx.lineWidth = 3;
        ctx.stroke();

        if (activeMode === 'homography') {
          // Nhãn điểm
          ctx.fillStyle = '#1e293b';
          ctx.fillRect(px - 45, py - 32, 90, 20);
          ctx.strokeStyle = '#d97706';
          ctx.strokeRect(px - 45, py - 32, 90, 20);
          ctx.fillStyle = '#ffffff';
          ctx.font = 'bold 11px Plus Jakarta Sans';
          ctx.textAlign = 'center';
          ctx.fillText(pointLabels[idx], px, py - 18);
        }
      });
    }

    // 3. VẼ VÙNG ĐA GIÁC ROI (NẾU CÓ)
    if (roiPoints.length > 0) {
      ctx.beginPath();
      ctx.moveTo(roiPoints[0][0] * scaleX, roiPoints[0][1] * scaleY);
      for (let i = 1; i < roiPoints.length; i++) {
        ctx.lineTo(roiPoints[i][0] * scaleX, roiPoints[i][1] * scaleY);
      }
      ctx.closePath();
      ctx.fillStyle = activeMode === 'roi' ? 'rgba(37, 99, 235, 0.25)' : 'rgba(37, 99, 235, 0.12)';
      ctx.fill();
      ctx.strokeStyle = '#2563eb';
      ctx.lineWidth = 2.5;
      ctx.stroke();

      roiPoints.forEach(([x, y]) => {
        ctx.beginPath();
        ctx.arc(x * scaleX, y * scaleY, 6, 0, Math.PI * 2);
        ctx.fillStyle = '#3b82f6';
        ctx.fill();
        ctx.strokeStyle = '#ffffff';
        ctx.lineWidth = 2;
        ctx.stroke();
      });
    }

    // 4. VẼ VẠCH ĐẾM (COUNTING LINE)
    const p1x = lineP1[0] * scaleX;
    const p1y = lineP1[1] * scaleY;
    const p2x = lineP2[0] * scaleX;
    const p2y = lineP2[1] * scaleY;

    ctx.beginPath();
    ctx.moveTo(p1x, p1y);
    ctx.lineTo(p2x, p2y);
    ctx.strokeStyle = '#10b981';
    ctx.lineWidth = activeMode === 'line' ? 4.5 : 3;
    ctx.stroke();

    // Điểm đầu mút P1, P2
    [ [p1x, p1y], [p2x, p2y] ].forEach(([px, py], i) => {
      ctx.beginPath();
      ctx.arc(px, py, activeMode === 'line' ? 10 : 7, 0, Math.PI * 2);
      ctx.fillStyle = '#10b981';
      ctx.fill();
      ctx.strokeStyle = '#ffffff';
      ctx.lineWidth = 3;
      ctx.stroke();
    });

    // Chú thích vạch đếm
    ctx.fillStyle = '#065f46';
    ctx.font = 'bold 12px Plus Jakarta Sans';
    ctx.textAlign = 'center';
    ctx.fillText('VẠCH ĐẾM LƯU LƯỢNG', (p1x + p2x) / 2, (p1y + p2y) / 2 - 12);
  }, [snapshotImg, lineP1, lineP2, roiPoints, homoPoints, activeMode]);

  // Chuyển đổi tọa độ chuột
  const getCanvasCoords = (e) => {
    const canvas = canvasRef.current;
    const rect = canvas.getBoundingClientRect();
    const scaleX = V_WIDTH / canvas.width;
    const scaleY = V_HEIGHT / canvas.height;
    return [
      Math.round((e.clientX - rect.left) * scaleX),
      Math.round((e.clientY - rect.top) * scaleY)
    ];
  };

  const handleMouseDown = (e) => {
    const [x, y] = getCanvasCoords(e);

    if (activeMode === 'homography') {
      // Tìm điểm gần nhất trong 4 điểm Homography
      for (let i = 0; i < homoPoints.length; i++) {
        const dist = Math.hypot(x - homoPoints[i][0], y - homoPoints[i][1]);
        if (dist < 40) {
          setDraggingHomoIdx(i);
          return;
        }
      }
    } else if (activeMode === 'line') {
      const distP1 = Math.hypot(x - lineP1[0], y - lineP1[1]);
      const distP2 = Math.hypot(x - lineP2[0], y - lineP2[1]);
      if (distP1 < 40) setDraggingLinePoint('p1');
      else if (distP2 < 40) setDraggingLinePoint('p2');
    } else if (activeMode === 'roi') {
      setRoiPoints((prev) => [...prev, [x, y]]);
    }
  };

  const handleMouseMove = (e) => {
    const [x, y] = getCanvasCoords(e);
    if (draggingHomoIdx !== null) {
      setHomoPoints((prev) => {
        const next = [...prev];
        next[draggingHomoIdx] = [x, y];
        return next;
      });
    } else if (draggingLinePoint === 'p1') {
      setLineP1([x, y]);
    } else if (draggingLinePoint === 'p2') {
      setLineP2([x, y]);
    }
  };

  const handleMouseUp = () => {
    setDraggingHomoIdx(null);
    setDraggingLinePoint(null);
  };

  // Lưu cấu hình toàn bộ xuống Backend
  const handleSave = async () => {
    if (!session) return;
    const payload = {
      counting_lines: [
        {
          id: 1,
          name: 'Vạch chính',
          p1: lineP1,
          p2: lineP2,
          direction_in: 'down',
          direction_out: 'up'
        }
      ],
      roi_polygon: roiPoints,
      homography: {
        points: homoPoints,
        source_pixels: homoPoints,
        road_width_m: roadWidthMeters,
        road_length_m: roadLengthMeters,
        target_meters: [
          [0.0, 0.0],
          [roadWidthMeters, 0.0],
          [roadWidthMeters, roadLengthMeters],
          [0.0, roadLengthMeters]
        ]
      }
    };

    try {
      await api.updateConfig(session.id, payload);
      setSaveSuccess(true);
      setTimeout(() => setSaveSuccess(false), 3500);
      if (onSaved) onSaved(payload);
    } catch (err) {
      alert(err.message);
    }
  };

  return (
    <div className="card">
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1.25rem' }}>
        <div>
          <h2 style={{ fontSize: '1.2rem', fontWeight: 800, color: '#0f172a' }}>
            CÂN CHỈNH PHỐI CẢNH HOMOGRAPHY & THIẾT LẬP VẠCH ĐẾM
          </h2>
          <p style={{ fontSize: '0.875rem', color: '#64748b' }}>
            Biến đổi không gian ảnh sang tọa độ mét thực tế (Khắc phục biến dạng góc nhìn Perspective Distortion).
          </p>
        </div>

        <div style={{ display: 'flex', gap: '0.75rem', alignItems: 'center' }}>
          <button
            id="reload-snapshot-btn"
            className="btn btn-secondary"
            onClick={loadSnapshot}
            disabled={loadingSnapshot}
          >
            <Camera size={16} />
            <span>Chụp Lại Frame</span>
          </button>

          <button
            id="save-roi-config-btn"
            className="btn btn-primary"
            onClick={handleSave}
          >
            <Save size={16} />
            <span>Lưu Cấu Hình Toàn Bộ</span>
          </button>
        </div>
      </div>

      {saveSuccess && (
        <div style={{ padding: '0.875rem 1rem', background: '#ecfdf5', border: '1px solid #10b981', borderRadius: '8px', color: '#065f46', marginBottom: '1rem', display: 'flex', alignItems: 'center', gap: '0.625rem', fontWeight: 600 }}>
          <CheckCircle size={20} style={{ color: '#059669' }} />
          <span>Đã lưu thành công! Ma trận Homography và Vạch đếm đã được áp dụng trực tiếp vào quá trình xử lý video.</span>
        </div>
      )}

      {/* Toolbar 3 Chế Độ */}
      <div style={{ display: 'flex', gap: '1rem', marginBottom: '1rem', alignItems: 'center', flexWrap: 'wrap' }}>
        <div style={{ display: 'flex', background: '#f1f5f9', borderRadius: '8px', padding: '4px', border: '1px solid #e2e8f0' }}>
          <button
            id="tool-homo-btn"
            className={`btn ${activeMode === 'homography' ? 'btn-primary' : 'btn-secondary'}`}
            style={{ padding: '0.45rem 0.9rem', fontSize: '0.8125rem' }}
            onClick={() => setActiveMode('homography')}
          >
            <Grid size={15} />
            <span>4 Điểm Homography (Đo Tốc Độ)</span>
          </button>

          <button
            id="tool-line-btn"
            className={`btn ${activeMode === 'line' ? 'btn-primary' : 'btn-secondary'}`}
            style={{ padding: '0.45rem 0.9rem', fontSize: '0.8125rem' }}
            onClick={() => setActiveMode('line')}
          >
            <Edit3 size={15} />
            <span>Vạch Đếm (Lưu Lượng)</span>
          </button>

          <button
            id="tool-roi-btn"
            className={`btn ${activeMode === 'roi' ? 'btn-primary' : 'btn-secondary'}`}
            style={{ padding: '0.45rem 0.9rem', fontSize: '0.8125rem' }}
            onClick={() => setActiveMode('roi')}
          >
            <MousePointer size={15} />
            <span>Đa Giác ROI (Khu Vực)</span>
          </button>
        </div>

        {activeMode === 'homography' && (
          <div style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.4rem', fontSize: '0.875rem' }}>
              <span style={{ color: '#475569', fontWeight: 600 }}>Chiều rộng làn $W$ (m):</span>
              <input
                type="number"
                value={roadWidthMeters}
                onChange={(e) => setRoadWidthMeters(Number(e.target.value))}
                style={{ width: '65px', padding: '4px 8px', borderRadius: '6px', border: '1px solid #cbd5e1', fontWeight: 700 }}
              />
            </div>

            <div style={{ display: 'flex', alignItems: 'center', gap: '0.4rem', fontSize: '0.875rem' }}>
              <span style={{ color: '#475569', fontWeight: 600 }}>Chiều dài đoạn $L$ (m):</span>
              <input
                type="number"
                value={roadLengthMeters}
                onChange={(e) => setRoadLengthMeters(Number(e.target.value))}
                style={{ width: '65px', padding: '4px 8px', borderRadius: '6px', border: '1px solid #cbd5e1', fontWeight: 700 }}
              />
            </div>

            <button
              className="btn btn-secondary"
              style={{ padding: '0.4rem 0.75rem', fontSize: '0.8125rem' }}
              onClick={() => setHomoPoints(DEFAULT_HOMOGRAPHY_POINTS)}
              title="Khôi phục vị trí 4 điểm mốc ban đầu"
            >
              <RotateCcw size={14} />
              <span>Khôi Phục Mặc Định</span>
            </button>
          </div>
        )}

        {activeMode === 'roi' && (
          <button
            className="btn btn-secondary"
            style={{ padding: '0.4rem 0.8rem', fontSize: '0.8125rem' }}
            onClick={() => setRoiPoints([])}
          >
            <RotateCcw size={14} />
            <span>Xóa Đa Giác ({roiPoints.length} điểm)</span>
          </button>
        )}
      </div>

      {/* Vùng Vẽ HTML5 Canvas */}
      <div style={{ width: '100%', background: '#0f172a', borderRadius: '12px', overflow: 'hidden', border: '1px solid #e2e8f0', position: 'relative' }}>
        <canvas
          ref={canvasRef}
          width={1024}
          height={576}
          style={{
            width: '100%',
            height: 'auto',
            display: 'block',
            cursor: activeMode === 'roi' ? 'crosshair' : 'grab'
          }}
          onMouseDown={handleMouseDown}
          onMouseMove={handleMouseMove}
          onMouseUp={handleMouseUp}
        />
      </div>

      {/* Ghi chú hướng dẫn sử dụng nhanh */}
      <div style={{ marginTop: '0.875rem', padding: '0.75rem 1rem', background: '#f8fafc', borderRadius: '8px', border: '1px solid #e2e8f0', fontSize: '0.8125rem', color: '#64748b', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <div>
          {activeMode === 'homography' && (
            <span>💡 <strong>Hướng dẫn Homography:</strong> Kéo 4 góc màu vàng cam đặt khít vào 4 góc của 1 đoạn mặt đường (2 điểm phía xa và 2 điểm phía gần). Nhập kích thước $W \times L$ tương ứng để chuẩn hóa tốc độ chính xác 100%.</span>
          )}
          {activeMode === 'line' && (
            <span>💡 <strong>Hướng dẫn Vạch Đếm:</strong> Kéo 2 đầu mút màu xanh lá đặt cắt ngang qua các làn đường cần đếm xe.</span>
          )}
          {activeMode === 'roi' && (
            <span>💡 <strong>Hướng dẫn Đa Giác ROI:</strong> Click chuột liên tiếp các điểm để giới hạn vùng camera cần theo dõi, bỏ qua các vùng ngoài lề.</span>
          )}
        </div>
      </div>
    </div>
  );
}
