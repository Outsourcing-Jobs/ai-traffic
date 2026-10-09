import React from 'react';
import { 
  ShieldCheck, 
  Video, 
  Gauge, 
  Activity, 
  AlertTriangle, 
  Layers, 
  Cpu, 
  ArrowRight, 
  CheckCircle2, 
  FileSpreadsheet, 
  Cloud, 
  GraduationCap 
} from 'lucide-react';

export default function LandingHomePage({ onGoToLogin }) {
  const features = [
    {
      icon: <Cpu size={24} color="#2563eb" />,
      title: 'AI Nhận Diện Phương Tiện YOLO',
      desc: 'Tự động phát hiện và phân loại chuẩn xác 4 nhóm phương tiện chính: Ô tô con, Xe máy, Xe buýt và Xe tải với độ trễ thấp.'
    },
    {
      icon: <Activity size={24} color="#059669" />,
      title: 'Theo Vết Đa Đối Tượng (ByteTrack)',
      desc: 'Gán mã định danh (Track ID) duy nhất cho từng xe, duy trì quỹ đạo di chuyển mượt mà qua các frame ngay cả khi bị che khuất.'
    },
    {
      icon: <Gauge size={24} color="#d97706" />,
      title: 'Ước Lượng Tốc Độ (Homography)',
      desc: 'Ánh xạ 4 điểm phối cảnh từ pixel sang khoảng cách thực tế (mét) để tính toán vận tốc tức thời và tốc độ trung bình chuẩn xác.'
    },
    {
      icon: <AlertTriangle size={24} color="#dc2626" />,
      title: 'Phạt Nguội & Cảnh Báo Ùn Tắc',
      desc: 'Tự động phát hiện xe vượt tốc độ quy định, chụp ảnh bằng chứng có Watermark và đánh giá mức độ ùn tắc giao thông thời gian thực.'
    }
  ];

  return (
    <div style={{ maxWidth: '1200px', margin: '0 auto', padding: '1rem 0 3rem 0' }}>
      {/* Hero Section */}
      <div style={{
        textAlign: 'center',
        padding: '3.5rem 1.5rem 3rem 1.5rem',
        backgroundColor: '#ffffff',
        borderRadius: '24px',
        border: '1px solid #e2e8f0',
        boxShadow: '0 10px 30px -10px rgba(0, 0, 0, 0.05)',
        marginBottom: '2.5rem',
        position: 'relative',
        overflow: 'hidden'
      }}>
        {/* Subtle Background Badge */}
        <div style={{
          display: 'inline-flex',
          alignItems: 'center',
          gap: '0.5rem',
          backgroundColor: '#eff6ff',
          color: '#1d4ed8',
          padding: '0.4rem 1rem',
          borderRadius: '9999px',
          fontSize: '0.8125rem',
          fontWeight: 700,
          marginBottom: '1.25rem',
          border: '1px solid #bfdbfe'
        }}>
          <GraduationCap size={18} />
          <span>ĐỒ ÁN TỐT NGHIỆP CNTT • ĐHCN VIỆT - HUNG</span>
        </div>

        <h1 style={{
          fontSize: '2.25rem',
          fontWeight: 900,
          color: '#0f172a',
          lineHeight: 1.3,
          maxWidth: '900px',
          margin: '0 auto 1.25rem auto'
        }}>
          HỆ THỐNG XÁC ĐỊNH LƯU LƯỢNG & ƯỚC LƯỢNG TỐC ĐỘ GIAO THÔNG BẰNG CAMERA GIÁM SÁT
        </h1>

        <p style={{
          fontSize: '1.05rem',
          color: '#64748b',
          maxWidth: '780px',
          margin: '0 auto 2rem auto',
          lineHeight: 1.6
        }}>
          Ứng dụng mô hình Thị giác máy tính <strong>YOLO + ByteTrack + Ma trận Homography</strong> để tự động đếm xe theo làn, ước lượng vận tốc di chuyển, lập biên bản phạt nguội và phát hiện ùn tắc giao thông.
        </p>

        {/* Action Buttons */}
        <div style={{ display: 'flex', justifyContent: 'center', gap: '1rem', flexWrap: 'wrap' }}>
          <button
            onClick={onGoToLogin}
            className="btn btn-primary"
            style={{
              padding: '0.875rem 2rem',
              fontSize: '1rem',
              fontWeight: 800,
              borderRadius: '12px',
              display: 'flex',
              alignItems: 'center',
              gap: '0.625rem',
              boxShadow: '0 10px 15px -3px rgba(37, 99, 235, 0.3)'
            }}
          >
            <span>Đăng Nhập Quản Trị Hệ Thống</span>
            <ArrowRight size={18} />
          </button>
        </div>
      </div>

      {/* Thông Tin Đề Tài & Giảng Viên Hướng Dẫn */}
      <div style={{
        display: 'grid',
        gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))',
        gap: '1.25rem',
        marginBottom: '2.5rem'
      }}>
        <div className="card" style={{ borderLeft: '4px solid #2563eb' }}>
          <div style={{ fontSize: '0.75rem', fontWeight: 800, color: '#64748b', textTransform: 'uppercase' }}>Đơn Vị Đào Tạo</div>
          <div style={{ fontSize: '1.125rem', fontWeight: 800, color: '#0f172a', marginTop: '0.25rem' }}>
            Trường ĐHCN Việt - Hung
          </div>
          <div style={{ fontSize: '0.8125rem', color: '#64748b', marginTop: '0.2rem' }}>
            Khoa Công Nghệ Thông Tin (K46TP-CNTT)
          </div>
        </div>

        <div className="card" style={{ borderLeft: '4px solid #059669' }}>
          <div style={{ fontSize: '0.75rem', fontWeight: 800, color: '#64748b', textTransform: 'uppercase' }}>Giảng Viên Hướng Dẫn</div>
          <div style={{ fontSize: '1.125rem', fontWeight: 800, color: '#059669', marginTop: '0.25rem' }}>
            TS. Nguyễn Hồng Quân
          </div>
          <div style={{ fontSize: '0.8125rem', color: '#64748b', marginTop: '0.2rem' }}>
            Cán bộ Giảng dạy & Hướng dẫn Đồ án
          </div>
        </div>

        <div className="card" style={{ borderLeft: '4px solid #7c3aed' }}>
          <div style={{ fontSize: '0.75rem', fontWeight: 800, color: '#64748b', textTransform: 'uppercase' }}>Kiến Trúc Công Nghệ</div>
          <div style={{ fontSize: '1.125rem', fontWeight: 800, color: '#7c3aed', marginTop: '0.25rem' }}>
            FastAPI + React Vite + YOLO
          </div>
          <div style={{ fontSize: '0.8125rem', color: '#64748b', marginTop: '0.2rem' }}>
            Supervision, SQLite, Cloudinary CDN
          </div>
        </div>
      </div>

      {/* 4 Trụ Cột Tính Năng Nổi Bật */}
      <div style={{ marginBottom: '2.5rem' }}>
        <div style={{ textAlign: 'center', marginBottom: '1.75rem' }}>
          <h2 style={{ fontSize: '1.5rem', fontWeight: 900, color: '#0f172a', margin: '0 0 0.5rem 0' }}>
            CÁC PHÂN HỆ TÍNH NĂNG CỐT LÕI
          </h2>
          <p style={{ fontSize: '0.875rem', color: '#64748b', margin: 0 }}>
            Quy trình khép kín từ thu thập video, xử lý thị giác máy tính tới xuất báo cáo nghiệp vụ.
          </p>
        </div>

        <div style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fit, minmax(260px, 1fr))',
          gap: '1.5rem'
        }}>
          {features.map((item, index) => (
            <div key={index} className="card" style={{
              display: 'flex',
              flexDirection: 'column',
              padding: '1.5rem',
              borderRadius: '16px'
            }}>
              <div style={{
                width: '48px',
                height: '48px',
                borderRadius: '12px',
                backgroundColor: '#f8fafc',
                border: '1px solid #e2e8f0',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                marginBottom: '1rem'
              }}>
                {item.icon}
              </div>
              <h3 style={{ fontSize: '1.05rem', fontWeight: 800, color: '#0f172a', marginBottom: '0.5rem' }}>
                {item.title}
              </h3>
              <p style={{ fontSize: '0.875rem', color: '#64748b', lineHeight: 1.5, flex: 1, margin: 0 }}>
                {item.desc}
              </p>
            </div>
          ))}
        </div>
      </div>

      {/* Quy Trình Xử Lý Pipeline Minh Họa */}
      <div className="card" style={{ padding: '2rem' }}>
        <h3 style={{ fontSize: '1.125rem', fontWeight: 800, color: '#0f172a', marginBottom: '1.25rem', textAlign: 'center' }}>
          QUY TRÌNH XỬ LÝ DỮ LIỆU THỜI GIAN THỰC (REAL-TIME PIPELINE)
        </h3>

        <div style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))',
          gap: '1rem',
          textAlign: 'center'
        }}>
          <div style={{ padding: '1rem', backgroundColor: '#f8fafc', borderRadius: '12px', border: '1px solid #e2e8f0' }}>
            <div style={{ fontSize: '1.25rem', fontWeight: 900, color: '#2563eb' }}>BƯỚC 1</div>
            <div style={{ fontWeight: 700, color: '#0f172a', marginTop: '0.25rem', fontSize: '0.9375rem' }}>Nạp Luồng Video</div>
            <div style={{ fontSize: '0.75rem', color: '#64748b', marginTop: '0.25rem' }}>CCTV, RTSP hoặc File MP4</div>
          </div>

          <div style={{ padding: '1rem', backgroundColor: '#f8fafc', borderRadius: '12px', border: '1px solid #e2e8f0' }}>
            <div style={{ fontSize: '1.25rem', fontWeight: 900, color: '#2563eb' }}>BƯỚC 2</div>
            <div style={{ fontWeight: 700, color: '#0f172a', marginTop: '0.25rem', fontSize: '0.9375rem' }}>AI Detection & Tracking</div>
            <div style={{ fontSize: '0.75rem', color: '#64748b', marginTop: '0.25rem' }}>YOLOv8 + ByteTrack MOT</div>
          </div>

          <div style={{ padding: '1rem', backgroundColor: '#f8fafc', borderRadius: '12px', border: '1px solid #e2e8f0' }}>
            <div style={{ fontSize: '1.25rem', fontWeight: 900, color: '#2563eb' }}>BƯỚC 3</div>
            <div style={{ fontWeight: 700, color: '#0f172a', marginTop: '0.25rem', fontSize: '0.9375rem' }}>Homography & Đếm Vạch</div>
            <div style={{ fontSize: '0.75rem', color: '#64748b', marginTop: '0.25rem' }}>Ước lượng km/h & Lưu lượng</div>
          </div>

          <div style={{ padding: '1rem', backgroundColor: '#f8fafc', borderRadius: '12px', border: '1px solid #e2e8f0' }}>
            <div style={{ fontSize: '1.25rem', fontWeight: 900, color: '#2563eb' }}>BƯỚC 4</div>
            <div style={{ fontWeight: 700, color: '#0f172a', marginTop: '0.25rem', fontSize: '0.9375rem' }}>Phạt Nguội & Báo Cáo</div>
            <div style={{ fontSize: '0.75rem', color: '#64748b', marginTop: '0.25rem' }}>Ảnh Watermark + Xuất CSV</div>
          </div>
        </div>
      </div>
    </div>
  );
}
