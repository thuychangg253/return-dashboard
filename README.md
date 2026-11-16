# Dashboard – Bản sửa dành cho Streamlit Community Cloud

Luồng dữ liệu và Project ID **giữ nguyên source gốc**:

- `data-cycle-510201-h1.Dataset3_Gold.ml_return_train` → Return Insights và Data Overview.
- `data-cycle-510201-h1.Dataset3_Gold.ml_return_test` INNER JOIN `return_risk_scores` theo `order_id` → Risk Alerts.
- Ảnh SHAP và ML từ `assets/`, không gọi lại model hoặc sinh điểm giả.

## 1. Deploy

Upload `app.py`, `charts.py`, `data_access.py`, `styles.py`, `requirements.txt`, `.streamlit/config.toml`, `assets/` lên GitHub; **không upload file chứa credential**. Deploy repo trong https://share.streamlit.io/.

## 2. Secrets trên Streamlit Cloud

Trong trình quản lý ứng dụng: **Manage app → Settings → Secrets**. Dán TOML có format như `.streamlit/secrets.toml.example` (nhưng bằng thông tin JSON key của service account THẬT). Không đưa JSON key vào source code hoặc repo. Chọn Save và reboot ứng dụng nếu chưa cập nhật.

Lưu ý: `PROJECT ID` là project chứa Gold và nơi chạy query, mặc định `data-cycle-510201-h1`. Project của service account trong JSON **có thể khác**. Điều kiện là service account được cấp quyền truy vấn project này.

Quyền cần cấp cho EMAIL của Service Account:
- `BigQuery Job User` trên project `data-cycle-510201-h1` để tạo query job.
- `BigQuery Data Viewer` trên dataset `Dataset3_Gold` (hoặc từng bảng cần đọc).

## 3. Không cần gcloud auth trên laptop

Lệnh `gcloud auth application-default login` không truyền thông tin xác thực sang Streamlit Community Cloud. Local ADC chỉ dùng nếu chạy Streamlit trên máy cá nhân.

## 4. Sau khi deploy

- Vào trang **Return Insights**, kiểm tra 200.000 đơn, 94.919 hoàn trả, 47,46% khi chưa áp bộ lọc.
- Vào **Risk Alerts** để kiểm tra `return_risk_scores` đã tồn tại trong cùng Dataset3_Gold.
- Nếu lỗi, mở **Chi tiết kỹ thuật**. Mã lỗi 403 → quyền; 404 → dataset/bảng; 400 → SQL/vùng dữ liệu; `DefaultCredentialsError` → Secrets.
- Đừng gửi private key hoặc file JSON key trong tin nhắn / ảnh chụp lỗi.

## 5. Lỗi UI chồng chữ

Đã bỏ selector CSS quá rộng `html,body,[class*="st-"]` để không đè lên font biểu tượng của Streamlit. Giao diện navy/cam và các biểu đồ giữ nguyên.

**Giới hạn:** Không thể xác nhận kết nối BigQuery live từ môi trường xây dựng vì không có credential truy cập tài khoản của bạn.
