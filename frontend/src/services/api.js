const API_BASE = '/api';

const getHeaders = (extraHeaders = {}) => {
  const token = localStorage.getItem('traffic_auth_token');
  const headers = { ...extraHeaders };
  if (token) {
    headers['Authorization'] = `Bearer ${token}`;
  }
  return headers;
};

export const api = {
  // Authentication
  async login(username, password) {
    const res = await fetch(`${API_BASE}/auth/login`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ username, password })
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.detail || 'Tên đăng nhập hoặc mật khẩu không đúng');
    }
    const data = await res.json();
    if (data.token) {
      localStorage.setItem('traffic_auth_token', data.token);
      localStorage.setItem('traffic_auth_user', JSON.stringify(data.user));
    }
    return data;
  },

  async register(payload) {
    const res = await fetch(`${API_BASE}/auth/register`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.detail || 'Lỗi khi đăng ký tài khoản');
    }
    return res.json();
  },

  async getMe() {
    const token = localStorage.getItem('traffic_auth_token');
    if (!token) return null;
    try {
      const res = await fetch(`${API_BASE}/auth/me`, {
        headers: getHeaders()
      });
      if (!res.ok) {
        localStorage.removeItem('traffic_auth_token');
        localStorage.removeItem('traffic_auth_user');
        return null;
      }
      return res.json();
    } catch {
      return null;
    }
  },

  logout() {
    localStorage.removeItem('traffic_auth_token');
    localStorage.removeItem('traffic_auth_user');
  },

  getStoredUser() {
    try {
      const u = localStorage.getItem('traffic_auth_user');
      return u ? JSON.parse(u) : null;
    } catch {
      return null;
    }
  },

  // Sessions
  async getSessions() {
    const res = await fetch(`${API_BASE}/sessions`, { headers: getHeaders() });
    if (!res.ok) throw new Error('Không thể tải danh sách phiên');
    return res.json();
  },

  async createSession(payload) {
    const res = await fetch(`${API_BASE}/sessions`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    });
    if (!res.ok) throw new Error('Lỗi khi tạo phiên mới');
    return res.json();
  },

  async getSession(id) {
    const res = await fetch(`${API_BASE}/sessions/${id}`);
    if (!res.ok) throw new Error('Không tìm thấy phiên giám sát');
    return res.json();
  },

  async updateConfig(id, config) {
    const res = await fetch(`${API_BASE}/sessions/${id}/config`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ config })
    });
    if (!res.ok) throw new Error('Lỗi khi cập nhật cấu hình ROI');
    return res.json();
  },

  async startSession(id) {
    const res = await fetch(`${API_BASE}/sessions/${id}/start`, {
      method: 'POST'
    });
    if (!res.ok) throw new Error('Lỗi khi khởi chạy phiên');
    return res.json();
  },

  async stopSession(id) {
    const res = await fetch(`${API_BASE}/sessions/${id}/stop`, {
      method: 'POST'
    });
    if (!res.ok) throw new Error('Lỗi khi dừng phiên');
    return res.json();
  },

  async deleteSession(id) {
    const res = await fetch(`${API_BASE}/sessions/${id}`, {
      method: 'DELETE'
    });
    if (!res.ok) throw new Error('Lỗi khi xóa phiên');
    return res.json();
  },

  // Stats & Crossings
  async getSummary(id) {
    const res = await fetch(`${API_BASE}/sessions/${id}/summary`);
    if (!res.ok) throw new Error('Lỗi khi lấy tóm tắt KPI');
    return res.json();
  },

  async getStats(id) {
    const res = await fetch(`${API_BASE}/sessions/${id}/stats`);
    if (!res.ok) throw new Error('Lỗi khi lấy dữ liệu biểu đồ');
    return res.json();
  },

  async getCrossings(id, limit = 30) {
    const res = await fetch(`${API_BASE}/sessions/${id}/crossings?limit=${limit}`);
    if (!res.ok) throw new Error('Lỗi khi lấy danh sách xe qua vạch');
    return res.json();
  },

  async getLiveCounts(id) {
    const res = await fetch(`${API_BASE}/sessions/${id}/live-counts`);
    if (!res.ok) throw new Error('Lỗi khi lấy số đếm live');
    return res.json();
  },

  // URL Helper
  getStreamUrl(id) {
    return `${API_BASE}/stream/${id}`;
  },

  getSnapshotUrl(id) {
    return `${API_BASE}/stream/${id}/snapshot?t=${Date.now()}`;
  },

  // Video Sources (Cloud URLs & Presets)
  async getVideoSources() {
    const res = await fetch(`${API_BASE}/videos`);
    if (!res.ok) throw new Error('Không thể tải danh sách nguồn video');
    return res.json();
  },

  async addVideoSource(payload) {
    const res = await fetch(`${API_BASE}/videos`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    });
    if (!res.ok) throw new Error('Lỗi khi lưu link video vào CSDL');
    return res.json();
  },

  async deleteVideoSource(id) {
    const res = await fetch(`${API_BASE}/videos/${id}`, {
      method: 'DELETE'
    });
    if (!res.ok) throw new Error('Lỗi khi xóa nguồn video');
    return res.json();
  },

  // Dataset Auto-labeling & Frame Extraction
  async captureLiveSample(sessionId) {
    const res = await fetch(`${API_BASE}/dataset/capture-live/${sessionId}`, {
      method: 'POST'
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.detail || 'Lỗi khi chụp và gán nhãn khung hình');
    }
    return res.json();
  },

  async autoExtractBatch(sessionId, count = 50) {
    const res = await fetch(`${API_BASE}/dataset/auto-extract/${sessionId}?count=${count}`, {
      method: 'POST'
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.detail || 'Lỗi khi trích xuất dữ liệu hàng loạt');
    }
    return res.json();
  },

  async getDatasetSummary() {
    const res = await fetch(`${API_BASE}/dataset/summary`);
    if (!res.ok) throw new Error('Lỗi khi lấy thông tin bộ dữ liệu');
    return res.json();
  },

  async getDatasetSamples(limit = 30) {
    const res = await fetch(`${API_BASE}/dataset/samples?limit=${limit}`);
    if (!res.ok) throw new Error('Lỗi khi lấy danh sách mẫu đã chụp');
    return res.json();
  },

  async getCloudinaryStatus() {
    const res = await fetch(`${API_BASE}/dataset/cloudinary-status`);
    if (!res.ok) throw new Error('Lỗi khi kiểm tra trạng thái Cloudinary');
    return res.json();
  },

  async configureCloudinary(payload) {
    const res = await fetch(`${API_BASE}/dataset/configure-cloudinary`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    });
    if (!res.ok) throw new Error('Lỗi khi lưu cấu hình Cloudinary');
    return res.json();
  },

  // Violations & Evidence
  async getViolations(sessionId = null, limit = 50, offset = 0) {
    const url = sessionId 
      ? `${API_BASE}/violations?session_id=${sessionId}&limit=${limit}&offset=${offset}`
      : `${API_BASE}/violations?limit=${limit}&offset=${offset}`;
    const res = await fetch(url);
    if (!res.ok) throw new Error('Không thể tải danh sách vi phạm');
    return res.json();
  },

  async getViolationsSummary(sessionId = null) {
    const url = sessionId
      ? `${API_BASE}/violations/summary?session_id=${sessionId}`
      : `${API_BASE}/violations/summary`;
    const res = await fetch(url);
    if (!res.ok) throw new Error('Không thể tải thống kê vi phạm');
    return res.json();
  },

  async updateSpeedLimit(sessionId, speedLimit) {
    const res = await fetch(`${API_BASE}/violations/session/${sessionId}/speed-limit?speed_limit=${speedLimit}`, {
      method: 'POST'
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.detail || 'Lỗi khi cập nhật giới hạn tốc độ');
    }
    return res.json();
  },

  async deleteViolation(id) {
    const res = await fetch(`${API_BASE}/violations/${id}`, {
      method: 'DELETE'
    });
    if (!res.ok) throw new Error('Lỗi khi xóa bản ghi vi phạm');
    return res.json();
  },

  getExportCsvUrl(sessionId) {
    return `${API_BASE}/sessions/${sessionId}/export/csv`;
  },

  getExportViolationsCsvUrl(sessionId) {
    return `${API_BASE}/sessions/${sessionId}/export/violations-csv`;
  }
};



