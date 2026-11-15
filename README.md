# E-commerce Returns Intelligence – BigQuery Gold (Project gốc)

**Giao diện:** Giữ UI xanh navy, cam, nền pastel và 4 trang như bản theo ảnh mẫu.

**Project ID mặc định, đúng theo code gốc bạn gửi:** `data-cycle-510201-h1`  
**Dataset:** `Dataset3_Gold`  

## Luồng dữ liệu (giữ nguyên SQL từ source cũ)

```
Streamlit → Google BigQuery: data-cycle-510201-h1.Dataset3_Gold
    ├── ml_return_train
    │     → GROUP BY category, shipping, payment, device
    │     → COUNT orders, returns, 7 quality flags → Return Insights & Data Overview
    └── ml_return_test
          INNER JOIN return_risk_scores USING (order_id)
          → risk_score (đã tính trước) → Risk Alerts
```

- Chỉ `SELECT` từ BigQuery Gold, không tải CSV Offline, không tính lại điểm ML, không ghi dữ liệu.
- Giữ cache query 300 giây.
- BI lấy từ **Train có nhãn**, Alerts lấy từ **Test không có nhãn**.
- `return_risk_scores` phải có sẵn trong cùng Dataset3_Gold và `order_id` không được trùng khi JOIN.
- SHAP/Model Explanation là hình kết quả từ Task 3.6/3.7 nằm trong `assets` (không phải truy vấn BigQuery).

## Chạy trên VS Code / máy cá nhân (KHÔNG cần secrets.toml)

1. Cài Google Cloud CLI nếu máy chưa có.
2. Mở Terminal và đăng nhập:

```bash
gcloud auth application-default login
```

3. Từ thư mục dự án:

```bash
pip install -r requirements.txt
streamlit run app.py
```

4. User đăng nhập phải có quyền chạy BigQuery jobs (`BigQuery Job User`) và đọc các bảng Gold (`BigQuery Data Viewer`).
5. Nếu dataset ở vùng không tự suy ra được, đặt biến môi trường `RETURN_BQ_LOCATION` đúng với vùng thực tế (vd: `US`).

**Không cần sửa Project ID**: mặc định dùng chính xác `data-cycle-510201-h1`. Nếu bạn tự đặt biến môi trường `RETURN_BQ_PROJECT`, biến đó sẽ ghi đè ID mặc định, giống source gốc.

## Chạy bằng service account / triển khai Streamlit Cloud

Nếu muốn sử dụng đúng nhánh xác thực của source cũ, hãy tạo `.streamlit/secrets.toml` từ file `.streamlit/secrets.toml.example`, sau đó điền `[gcp_service_account]` bằng JSON của service account. **Không đưa file đó lên GitHub hoặc gửi khóa cho người khác.**

Mã đã hỗ trợ cả hai phương án:
- Có `[gcp_service_account]` → sử dụng `service_account.Credentials.from_service_account_info()`.
- Không có → sử dụng ADC qua `bigquery.Client(project=PROJECT)`.

**Lưu ý:** Chỉ khai báo `PROJECT = ...` không tự xác thực; phải đăng nhập bằng ADC hoặc cấp danh tính dịch vụ.

## Những điều đã kiểm tra

- SQL lấy dữ liệu đúng các bảng trên.
- Không còn yêu cầu bắt buộc phải có `secrets.toml` khi chạy local.
- Cú pháp Python, hàm xử lý dữ liệu và bộ lọc kiểm tra cục bộ đạt.
- **Chưa gọi BigQuery live** vì môi trường tạo file không có credential của bạn. Nếu project ID không tồn tại hoặc tài khoản không có quyền, Dashboard sẽ báo lỗi. Không tự chuyển sang project khác.
- Nút thời gian và số liệu tăng trưởng được loại khỏi UI vì dataset không có ngày đặt hàng.
