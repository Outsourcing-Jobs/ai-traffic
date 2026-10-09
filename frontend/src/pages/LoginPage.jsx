import React, { useState } from 'react';
import { api } from '../services/api';
import { 
  Lock, 
  User, 
  ShieldCheck, 
  ArrowRight, 
  Radio, 
  AlertCircle, 
  Eye, 
  EyeOff, 
  Cpu, 
  Gauge, 
  Video, 
  Sparkles,
  CheckCircle2
} from 'lucide-react';

export default function LoginPage({ onLoginSuccess }) {
  const [username, setUsername] = useState('admin');
  const [password, setPassword] = useState('admin123');
  const [showPassword, setShowPassword] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setLoading(true);
    try {
      const data = await api.login(username, password);
      onLoginSuccess(data.user);
    } catch (err) {
      setError(err.message || 'Tên đăng nhập hoặc mật khẩu không chính xác');
    } finally {
      setLoading(false);
    }
  };

  const handleFillDemo = () => {
    setUsername('admin');
    setPassword('admin123');
    setError('');
  };

  return (
    <div style={{
      minHeight: '100vh',
      width: '100vw',
      position: 'fixed',
      top: 0,
      left: 0,
      display: 'flex',
      flexDirection: 'column',
      background: 'radial-gradient(circle at 15% 15%, rgba(37, 99, 235, 0.08), transparent 45%), radial-gradient(circle at 85% 85%, rgba(6, 182, 212, 0.07), transparent 40%), linear-gradient(135deg, #f8fafc 0%, #f1f5f9 100%)',
      color: '#0f172a',
      overflowY: 'auto',
      zIndex: 100
    }}>
      {/* Background Dot Pattern */}
      <div style={{
        position: 'absolute',
        inset: 0,
        backgroundImage: 'radial-gradient(#cbd5e1 1px, transparent 1px)',
        backgroundSize: '28px 28px',
        opacity: 0.55,
        pointerEvents: 'none'
      }} />

      {/* Top Bar */}
      <header style={{
        position: 'relative',
        zIndex: 10,
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        padding: '1.125rem 2.5rem',
        borderBottom: '1px solid #e2e8f0',
        backdropFilter: 'blur(12px)',
        background: 'rgba(255, 255, 255, 0.85)',
        boxShadow: '0 1px 4px rgba(0, 0, 0, 0.03)'
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
          <div style={{
            width: '38px',
            height: '38px',
            borderRadius: '10px',
            background: 'linear-gradient(135deg, #2563eb, #0284c7)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            boxShadow: '0 4px 10px rgba(37, 99, 235, 0.25)'
          }}>
            <Radio size={20} color="#ffffff" />
          </div>
          <div>
            <div style={{
              fontSize: '1.125rem',
              fontWeight: 900,
              letterSpacing: '-0.02em',
              background: 'linear-gradient(135deg, #1d4ed8, #0284c7)',
              WebkitBackgroundClip: 'text',
              WebkitTextFillColor: 'transparent'
            }}>
              AI TRAFFIC MONITOR
            </div>
            <div style={{ fontSize: '0.6875rem', color: '#64748b', letterSpacing: '0.05em', textTransform: 'uppercase', fontWeight: 600 }}>
              Hệ Thống Quản Lý Giao Thông Thông Minh (ITS)
            </div>
          </div>
        </div>

        <div style={{
          display: 'inline-flex',
          alignItems: 'center',
          gap: '0.5rem',
          padding: '0.35rem 0.85rem',
          borderRadius: '9999px',
          background: '#ecfdf5',
          border: '1px solid #a7f3d0',
          color: '#059669',
          fontSize: '0.75rem',
          fontWeight: 800
        }}>
          <span style={{
            width: '7px',
            height: '7px',
            borderRadius: '50%',
            backgroundColor: '#10b981',
            boxShadow: '0 0 6px #10b981'
          }} />
          <span>HỆ THỐNG TRỰC TUYẾN</span>
        </div>
      </header>

      {/* Main Container */}
      <main style={{
        position: 'relative',
        zIndex: 10,
        flex: 1,
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        padding: '2.5rem 1.5rem',
        maxWidth: '1200px',
        margin: '0 auto',
        width: '100%'
      }}>
        <div style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fit, minmax(360px, 1fr))',
          gap: '3.5rem',
          alignItems: 'center',
          width: '100%'
        }}>
          {/* Cột Trái: Giới thiệu hệ thống & tính năng */}
          <div style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
            <div style={{
              display: 'inline-flex',
              alignItems: 'center',
              gap: '0.5rem',
              padding: '0.35rem 0.85rem',
              borderRadius: '9999px',
              backgroundColor: '#eff6ff',
              border: '1px solid #bfdbfe',
              color: '#2563eb',
              fontSize: '0.75rem',
              fontWeight: 800,
              width: 'fit-content'
            }}>
              <Sparkles size={14} />
              <span>TRUNG TÂM GIÁM SÁT GIAO THÔNG THÔNG MINH</span>
            </div>

            <div>
              <h1 style={{
                fontSize: '2.25rem',
                fontWeight: 900,
                lineHeight: 1.25,
                margin: '0 0 0.75rem 0',
                color: '#0f172a',
                letterSpacing: '-0.02em'
              }}>
                Giám Sát Lưu Lượng & Đo Tốc Độ Phương Tiện
              </h1>
              <p style={{ fontSize: '0.9375rem', color: '#475569', lineHeight: 1.65, margin: 0 }}>
                Hệ thống ứng dụng mô hình học sâu <strong>YOLOv8</strong> kết hợp thuật toán theo vết <strong>ByteTrack</strong> và biến đổi phối cảnh <strong>Homography</strong>, phục vụ đếm xe đa làn và phát hiện vi phạm tốc độ tự động.
              </p>
            </div>

            {/* 3 Thẻ tính năng sáng sủa, trang nhã */}
            <div style={{ display: 'flex', flexDirection: 'column', gap: '0.875rem' }}>
              <div style={{
                display: 'flex',
                gap: '1rem',
                alignItems: 'flex-start',
                padding: '1rem 1.125rem',
                borderRadius: '14px',
                background: '#ffffff',
                border: '1px solid #e2e8f0',
                boxShadow: '0 2px 8px rgba(15, 23, 42, 0.04)'
              }}>
                <div style={{
                  padding: '0.6rem',
                  borderRadius: '10px',
                  background: '#eff6ff',
                  color: '#2563eb'
                }}>
                  <Cpu size={20} />
                </div>
                <div>
                  <div style={{ fontSize: '0.875rem', fontWeight: 800, color: '#0f172a' }}>
                    Nhận Diện & Theo Vết Thời Gian Thực
                  </div>
                  <div style={{ fontSize: '0.75rem', color: '#64748b', marginTop: '0.2rem', lineHeight: 1.5 }}>
                    Phát hiện đồng thời ô tô, xe máy, xe tải, xe buýt với cơ chế Multi-Object Tracking ổn định ID.
                  </div>
                </div>
              </div>

              <div style={{
                display: 'flex',
                gap: '1rem',
                alignItems: 'flex-start',
                padding: '1rem 1.125rem',
                borderRadius: '14px',
                background: '#ffffff',
                border: '1px solid #e2e8f0',
                boxShadow: '0 2px 8px rgba(15, 23, 42, 0.04)'
              }}>
                <div style={{
                  padding: '0.6rem',
                  borderRadius: '10px',
                  background: '#ecfdf5',
                  color: '#059669'
                }}>
                  <Gauge size={20} />
                </div>
                <div>
                  <div style={{ fontSize: '0.875rem', fontWeight: 800, color: '#0f172a' }}>
                    Ước Lượng Tốc Độ & Đếm Đa Điểm Neo
                  </div>
                  <div style={{ fontSize: '0.75rem', color: '#64748b', marginTop: '0.2rem', lineHeight: 1.5 }}>
                    Chuyển đổi phối cảnh camera sang mặt đất thực tế (mét) với độ trễ thấp & đếm lưu lượng In / Out chuẩn xác.
                  </div>
                </div>
              </div>

              <div style={{
                display: 'flex',
                gap: '1rem',
                alignItems: 'flex-start',
                padding: '1rem 1.125rem',
                borderRadius: '14px',
                background: '#ffffff',
                border: '1px solid #e2e8f0',
                boxShadow: '0 2px 8px rgba(15, 23, 42, 0.04)'
              }}>
                <div style={{
                  padding: '0.6rem',
                  borderRadius: '10px',
                  background: '#fff1f2',
                  color: '#e11d48'
                }}>
                  <Video size={20} />
                </div>
                <div>
                  <div style={{ fontSize: '0.875rem', fontWeight: 800, color: '#0f172a' }}>
                    Phát Hiện Vi Phạm Tốc Độ (Phạt Nguội)
                  </div>
                  <div style={{ fontSize: '0.75rem', color: '#64748b', marginTop: '0.2rem', lineHeight: 1.5 }}>
                    Tự động chụp ảnh chứng cứ, đóng dấu thời gian, đo vận tốc và xuất báo cáo dữ liệu vi phạm.
                  </div>
                </div>
              </div>
            </div>

            {/* Thông tin đồ án tốt nghiệp */}
            <div style={{
              fontSize: '0.8125rem',
              color: '#64748b',
              paddingTop: '0.875rem',
              borderTop: '1px solid #e2e8f0',
              display: 'flex',
              alignItems: 'center',
              gap: '0.5rem',
              fontWeight: 500
            }}>
              <CheckCircle2 size={16} color="#2563eb" />
              <span>Đồ Án Tốt Nghiệp Ngành CNTT • GVHD: TS. Nguyễn Hồng Quân</span>
            </div>
          </div>

          {/* Cột Phải: Thẻ Form Đăng Nhập Tone Sáng */}
          <div style={{ display: 'flex', justifyContent: 'center' }}>
            <div style={{
              width: '100%',
              maxWidth: '440px',
              backgroundColor: '#ffffff',
              borderRadius: '24px',
              padding: '2.5rem',
              boxShadow: '0 20px 40px -15px rgba(15, 23, 42, 0.08), 0 0 1px 1px rgba(0, 0, 0, 0.04)',
              border: '1px solid #e2e8f0'
            }}>
              {/* Header Thẻ */}
              <div style={{ textAlign: 'center', marginBottom: '2rem' }}>
                <div style={{
                  width: '58px',
                  height: '58px',
                  borderRadius: '18px',
                  background: '#eff6ff',
                  border: '1px solid #bfdbfe',
                  color: '#2563eb',
                  display: 'inline-flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  marginBottom: '1rem',
                  boxShadow: '0 4px 12px rgba(37, 99, 235, 0.12)'
                }}>
                  <ShieldCheck size={30} />
                </div>
                <h2 style={{ fontSize: '1.375rem', fontWeight: 900, color: '#0f172a', margin: '0 0 0.35rem 0' }}>
                  ĐĂNG NHẬP HỆ THỐNG
                </h2>
                <p style={{ fontSize: '0.8125rem', color: '#64748b', margin: 0 }}>
                  Cổng Thông Tin Vận Hành Giám Sát ITS
                </p>
              </div>

              {/* Thông báo lỗi */}
              {error && (
                <div style={{
                  backgroundColor: '#fee2e2',
                  border: '1px solid #fecaca',
                  color: '#b91c1c',
                  padding: '0.75rem 1rem',
                  borderRadius: '12px',
                  fontSize: '0.8125rem',
                  display: 'flex',
                  alignItems: 'center',
                  gap: '0.5rem',
                  marginBottom: '1.25rem'
                }}>
                  <AlertCircle size={16} color="#dc2626" />
                  <span>{error}</span>
                </div>
              )}

              {/* Form Đăng Nhập */}
              <form onSubmit={handleSubmit} style={{ display: 'flex', flexDirection: 'column', gap: '1.25rem' }}>
                <div>
                  <label style={{ display: 'block', fontSize: '0.8125rem', fontWeight: 700, color: '#334155', marginBottom: '0.375rem' }}>
                    Tài Khoản Đăng Nhập
                  </label>
                  <div style={{ position: 'relative' }}>
                    <User size={18} style={{ position: 'absolute', left: '14px', top: '50%', transform: 'translateY(-50%)', color: '#94a3b8' }} />
                    <input
                      type="text"
                      value={username}
                      onChange={(e) => setUsername(e.target.value)}
                      placeholder="Nhập tên tài khoản"
                      required
                      style={{
                        width: '100%',
                        padding: '0.75rem 1rem 0.75rem 2.75rem',
                        borderRadius: '12px',
                        border: '1px solid #cbd5e1',
                        backgroundColor: '#f8fafc',
                        color: '#0f172a',
                        fontSize: '0.875rem',
                        outline: 'none',
                        transition: 'all 0.2s',
                        boxSizing: 'border-box'
                      }}
                      onFocus={(e) => {
                        e.target.style.borderColor = '#2563eb';
                        e.target.style.backgroundColor = '#ffffff';
                        e.target.style.boxShadow = '0 0 0 3px rgba(37, 99, 235, 0.12)';
                      }}
                      onBlur={(e) => {
                        e.target.style.borderColor = '#cbd5e1';
                        e.target.style.backgroundColor = '#f8fafc';
                        e.target.style.boxShadow = 'none';
                      }}
                    />
                  </div>
                </div>

                <div>
                  <label style={{ display: 'block', fontSize: '0.8125rem', fontWeight: 700, color: '#334155', marginBottom: '0.375rem' }}>
                    Mật Khẩu Xác Thực
                  </label>
                  <div style={{ position: 'relative' }}>
                    <Lock size={18} style={{ position: 'absolute', left: '14px', top: '50%', transform: 'translateY(-50%)', color: '#94a3b8' }} />
                    <input
                      type={showPassword ? 'text' : 'password'}
                      value={password}
                      onChange={(e) => setPassword(e.target.value)}
                      placeholder="Nhập mật khẩu"
                      required
                      style={{
                        width: '100%',
                        padding: '0.75rem 2.75rem 0.75rem 2.75rem',
                        borderRadius: '12px',
                        border: '1px solid #cbd5e1',
                        backgroundColor: '#f8fafc',
                        color: '#0f172a',
                        fontSize: '0.875rem',
                        outline: 'none',
                        transition: 'all 0.2s',
                        boxSizing: 'border-box'
                      }}
                      onFocus={(e) => {
                        e.target.style.borderColor = '#2563eb';
                        e.target.style.backgroundColor = '#ffffff';
                        e.target.style.boxShadow = '0 0 0 3px rgba(37, 99, 235, 0.12)';
                      }}
                      onBlur={(e) => {
                        e.target.style.borderColor = '#cbd5e1';
                        e.target.style.backgroundColor = '#f8fafc';
                        e.target.style.boxShadow = 'none';
                      }}
                    />
                    <button
                      type="button"
                      onClick={() => setShowPassword(!showPassword)}
                      style={{
                        position: 'absolute',
                        right: '12px',
                        top: '50%',
                        transform: 'translateY(-50%)',
                        background: 'none',
                        border: 'none',
                        color: '#94a3b8',
                        cursor: 'pointer',
                        padding: 0,
                        display: 'flex',
                        alignItems: 'center'
                      }}
                      title={showPassword ? 'Ẩn mật khẩu' : 'Hiện mật khẩu'}
                    >
                      {showPassword ? <EyeOff size={18} /> : <Eye size={18} />}
                    </button>
                  </div>
                </div>

                {/* Thẻ gợi ý tài khoản có nút tự động điền */}
                <div style={{
                  backgroundColor: '#f8fafc',
                  border: '1px dashed #cbd5e1',
                  borderRadius: '12px',
                  padding: '0.75rem 1rem',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'space-between',
                  gap: '0.5rem'
                }}>
                  <div style={{ fontSize: '0.75rem', color: '#475569' }}>
                    <div>🔑 <strong>Tài khoản mặc định:</strong></div>
                    <div style={{ marginTop: '0.15rem' }}>
                      <span style={{ color: '#2563eb', fontWeight: 700 }}>admin</span> / <span style={{ color: '#2563eb', fontWeight: 700 }}>admin123</span>
                    </div>
                  </div>
                  <button
                    type="button"
                    onClick={handleFillDemo}
                    style={{
                      background: '#eff6ff',
                      border: '1px solid #bfdbfe',
                      color: '#2563eb',
                      fontSize: '0.6875rem',
                      fontWeight: 700,
                      padding: '0.35rem 0.65rem',
                      borderRadius: '8px',
                      cursor: 'pointer'
                    }}
                  >
                    Tự động điền
                  </button>
                </div>

                {/* Nút bấm Submit */}
                <button
                  type="submit"
                  disabled={loading}
                  style={{
                    width: '100%',
                    padding: '0.8125rem',
                    fontSize: '0.9375rem',
                    fontWeight: 800,
                    borderRadius: '12px',
                    border: 'none',
                    background: 'linear-gradient(135deg, #2563eb 0%, #1d4ed8 100%)',
                    color: '#ffffff',
                    cursor: loading ? 'not-allowed' : 'pointer',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    gap: '0.5rem',
                    marginTop: '0.5rem',
                    boxShadow: '0 4px 14px 0 rgba(37, 99, 235, 0.3)',
                    transition: 'all 0.2s',
                    opacity: loading ? 0.7 : 1
                  }}
                  onMouseEnter={(e) => !loading && (e.currentTarget.style.transform = 'translateY(-1px)')}
                  onMouseLeave={(e) => !loading && (e.currentTarget.style.transform = 'translateY(0)')}
                >
                  <span>{loading ? 'Đang Xác Thực...' : 'Đăng Nhập Vào Hệ Thống'}</span>
                  <ArrowRight size={18} />
                </button>
              </form>

              {/* Chân thẻ bảo mật */}
              <div style={{
                textAlign: 'center',
                marginTop: '1.5rem',
                fontSize: '0.75rem',
                color: '#94a3b8'
              }}>
                🔒 Xác thực an toàn PBKDF2 HMAC-SHA256 • ITS Session Guard
              </div>
            </div>
          </div>
        </div>
      </main>
    </div>
  );
}
