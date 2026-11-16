"""E-commerce Returns Intelligence — Streamlit reference-style dashboard.

Run: streamlit run app.py
Visual design follows the provided sample, while all metrics use real project data.
"""

from __future__ import annotations

from html import escape
from pathlib import Path
import os

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from charts import bars, confusion, flagged_bars, heatmap, risk_histogram, style
from google.api_core.exceptions import Forbidden, NotFound, BadRequest
from google.cloud import bigquery
from google.oauth2 import service_account
from google.auth.exceptions import DefaultCredentialsError, RefreshError
from data_access import (
    FLAG_COLUMNS, FLAG_COUNT_COLUMNS, HISTORY_COLUMNS, ALERT_COLUMNS, DIMS,
    group_stats, history_sql, alerts_sql, validate_history, validate_alerts, make_summary
)
from styles import STYLES

ROOT = Path(__file__).resolve().parent
# Giữ đúng Project ID và Dataset Gold như source gốc của nhóm.
PROJECT = os.getenv("RETURN_BQ_PROJECT", "data-cycle-510201-h1")
GOLD = f"{PROJECT}.Dataset3_Gold"
st.set_page_config(
    page_title="E-commerce Returns Intelligence",
    page_icon="🛍️", layout="wide", initial_sidebar_state="expanded",
)
st.markdown(STYLES, unsafe_allow_html=True)

st.markdown(
    """
    <style>
    /* Giữ sidebar trong chiều cao màn hình và cho phép cuộn nội dung bên trong */
    section[data-testid="stSidebar"] [data-testid="stSidebarContent"] {
        height: 100vh;
        overflow-y: auto;
        overflow-x: hidden;
        scrollbar-width: thin;
        scrollbar-color: #AAB8CC transparent;
    }

    /* Tùy chỉnh thanh cuộn trên Chrome/Edge */
    section[data-testid="stSidebar"] [data-testid="stSidebarContent"]::-webkit-scrollbar {
        width: 7px;
    }
    section[data-testid="stSidebar"] [data-testid="stSidebarContent"]::-webkit-scrollbar-track {
        background: transparent;
    }
    section[data-testid="stSidebar"] [data-testid="stSidebarContent"]::-webkit-scrollbar-thumb {
        background: #AAB8CC;
        border-radius: 10px;
    }
    section[data-testid="stSidebar"] [data-testid="stSidebarContent"]::-webkit-scrollbar-thumb:hover {
        background: #8294AE;
    }
    </style>
    """,
    unsafe_allow_html=True,
)


NAVIGATION = [
    "📊  Return Insights",
    "🔔  Risk Alerts",
    "✨  Model Explanation",
    "🗃️  Data Overview",
]
FLAG_LABELS = {
    "flag_bad_price": "Giá sản phẩm bất thường",
    "flag_bad_views": "Lượt xem sản phẩm bất thường",
    "flag_rating_out_of_range": "Rating ngoài ngưỡng",
    "flag_bad_return_rate": "Lịch sử hoàn trả bất thường",
    "flag_age_under_18": "Độ tuổi dưới 18",
    "flag_bad_discount": "Tỷ lệ giảm giá bất thường",
    "flag_bad_session": "Thời lượng phiên bất thường",
}


def number(value):
    return f"{int(value):,}".replace(",", ".")


def percentage(value, decimals=2):
    return f"{value:.{decimals}f}".replace(".", ",") + "%"


def title(text, subtitle, source):
    st.markdown(
        '<div class="page-top">'
        f'<div class="page-title">{text}</div>'
        f'<div class="page-sub">{escape(subtitle)}</div>'
        f'<span class="scope-pill">▣ &nbsp; {escape(source)}</span>'
        '</div>', unsafe_allow_html=True,
    )


def metric_card(label, value, icon, color, caption, ratio=None, watermark=None):
    extra = ""
    if ratio is not None:
        extra = f'<span class="metric-ring" style="--ratio:{min(100,max(0,ratio)):.3f}"></span>'
    elif watermark:
        extra = f'<span class="metric-watermark">{watermark}</span>'
    st.markdown(
        f'<div class="metric-card {color}">'
        f'<div class="metric-head"><span class="metric-icon">{icon}</span>{escape(label)}</div>'
        f'<div class="metric-val">{escape(str(value))}</div>'
        f'<div class="metric-caption">{escape(caption)}</div>'
        f'{extra}</div>', unsafe_allow_html=True,
    )


def chart_heading(text, icon=""):
    st.markdown(f'<div class="section-caption">{icon} {escape(text)}</div>', unsafe_allow_html=True)


def chart_subheading(text):
    st.markdown(f'<div class="section-sub">{escape(text)}</div>', unsafe_allow_html=True)


def show(fig, key=None):
    st.plotly_chart(fig, use_container_width=True,
                    config={"displayModeBar": False, "responsive": True}, key=key)


def group_chart(frame, column, measure, theme, top3=False):
    """One faithful horizontal bar chart with real values and shared tooltips."""
    grouped = group_stats(frame, column)
    if top3:
        grouped = grouped.nlargest(3, "rate" if measure == "rate" else "returns")
    grouped = grouped.sort_values(measure)
    vals = grouped[measure].to_numpy()
    labels = ([f"{x:.2f}%" for x in vals] if measure == "rate"
              else [number(x) for x in vals])
    fig = go.Figure(go.Bar(
        y=grouped[column].astype(str), x=vals, orientation="h",
        marker=dict(color=theme, line=dict(width=0)), width=.62,
        text=labels, textposition="outside", cliponaxis=False,
        textfont=dict(size=13, color="#1A2D4B", family="Arial"),
        customdata=grouped[["orders", "returns", "rate"]].to_numpy(),
        hovertemplate=(
            "<b>%{y}</b><br>Đơn hàng: %{customdata[0]:,.0f}"
            "<br>Đơn hoàn trả: %{customdata[1]:,.0f}"
            "<br>Return rate: %{customdata[2]:.2f}%<extra></extra>"
        ),
    ))
    if measure == "rate":
        upper = max(60.0, float(vals.max() + 5) if len(vals) else 60)
        fmt = ".0f"
        ticks = "%"
    else:
        upper = max(1, float(vals.max() * 1.22) if len(vals) else 1)
        fmt, ticks = ",d", ""
    fig.update_layout(
        height=268 if top3 else max(305, 49 * len(grouped) + 80),
        margin=dict(l=6, r=50, t=13, b=24),
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        font=dict(family="Arial, sans-serif", size=13, color="#20334F"),
        showlegend=False, bargap=.30,
        hoverlabel=dict(bgcolor="white", font_size=12),
    )
    fig.update_xaxes(range=[0, upper], tickformat=fmt, ticksuffix=ticks,
                     gridcolor="#E9EFF9", showline=True, linecolor="#8796AC",
                     zeroline=False, title=None)
    fig.update_yaxes(showgrid=False, title=None, tickfont=dict(size=13),
                     showline=False, automargin=True)
    return fig


def apply_filters(df, choices):
    if df is None:
        return None
    out = df
    for field, values in choices.items():
        if values and field in out:
            out = out[out[field].isin(values)]
    return out


def optional_secret(name, default=None):
    """Read optional Streamlit secrets without requiring a secrets.toml locally."""
    try:
        return st.secrets.get(name, default)
    except (FileNotFoundError, KeyError):
        return default



@st.cache_data(ttl=300, show_spinner="Đang đọc dữ liệu Gold từ BigQuery…")
def query(project, sql, expected_columns):
    """Use the user's original BigQuery queries; Cloud credentials via st.secrets.

    Service Account in Streamlit Community Cloud > Settings > Secrets is primary.
    Local ADC is retained only as a fallback when no service account is configured.
    """
    sa_info = optional_secret("gcp_service_account")
    if sa_info:
        credentials = service_account.Credentials.from_service_account_info(dict(sa_info))
        client = bigquery.Client(project=project, credentials=credentials)
    else:
        try:
            client = bigquery.Client(project=project)
        except DefaultCredentialsError as exc:
            raise RuntimeError(
                "Chưa cấu hình Google Cloud credentials cho ứng dụng. "
                "Nếu deploy lên Streamlit Community Cloud: vào Manage app → Settings "
                "→ Secrets và khai báo [gcp_service_account]. "
                "Đăng nhập gcloud trên laptop không cấp quyền cho Streamlit Cloud."
            ) from exc

    location = os.getenv("RETURN_BQ_LOCATION") or optional_secret("RETURN_BQ_LOCATION")
    if not location:
        try:
            location = client.get_dataset(f"{project}.Dataset3_Gold").location
        except Forbidden:
            # Users with table/query rights may lack dataset metadata permission.
            # Query will still run without explicitly specifying location.
            location = None
        except NotFound as exc:
            raise RuntimeError(
                f"Không tìm thấy dataset {project}.Dataset3_Gold. "
                "Kiểm tra Project ID và tên Dataset trong BigQuery."
            ) from exc

    return pd.DataFrame.from_records(
        [dict(row) for row in client.query(sql, location=location).result(timeout=90)],
        columns=list(expected_columns),
    )


def friendly_bigquery_error(exc):
    """Explain the likely failure while preserving the detailed exception for debugging."""
    if isinstance(exc, (DefaultCredentialsError, RefreshError)):
        return ("Lỗi xác thực Google Cloud.",
                "Kiểm tra [gcp_service_account] trong Settings → Secrets trên Streamlit Cloud. "
                "Private key phải đúng định dạng JSON đã tải từ Google Cloud.")
    if isinstance(exc, Forbidden):
        return ("Service Account không đủ quyền truy vấn BigQuery.",
                "Cấp roles/bigquery.jobUser trên project chạy query và "
                "roles/bigquery.dataViewer trên Dataset3_Gold (hoặc các bảng cần đọc).")
    if isinstance(exc, NotFound):
        return ("Không tìm thấy BigQuery Project/Dataset/Table.",
                "Kiểm tra data-cycle-510201-h1.Dataset3_Gold và ba bảng "
                "ml_return_train, ml_return_test, return_risk_scores.")
    if isinstance(exc, BadRequest):
        return ("BigQuery từ chối SQL hoặc cấu hình vùng dữ liệu.",
                "Kiểm tra nội dung lỗi, tên cột, trường flag_* và "
                "RETURN_BQ_LOCATION (phải đúng vị trí thực của dataset).")
    message = str(exc).lower()
    if "chưa cấu hình" in message or "credentials" in message or "private_key" in message:
        return ("Chưa thiết lập xác thực trên Streamlit Cloud.",
                "Mở Manage app → Settings → Secrets, thêm [gcp_service_account] "
                "và Save. KHÔNG tải JSON key lên GitHub.")
    return ("Không đọc được BigQuery Gold.",
            "Mở mục 'Chi tiết kỹ thuật' để biết có phải lỗi credential, SQL, bảng hoặc location.")


def get_project():
    return PROJECT


@st.cache_data(show_spinner=False)
def load_model_metrics():
    compare = ROOT / "assets" / "final_model_comparison.csv"
    confusion_file = ROOT / "assets" / "best_model_confusion_matrix.csv"
    return (pd.read_csv(compare) if compare.is_file() else None,
            pd.read_csv(confusion_file, index_col=0) if confusion_file.is_file() else None)


# -------- Sidebar --------
logo = '''<svg class="brand-bag" viewBox="0 0 72 80" xmlns="http://www.w3.org/2000/svg">
<defs><linearGradient id="bag" x1="0" x2="1" y1="0" y2="1"><stop stop-color="#FFCA81"/><stop offset="1" stop-color="#EE9336"/></linearGradient></defs>
<path d="M17 26h39l6 44q.5 5-5 5H15q-5 0-5-5z" fill="url(#bag)" />
<path d="M25 30V20C25 8 47 8 47 20v10" stroke="#FFD59C" stroke-width="5" fill="none" stroke-linecap="round"/>
<path d="m27 52 7 7 14-15" stroke="white" stroke-width="5" fill="none" stroke-linecap="round" stroke-linejoin="round"/>
</svg>'''
st.sidebar.markdown(
    f'<div class="brand-wrap">{logo}'
    '<div class="brand-name">E-commerce<br>Returns Intelligence</div>'
    '<div class="brand-line"></div></div>', unsafe_allow_html=True,
)
page = st.sidebar.radio("Điều hướng", NAVIGATION, label_visibility="collapsed", key="navigation")

# Project ID và SQL lấy từ source gốc. Khi chạy Cloud cần Secrets hoặc danh tính Google Cloud được cấu hình.
project = get_project()

with st.sidebar.expander("⚙ Nguồn dữ liệu", expanded=False):
    st.caption("Nguồn: BigQuery Gold (đúng luồng source cũ)")
    st.code(f"{project}.Dataset3_Gold", language=None)
    if st.button("Làm mới dữ liệu BigQuery", use_container_width=True):
        query.clear()
        st.rerun()

try:
    train = validate_history(query(project, history_sql(project), tuple(HISTORY_COLUMNS)))
    risks = (validate_alerts(query(project, alerts_sql(project), tuple(ALERT_COLUMNS)))
             if page == NAVIGATION[1] else None)
except Exception as exc:
    heading, hint = friendly_bigquery_error(exc)
    st.error(heading)
    st.info(hint)
    with st.expander("Chi tiết kỹ thuật (không chứa khóa bí mật)", expanded=False):
        st.code(f"{type(exc).__name__}: {str(exc)[:1400]}", language="text")
        st.caption(f"Truy vấn đến: {project}.Dataset3_Gold")
    st.stop()

dataset = {"train":train, "risks":risks,
           "source":f"BigQuery Gold · {project}.Dataset3_Gold",
           "risk_source":f"{project}.Dataset3_Gold.return_risk_scores"}

with st.sidebar.expander("🔎 Lọc theo đặc điểm đơn hàng", expanded=False):
    selected = {}
    for field, label in [
        ("product_category", "Danh mục sản phẩm"),
        ("shipping_method", "Vận chuyển"),
        ("payment_method", "Thanh toán"),
        ("device_type", "Thiết bị"),
    ]:
        if field in train.columns:
            opts = sorted(train[field].dropna().astype(str).unique().tolist())
            selected[field] = st.multiselect(label, opts, key=f"filter_{field}")
    if st.button("Xóa tất cả bộ lọc", use_container_width=True):
        for name in list(st.session_state.keys()):
            if name.startswith("filter_"):
                del st.session_state[name]
        st.rerun()

st.sidebar.markdown(
    '<div class="sidebar-motto">↗<br><b>Smarter Insights.<br>Lower Return Rate.</b></div>'
    '<div class="nav-footer">Dữ liệu từ đồ án · Không có thời gian giao dịch</div>',
    unsafe_allow_html=True,
)

filtered = apply_filters(train, selected)
filtered_risks = apply_filters(risks, selected)
summary = make_summary(filtered)
source_text = "Toàn bộ dữ liệu" if not any(selected.values()) else "Đang áp dụng bộ lọc"


# -------- Return Insights --------
if page == NAVIGATION[0]:
    title("📊 Tổng quan hoàn trả",
          "Theo dõi tình hình và khám phá những nhóm giao dịch có tỷ lệ hoàn trả cao.",
          source_text)

    c1, c2, c3, c4 = st.columns(4)
    with c1:
        metric_card("Tổng số đơn", number(summary["orders"]), "📦", "blue", "Tập Train có nhãn")
    with c2:
        metric_card("Đơn đã hoàn trả", number(summary["returns"]), "↩️", "orange", "Trạng thái hoàn trả thực tế")
    with c3:
        metric_card("Tỷ lệ hoàn trả", percentage(summary["rate"]), "%", "blue",
                    "Tổng hoàn trả / Tổng đơn", ratio=summary["rate"])
    with c4:
        price_flags = int(filtered["price_flags"].sum()) if len(filtered) else 0
        metric_card("Cờ giá bất thường", number(price_flags), "⚠️", "orange",
                    "Không phải số đơn dự đoán rủi ro", watermark="⚠")

    st.write("")
    with st.container(border=True):
        h1, h2 = st.columns([2.1, 1.5], vertical_alignment="center")
        with h1:
            st.markdown('<div class="section-title">📊 Hoàn trả theo nhóm</div>', unsafe_allow_html=True)
            chart_subheading("So sánh các nhóm theo dữ liệu thực tế")
        with h2:
            measure_label = st.radio("Chỉ số", ["Tỷ lệ hoàn trả", "Số lượng hoàn trả"],
                                     horizontal=True, label_visibility="collapsed", key="overview_measure")
        measure = "rate" if measure_label == "Tỷ lệ hoàn trả" else "returns"
        st.write("")
        if filtered.empty:
            st.info("Không có đơn phù hợp với các bộ lọc đang chọn.")
        else:
            a, b = st.columns(2)
            with a:
                chart_heading("Danh mục sản phẩm", "📦")
                show(group_chart(filtered, "product_category", measure, "#4D93EE", top3=True),
                     key="chart_top_categories")
            with b:
                chart_heading("Phương thức vận chuyển", "🚚")
                show(group_chart(filtered, "shipping_method", measure, "#FFAD51", top3=True),
                     key="chart_top_shipping")
            show_full = st.checkbox("Xem toàn bộ danh mục và nhóm vận chuyển", value=False)
            if show_full:
                a, b = st.columns(2)
                with a:
                    show(group_chart(filtered, "product_category", measure, "#4D93EE", top3=False),
                         key="chart_all_categories")
                with b:
                    show(group_chart(filtered, "shipping_method", measure, "#FFAD51", top3=False),
                         key="chart_all_shipping")
    st.markdown(
        '<div class="small-explainer">'
        'Chỉ số được tính trên đơn Train có nhãn. Bộ dữ liệu không có thời gian giao dịch, '
        'vì vậy không hiển thị tăng trưởng 30 ngày hoặc biểu đồ xu hướng giả định.'
        '</div>', unsafe_allow_html=True,
    )

# -------- Risk Alerts --------
elif page == NAVIGATION[1]:
    title("🔔 Cảnh báo rủi ro hoàn trả",
          "Xếp hạng các đơn Test chưa có nhãn dựa trên điểm dự đoán của XGBoost Tuned.",
          "Test · Risk Scores")
    if filtered_risks is None or filtered_risks.empty:
        st.warning("Không có điểm rủi ro hoặc không có đơn phù hợp bộ lọc.")
        st.stop()

    with st.container(border=True):
        u, v, w = st.columns([1.5, 1.1, 1.0])
        with u:
            threshold = st.slider("Ngưỡng rủi ro minh họa", 0.30, 0.85, 0.60, 0.01)
        with v:
            top_n = st.selectbox("Số đơn hiển thị", [10, 25, 50, 100, 200, 500], index=2)
        with w:
            only_high = st.toggle("Chỉ hiện đơn ≥ ngưỡng", True)
    total_risk = len(filtered_risks)
    high_risk = int(filtered_risks["risk_score"].ge(threshold).sum())
    a, b, c, d = st.columns(4)
    with a:
        metric_card("Đơn đã chấm điểm", number(total_risk), "📦", "blue", "Test chưa có nhãn")
    with b:
        metric_card("Đơn ≥ ngưỡng", number(high_risk), "⚠️", "orange", f"Ngưỡng {threshold:.2f}")
    with c:
        metric_card("Điểm trung bình", percentage(filtered_risks.risk_score.mean() * 100),
                    "%", "blue", "Không phải Return Rate")
    with d:
        metric_card("Điểm cao nhất", percentage(filtered_risks.risk_score.max() * 100),
                    "🔔", "orange", "Giá trị trong phạm vi lọc")

    st.write("")
    with st.container(border=True):
        st.markdown('<div class="section-title">Phân phối và mức độ rủi ro</div>', unsafe_allow_html=True)
        a, b = st.columns([1.2, 1])
        with a:
            chart_heading("Phân phối điểm dự đoán")
            show(risk_histogram(filtered_risks, threshold))
        with b:
            chart_heading("Điểm dự đoán trung bình theo danh mục")
            groups = filtered_risks.groupby("product_category", observed=True, dropna=False).risk_score.agg(["mean", "size"]).reset_index().sort_values("mean")
            fig = go.Figure(go.Bar(y=groups.product_category,
                                   x=groups["mean"] * 100, orientation="h",
                                   marker_color="#4D93EE", text=[percentage(x*100) for x in groups["mean"]],
                                   textposition="outside", cliponaxis=False))
            style(fig, 340)
            fig.update_layout(xaxis_title="Điểm dự đoán trung bình (%)", yaxis_title="")
            fig.update_xaxes(range=[0, max(60, float(groups["mean"].max() * 120))])
            show(fig)

    with st.container(border=True):
        st.markdown('<div class="section-title">Danh sách đơn ưu tiên rà soát</div>', unsafe_allow_html=True)
        searched = st.text_input("Tra cứu mã đơn", placeholder="Nhập chính xác order_id")
        ranked = filtered_risks.copy()
        if searched.strip():
            ranked = ranked[ranked.order_id.astype(str) == searched.strip()]
        elif only_high:
            ranked = ranked[ranked.risk_score.ge(threshold)]
        ranked = ranked.sort_values("risk_score", ascending=False).head(top_n).copy()
        if ranked.empty:
            st.info("Không có đơn phù hợp. Hãy chỉnh ngưỡng hoặc bộ lọc.")
        else:
            ranked["risk_pct"] = (ranked.risk_score * 100).round(2)
            fields = [col for col in ["order_id", "risk_pct", "product_category", "shipping_method", "payment_method", "device_type", "used_coupon"] if col in ranked.columns]
            shown = ranked[fields].rename(columns={"order_id":"Order ID", "risk_pct":"Risk Score (%)",
                    "product_category":"Danh mục", "shipping_method":"Vận chuyển", "payment_method":"Thanh toán",
                    "device_type":"Thiết bị", "used_coupon":"Coupon"})
            st.dataframe(shown, use_container_width=True, hide_index=True,
                         column_config={"Risk Score (%)": st.column_config.ProgressColumn(
                             "Risk Score (%)", min_value=0, max_value=100, format="%.2f%%")})
            st.download_button("Tải danh sách CSV", shown.to_csv(index=False).encode("utf-8-sig"),
                               file_name="return_risk_alerts.csv", mime="text/csv")
    st.warning("Ngưỡng 0,60 chỉ phục vụ thử nghiệm. Mô hình có ROC-AUC ≈ 0,60; không dùng điểm này để tự động từ chối đơn.")
    st.caption(f"Nguồn điểm: {dataset['risk_source']}")

# -------- Model Explanation --------
elif page == NAVIGATION[2]:
    title("✨ Giải thích mô hình dự đoán",
          "Mô tả những đặc trưng XGBoost Tuned sử dụng để tạo ra điểm rủi ro hoàn trả.",
          "SHAP · Validation 40.000 đơn")
    results, _ = load_model_metrics()
    a, b, c = st.columns(3)
    with a:
        metric_card("Mô hình", "XGBoost Tuned", "🧠", "blue", "Chọn theo ROC-AUC")
    with b:
        metric_card("ROC-AUC", "0,5997", "📈", "orange", "Tập Validation")
    with c:
        metric_card("Dữ liệu giải thích", "40.000", "📋", "blue", "Quan sát Validation")
    st.write("")
    with st.container(border=True):
        st.markdown('<div class="section-title">Global SHAP</div>', unsafe_allow_html=True)
        a, b = st.columns([1, 1])
        with a:
            chart_heading("Grouped Feature Importance")
            file = ROOT / "assets" / "shap_grouped.png"
            if file.is_file():
                st.image(str(file), use_container_width=True)
            else:
                st.info("Chưa có ảnh Grouped SHAP. Bổ sung file assets/shap_grouped.png.")
        with b:
            chart_heading("Beeswarm Plot")
            file = ROOT / "assets" / "shap_beeswarm.png"
            if file.is_file():
                st.image(str(file), use_container_width=True)
            else:
                st.info("Chưa có ảnh Beeswarm. Bổ sung file assets/shap_beeswarm.png.")
    with st.container(border=True):
        st.markdown('<div class="section-title">Local SHAP – ví dụ một dự đoán</div>', unsafe_allow_html=True)
        a, b = st.columns([1, 1.25])
        with a:
            st.metric("Xác suất hoàn trả dự đoán", "74,03%")
            st.write("Nhãn thực tế trong Validation: **Có hoàn trả (1)**")
            st.markdown("**Đóng góp nổi bật trên thang log-odds:**")
            st.markdown("- Not Standard Shipping: **+0,1920**\n- Clothing: **+0,1822**\n- Past Purchase Count: **+0,1528**\n- Used Coupon: **+0,1002**")
        with b:
            file = ROOT / "assets" / "shap_waterfall.png"
            if file.is_file():
                st.image(str(file), use_container_width=True)
            else:
                st.info("Chưa có Waterfall. Bổ sung assets/shap_waterfall.png.")
    st.info("SHAP giải thích đóng góp vào dự đoán của mô hình; không chứng minh nguyên nhân thực tế gây hoàn trả.")

# -------- Data Overview --------
else:
    title("🗃️ Tổng quan dữ liệu & chất lượng",
          "Đối soát dữ liệu Silver/Gold và theo dõi các kết quả đánh giá mô hình.",
          "Data Quality · Model Validation")
    a, b, c, d = st.columns(4)
    with a:
        metric_card("Đơn Train có nhãn", number(summary["orders"]), "📦", "blue", "Theo bộ lọc")
    with b:
        metric_card("Đơn có cờ bất thường", number(summary["flagged"]), "⚠️", "orange",
                    percentage(summary["flagged_pct"]) + " đơn đang lọc")
    with c:
        metric_card("Số quy tắc cờ", "7", "📋", "blue", "Silver Data Quality")
    with d:
        metric_card("Kiểm thử dbt", "45 / 45", "✅", "orange", "Theo log đồ án")

    st.write("")
    with st.container(border=True):
        st.markdown('<div class="section-title">Các nhóm dữ liệu bất thường</div>', unsafe_allow_html=True)
        if len(filtered):
            show(flagged_bars(filtered, FLAG_COLUMNS, FLAG_LABELS))
        else:
            st.info("Không có dữ liệu phù hợp bộ lọc.")
        st.caption("Cờ Silver phản ánh điều kiện kiểm tra đã khai báo, không tự chứng minh mọi trường hợp đều là lỗi nghiệp vụ.")
    with st.container(border=True):
        st.markdown('<div class="section-title">Đánh giá mô hình trên Validation</div>', unsafe_allow_html=True)
        results, cm = load_model_metrics()
        if results is None:
            st.warning("Thiếu file assets/final_model_comparison.csv.")
        else:
            vals = results.sort_values("ROC_AUC")
            fig = go.Figure(go.Bar(y=vals.Model, x=vals.ROC_AUC, orientation="h",
                                   marker_color=["#FFAD51" if x == "XGBoost Tuned" else "#4D93EE" for x in vals.Model],
                                   text=[f"{v:.4f}" for v in vals.ROC_AUC], textposition="outside", cliponaxis=False))
            style(fig, 385)
            fig.update_layout(xaxis_title="ROC-AUC", yaxis_title="")
            fig.update_xaxes(range=[0.45, 0.65])
            show(fig)
            a, b = st.columns(2)
            with a:
                chart_heading("Confusion Matrix – XGBoost Tuned")
                if cm is not None:
                    show(confusion(cm))
            with b:
                chart_heading("ROC Curve – Final Models")
                path = ROOT / "assets" / "roc_curve_final.png"
                if path.is_file():
                    st.image(str(path), use_container_width=True)
            with st.expander("Bảng kết quả đầy đủ"):
                st.dataframe(results, hide_index=True, use_container_width=True)
    st.caption("Không có ngày đặt hàng nên không hiển thị Last 30 Days hoặc xu hướng tháng/năm. PASS 45/45 là kết quả các kiểm thử đã khai báo.")

st.markdown(
    '<div class="small-explainer">E-commerce Returns Intelligence · '
    'BI dùng thống kê nhóm từ ml_return_train, Risk Alerts dùng ml_return_test kết hợp return_risk_scores. '
    'Các chỉ số trong Dashboard được tính từ dữ liệu thực.</div>',
    unsafe_allow_html=True,
)
