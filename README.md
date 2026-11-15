# Returns Intelligence – UI ảnh mẫu + BigQuery Gold (luồng source cũ)

**Giao diện giữ nguyên**: sidebar navy, nút cam, nền pastel xanh nhạt, bốn KPI card và biểu đồ cột xanh/cam. Chỉ thay luồng truy cập dữ liệu trở lại source ban đầu.

## Nguồn dữ liệu (không CSV, không tự tính lại điểm ML)

1. Streamlit đọc `st.secrets["gcp_service_account"]`, tạo BigQuery Client theo source ban đầu.
2. Gọi `query()` được cache bằng `st.cache_data(ttl=300)`.
3. `history_sql()` đọc trực tiếp **`{project}.Dataset3_Gold.ml_return_train`**, `GROUP BY` bốn chiều `product_category`, `shipping_method`, `payment_method`, `device_type`. SQL đếm đơn, đơn hoàn trả và các Data Quality Flags. Bổ sung đếm 7 cờ chỉ để phục vụ trang Data Overview, **không đổi ý nghĩa KPI**.
4. `alerts_sql()` giữ đúng **`ml_return_test INNER JOIN return_risk_scores ON order_id`** và truy vấn `risk_score` từ BigQuery. **Không có chế độ CSV Offline** và không có fallback đọc score local.
5. Trang Model Explanation sử dụng hình ảnh và bảng đánh giá đã lưu từ Task 3.6/3.7; không chấm điểm lại mô hình.

## Thiết lập Streamlit

1. Tải ZIP source, giải nén, vào thư mục `Returns_Intelligence_Dashboard_Reference_UI_BIGQUERY_ORIGINAL_FLOW`.
2. `pip install -r requirements.txt`
3. Copy `.streamlit/secrets.toml.example` thành `.streamlit/secrets.toml`.
4. Điền thông tin **service account thật** vào `[gcp_service_account]`; tài khoản cần có quyền đọc dataset Gold và thực thi BigQuery Jobs (`bigquery.jobUser` trên project chạy query + `dataViewer` trên dataset). Không chia sẻ key lên chat/GitHub.
5. `RETURN_BQ_PROJECT` **mặc định theo code gốc là `data-cycle-510201-h1`**. Nếu Gold của bạn thực tế ở `thermal-wonder-510201-c1`, sửa đúng Project ID. Đặt `RETURN_BQ_LOCATION` trùng vùng dataset (US hoặc asia-southeast1).
6. `streamlit run app.py`

## Khác biệt giữa source cũ và UI mới

- UI mới có 4 trang; source cũ có 2 trang. Các trang mới dùng dữ liệu thống kê từ **cùng nguồn Gold** và các artifact ML tĩnh.
- Lịch sử được tổng hợp ngay ở BigQuery như source gốc. Do đó bộ lọc là **4 chiều nguồn có sẵn**. Không tự thêm `age_group` hoặc `used_coupon` vào bộ lọc nếu chưa sửa `history_sql`.
- KPI thứ tư = `COUNTIF(flag_bad_price)` (**cờ giá bất thường**), không phải số đơn rủi ro cao.
- Không hiển thị Last 30 Days, sparkline thay đổi tháng và % tăng/giảm vì không có dữ liệu thời gian giao dịch.
- Các số hiển thị trên BI lấy từ Train có nhãn, Risk Alerts lấy từ Test không nhãn; không trộn hai nguồn thành một tỷ lệ hoàn trả.

## SQL và bảo mật

- Chỉ chạy SELECT. Không CREATE/UPDATE/DELETE.
- Không lưu khóa API / tài khoản trong ZIP.
- Nếu `return_risk_scores` không tồn tại, trang Risk Alerts báo lỗi rõ ràng; cần tạo đúng bảng theo source cũ trước khi sử dụng.
- Dữ liệu được cache trong phiên Streamlit 300 giây, có nút làm mới.

## Kiểm tra

- Đã kiểm tra Python syntax và hàm xử lý nhóm bằng dữ liệu CSV trong dự án mà không kết nối BigQuery.
- Chưa kiểm thử end-to-end với service account và BigQuery thực do không có quyền credentials trong phiên này.
- Ảnh preview là bản mô phỏng UI, không phải screenshot Streamlit chạy.
