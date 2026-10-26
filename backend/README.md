# 🚗 Traffic Vehicle Dataset (Đồ án tốt nghiệp ĐHCN Việt - Hung)

## 1. Giới thiệu bộ dữ liệu
Bộ dữ liệu hình ảnh phương tiện giao thông thực nghiệm được trích xuất trực tiếp từ camera giám sát giao thông thực tế phục vụ đồ án:
**"Xây dựng CSDL và giao diện người dùng cho ứng dụng xác định lưu lượng và ước lượng tốc độ trung bình của phương tiện giao thông sử dụng camera giám sát"**.

## 2. Danh mục phân loại phương tiện (Classes)
- **Class 0 (`car`)**: Ô tô con, xe bán tải, SUV
- **Class 1 (`motorcycle`)**: Xe máy, xe gắn máy, xe tay ga
- **Class 2 (`bus`)**: Xe buýt công cộng, xe khách
- **Class 3 (`truck`)**: Xe tải, container, xe ben

## 3. Định dạng nhãn (Annotation Format)
Chuẩn format YOLOv8: Mỗi file `.txt` tương ứng với một file `.jpg` cùng tên trong thư mục `images/`.
Cấu trúc mỗi dòng:
`<class_id> <x_center> <y_center> <width> <height>` (được chuẩn hóa trong đoạn [0, 1]).
