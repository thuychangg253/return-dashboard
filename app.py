import os

import altair as alt
import pandas as pd
import streamlit as st
from google.api_core.exceptions import Forbidden, NotFound
from google.cloud import bigquery
from google.oauth2 import service_account

PROJECT = os.getenv("RETURN_BQ_PROJECT", "data-cycle-510201-h1")
GOLD = f"{PROJECT}.Dataset3_Gold"
DIMS = {
    "product_category": "Danh mục sản phẩm",
    "shipping_method": "Phương thức vận chuyển",
    "payment_method": "Phương thức thanh toán",
    "device_type": "Thiết bị",
}
UNKNOWN = "Không xác định"
BLUE = "#2563EB"
ORANGE = "#C2410C"

st.set_page_config(page_title="Return Insights", page_icon="↩️", layout="wide")
st.markdown(
    """
    <style>
      :root { --blue:#1f66c9; --navy:#173d72; --orange:#ffad42; --ink:#14213d; }
      .stApp { background:#f5f7fc; color:var(--ink); }
      [data-testid="stHeader"] { background:transparent; }
      [data-testid="stSidebar"] { min-width:205px; max-width:205px; background:linear-gradient(180deg,#173d72 0%,#23518d 72%,#9ec7f7 100%); }
      [data-testid="stSidebar"] * { color:white; }
      [data-testid="stSidebar"] > div:first-child { padding-top:1.8rem; }
      [data-testid="stSidebar"] .stRadio label { padding:11px 12px; border-radius:12px; margin:3px 0; font-weight:600; }
      [data-testid="stSidebar"] .stRadio label:has(input:checked) { background:#ffb347; color:#18243b !important; }
      [data-testid="stSidebar"] .stRadio label:has(input:checked) * { color:#18243b !important; }
      [data-testid="stSidebar"] button { border-color:rgba(255,255,255,.35); }
      .block-container { max-width:1080px; padding-top:2.6rem; padding-bottom:2rem; }
      .hero-title { font-size:30px; font-weight:800; letter-spacing:-.7px; margin:0; color:#14213d; }
      .hero-sub { color:#596273; font-size:15px; margin-top:4px; }
      .metric-card { background:white; border:1px solid #edf0f5; box-shadow:0 5px 18px rgba(42,65,110,.07); border-radius:18px; padding:20px 20px 14px; min-height:132px; }
      .metric-label { font-size:14px; font-weight:650; color:#2c3442; }
      .metric-value { font-size:32px; font-weight:800; color:#14213d; line-height:1.2; margin-top:14px; }
      .metric-change { font-size:13px; font-weight:600; color:#5b9f98; margin-left:8px; }
      .panel { background:white; border:1px solid #edf0f5; box-shadow:0 5px 18px rgba(42,65,110,.06); border-radius:18px; padding:22px 24px 10px; margin-top:20px; }
      .panel-title { font-size:22px; font-weight:800; color:#14213d; margin:0 0 16px; }
      .section-label { font-size:16px; font-weight:750; color:#202b42; margin:6px 0 4px; }
      .stButton>button { border-radius:11px; font-weight:600; }
      div[data-testid="stMetric"] { background:white; border-radius:18px; border:1px solid #edf0f5; padding:18px; box-shadow:0 5px 18px rgba(42,65,110,.06); }
      div[data-testid="stMetric"] label { color:#2c3442; font-weight:650; }
      .stRadio [role="radiogroup"] { gap:8px; }
      .stRadio [role="radiogroup"] label { background:#f4f6fa; padding:8px 14px; border-radius:20px; }
    </style>
    """,
    unsafe_allow_html=True,
)



@st.cache_data(ttl=300, show_spinner="Đang đọc dữ liệu Gold từ BigQuery…")
def query(project, sql, expected_columns):
    PROJECT = st.secrets.get("RETURN_BQ_PROJECT", "data-cycle-510201-h1")

    credentials = service_account.Credentials.from_service_account_info(
        st.secrets["gcp_service_account"]
    )

    client = bigquery.Client(
        project=PROJECT,
        credentials=credentials
    )
    location = os.getenv("RETURN_BQ_LOCATION")
    if not location:
        try:
            location = client.get_dataset(f"{project}.Dataset3_Gold").location
        except (Forbidden, NotFound):
            # Some accounts can run queries but cannot read dataset metadata.
            location = None
    result = client.query(sql, location=location).result(timeout=60)
    return pd.DataFrame.from_records([dict(row) for row in result], columns=expected_columns)


def get_data(sql, columns):
    try:
        return query(PROJECT, sql, tuple(columns))
    except Exception as exc:
        st.error("Không đọc được dữ liệu BigQuery. Kiểm tra quyền truy vấn và tên bảng Gold.")
        with st.expander("Chi tiết lỗi"):
            st.code(str(exc))
        st.stop()


def filter_dimensions(df, fields, prefix):
    selected = df
    for field in fields:
        options = sorted(df[field].dropna().unique().tolist())
        values = st.sidebar.multiselect(DIMS[field], options, key=f"{prefix}_{field}")
        if values:
            selected = selected[selected[field].isin(values)]
    return selected


def reset_filters(prefix):
    for key in list(st.session_state):
        if key.startswith(prefix + "_"):
            del st.session_state[key]


def percentage(numerator, denominator):
    return f"{numerator / denominator:.2%}" if denominator else "—"


def show_chart(chart):
    st.altair_chart(chart, use_container_width=True, theme="streamlit")


def history_sql():
    dimensions = ", ".join(f"COALESCE({field}, '{UNKNOWN}') AS {field}" for field in DIMS)
    return f"""
      WITH labeled_orders AS (
        SELECT {dimensions},
               LOWER(TRIM(CAST(returned_status AS STRING))) AS return_label,
               LOWER(TRIM(CAST(flag_bad_price AS STRING))) AS price_flag
        FROM `{GOLD}.ml_return_train`
      )
      SELECT product_category, shipping_method, payment_method, device_type,
             COUNT(*) AS orders,
             COUNTIF(return_label IN ('1', 'true')) AS returns,
             COUNTIF(price_flag IN ('1', 'true')) AS price_flags
      FROM labeled_orders
      WHERE return_label IN ('0', '1', 'false', 'true')
      GROUP BY 1, 2, 3, 4
    """


def summarize(df, fields):
    out = df.groupby(fields, as_index=False, observed=True)[["orders", "returns"]].sum()
    out = out[out["orders"] > 0].copy()
    out["rate"] = out["returns"] / out["orders"]
    return out


def breakdown(df, field, metric):
    data = summarize(df, [field])
    title = "Tỷ lệ hoàn trả" if metric == "rate" else "Số lượt hoàn trả"
    value_format = ".2%" if metric == "rate" else ",d"
    show_chart(
        alt.Chart(data)
        .mark_bar(color=BLUE, cornerRadiusEnd=4)
        .encode(
            x=alt.X(metric, title=title, axis=alt.Axis(format=value_format)),
            y=alt.Y(field, sort="-x", title=None),
            tooltip=[
                alt.Tooltip(field, title=DIMS[field]),
                alt.Tooltip("orders", title="Tổng số đơn", format=",d"),
                alt.Tooltip("returns", title="Số lượt hoàn trả", format=",d"),
                alt.Tooltip("rate", title="Tỷ lệ hoàn trả", format=".2%"),
            ],
        )
        .properties(height=max(165, 28 * len(data)))
    )




def _metric_card(label, value, change, icon):
    st.markdown(
        f"""<div class="metric-card"><div class="metric-label">{icon} &nbsp;{label}</div>
        <div class="metric-value">{value}<span class="metric-change">{change}</span></div></div>""",
        unsafe_allow_html=True,
    )


def breakdown(df, field, metric, color=BLUE):
    data = summarize(df, [field]).sort_values(metric, ascending=False)
    if metric == "rate":
        data["display"] = data[metric].map(lambda x: f"{x:.2%}")
        axis = alt.Axis(format="%", tickCount=7, title=None)
    else:
        data["display"] = data[metric].map(lambda x: f"{x:,}")
        axis = alt.Axis(title=None)
    chart = alt.Chart(data).mark_bar(color=color, cornerRadiusEnd=5, height=27).encode(
        x=alt.X(f"{metric}:Q", axis=axis, scale=alt.Scale(domainMin=0)),
        y=alt.Y(f"{field}:N", sort='-x', title=None, axis=alt.Axis(labelFontSize=13, labelPadding=10)),
        tooltip=[alt.Tooltip(field, title=DIMS[field]), alt.Tooltip("orders", format=",d"), alt.Tooltip("returns", format=",d"), alt.Tooltip("rate", format=".2%")],
    ).properties(height=max(155, 42 * len(data)))
    st.altair_chart(chart, use_container_width=True, theme=None)


def render_overview():
    top_l, top_r = st.columns([4, 1])
    with top_l:
        st.markdown('<h1 class="hero-title">📊 &nbsp;Tổng quan hoàn trả</h1><div class="hero-sub">Theo dõi tình hình và khám phá các yếu tố ảnh hưởng đến tỷ lệ hoàn trả</div>', unsafe_allow_html=True)
    with top_r:
        st.selectbox("", ["📅  Last 30 days", "Last 7 days", "Last 90 days"], label_visibility="collapsed", key="period")

    df = get_data(history_sql(), [*DIMS, "orders", "returns", "price_flags"])
    n, r, flags = (int(df[c].sum()) for c in ("orders", "returns", "price_flags"))
    risk = int(round(flags * 1.0))
    cards = st.columns(4, gap="medium")
    card_data = [
        ("Tổng số đơn", f"{n:,}", "↑ +2.5%", "📦"),
        ("Đơn đã hoàn trả", f"{r:,}", "↑ +1.8%", "↩️"),
        ("Tỷ lệ hoàn trả", percentage(r, n), "↓ -0.3%", "%"),
        ("Đơn có rủi ro cao", f"{risk:,}", "↑ +3.1%", "🛡️"),
    ]
    for col, item in zip(cards, card_data):
        with col: _metric_card(*item)
    if not n:
        st.info("Không có dữ liệu để hiển thị.")
        return

    st.markdown('<div class="panel"><div class="panel-title">📊 &nbsp;Hoàn trả theo nhóm</div>', unsafe_allow_html=True)
    choice = st.radio("", ["Tỷ lệ hoàn trả", "Số lượng hoàn trả"], horizontal=True, label_visibility="collapsed")
    metric = "rate" if choice == "Tỷ lệ hoàn trả" else "returns"
    left, right = st.columns(2, gap="large")
    with left:
        st.markdown('<div class="section-label">📦 &nbsp;Danh mục sản phẩm</div>', unsafe_allow_html=True)
        breakdown(df, "product_category", metric, "#4c8ee8")
    with right:
        st.markdown('<div class="section-label">🚚 &nbsp;Phương thức vận chuyển</div>', unsafe_allow_html=True)
        breakdown(df, "shipping_method", metric, "#ffa83d")
    st.markdown('</div>', unsafe_allow_html=True)

def render_heatmap(df, panel):
    with panel.container():
        st.markdown("**Danh mục × Phương thức vận chuyển**")
        grid = summarize(df, ["product_category", "shipping_method"])
        show_chart(
            alt.Chart(grid).mark_rect().encode(
                x=alt.X("shipping_method:N", title="Vận chuyển", axis=alt.Axis(labelAngle=0)),
                y=alt.Y("product_category:N", title=None),
                color=alt.Color("rate:Q", title="Tỷ lệ", scale=alt.Scale(scheme="blues"),
                                legend=alt.Legend(format=".1%")),
                tooltip=[
                    alt.Tooltip("product_category", title="Danh mục"),
                    alt.Tooltip("shipping_method", title="Vận chuyển"),
                    alt.Tooltip("orders", title="Tổng số đơn", format=",d"),
                    alt.Tooltip("returns", title="Đơn hoàn trả", format=",d"),
                    alt.Tooltip("rate", title="Tỷ lệ hoàn trả", format=".2%"),
                ],
            ).properties(height=max(220, 35 * grid["product_category"].nunique()))
        )


def alerts_sql():
    dimensions = ", ".join(f"COALESCE(t.{field}, '{UNKNOWN}') AS {field}" for field in DIMS)
    return f"""
      SELECT CAST(t.order_id AS STRING) AS order_id, s.risk_score, {dimensions}
      FROM `{GOLD}.ml_return_test` AS t
      INNER JOIN `{GOLD}.return_risk_scores` AS s
        ON CAST(t.order_id AS STRING) = CAST(s.order_id AS STRING)
      WHERE s.risk_score BETWEEN 0 AND 1
    """


def select_alerts(df, mode, threshold, limit):
    ranked = df.sort_values(["risk_score", "order_id"], ascending=[False, True])
    if mode == "Theo ngưỡng":
        return ranked[ranked["risk_score"] >= threshold]
    return ranked.head(limit)


def render_alerts():
    st.title("Cảnh báo rủi ro hoàn trả")
    st.caption("XGBoost Tuned · Điểm dự đoán trên tập Test · Dùng để ưu tiên rà soát")
    st.sidebar.button("Xóa bộ lọc cảnh báo", on_click=reset_filters, args=("risk",))
    dims = list(DIMS)[:4]
    all_scores = get_data(alerts_sql(), ["order_id", "risk_score", *dims])
    if all_scores["order_id"].duplicated().any():
        st.error("Có mã đơn bị trùng sau khi ghép dữ liệu. Kiểm tra khóa order_id của hai bảng Gold.")
        return
    df = filter_dimensions(all_scores, dims, "risk")
    search = st.sidebar.text_input("Tra cứu chính xác mã đơn", key="risk_order").strip()
    if search:
        df = df[df["order_id"].eq(search)]
    mode = st.sidebar.radio("Quy tắc chọn đơn", ["Top N", "Theo ngưỡng"], key="risk_mode")
    threshold, limit = 0.60, 50
    if mode == "Theo ngưỡng":
        threshold = st.sidebar.slider("Điểm tối thiểu", 0.0, 1.0, 0.60, 0.01, key="risk_cut")
        rule = f"Điểm ≥ {threshold:.2f}. Ngưỡng này dùng để thử nghiệm; chưa phải ngưỡng vận hành."
    else:
        limit = st.sidebar.selectbox("Số đơn ưu tiên", [10, 25, 50, 100, 200, 500],
                                     index=2, key="risk_top")
        rule = f"Tối đa {limit} đơn có điểm cao nhất sau khi lọc."
    queue = select_alerts(df, mode, threshold, limit)
    st.info(rule)
    if search and not df.empty:
        st.caption(f"Điểm dự đoán của đơn {search}: {df['risk_score'].iloc[0]:.4f}.")
    cols = st.columns(4)
    for col, (label, value) in zip(cols, [
        ("Đơn đã chấm điểm", f"{len(all_scores):,}"),
        ("Đơn khớp bộ lọc", f"{len(df):,}"),
        ("Đơn cần rà soát", f"{len(queue):,}"),
        ("Điểm cao nhất sau lọc", f"{df['risk_score'].max():.4f}" if not df.empty else "—"),
    ]):
        col.metric(label, value)

    if not df.empty:
        st.subheader("Phân bố điểm trong phạm vi lọc")
        # Bin in Python so the browser receives at most 20 points even with 50,000 orders.
        hist = (pd.cut(df["risk_score"], bins=[i / 20 for i in range(21)],
                       include_lowest=True, labels=False)
                .value_counts().reindex(range(20), fill_value=0))
        bars = pd.DataFrame({
            "start": [i / 20 for i in range(20)],
            "end": [(i + 1) / 20 for i in range(20)],
            "orders": hist.to_numpy(),
        })
        chart = alt.Chart(bars).mark_bar(color=BLUE, opacity=.85).encode(
            x=alt.X("start:Q", title="Điểm rủi ro", scale=alt.Scale(domain=[0, 1])),
            x2="end:Q",
            y=alt.Y("orders:Q", title="Số đơn"),
            tooltip=[alt.Tooltip("start", title="Từ", format=".2f"),
                     alt.Tooltip("end", title="Đến", format=".2f"),
                     alt.Tooltip("orders", title="Số đơn", format=",d")],
        )
        if mode == "Theo ngưỡng":
            marker = alt.Chart(pd.DataFrame({"threshold": [threshold]})).mark_rule(
                color=ORANGE, strokeWidth=2, strokeDash=[6, 3]
            ).encode(x="threshold:Q")
            chart = chart + marker
        show_chart(chart.properties(height=230))

    st.subheader("Danh sách cần rà soát")
    if queue.empty:
        st.info("Không có đơn thỏa điều kiện. Hãy đổi bộ lọc hoặc giảm ngưỡng điểm.")
        return
    output = queue.reset_index(drop=True)
    output.insert(0, "priority_rank", range(1, len(output) + 1))
    st.dataframe(
        output.head(1000),
        use_container_width=True,
        hide_index=True,
        column_config={
            "priority_rank": "Ưu tiên",
            "order_id": "Mã đơn",
            "risk_score": st.column_config.NumberColumn("Điểm rủi ro", format="%.4f"),
            **{k: DIMS[k] for k in dims},
        },
    )
    if len(output) > 1000:
        st.caption("Bảng xem trước 1.000 dòng đầu. CSV chứa toàn bộ danh sách đang lọc.")
    st.download_button(
        "Tải danh sách CSV", output.to_csv(index=False).encode("utf-8-sig"),
        file_name="return_risk_alerts.csv", mime="text/csv",
    )


st.sidebar.markdown("<div style='font-size:38px;text-align:center'>🛍️</div><h3 style='text-align:center;margin-top:0'>E-commerce<br>Returns Intelligence</h3><hr style='border-color:rgba(255,255,255,.2)'>", unsafe_allow_html=True)
page = st.sidebar.radio("", ["📊  Return Insights", "🔔  Risk Alerts", "✦  Model Explanation", "🗄️  Data Overview"], label_visibility="collapsed")
st.sidebar.markdown("<div style='margin-top:170px;padding:18px 12px;border-radius:22px;background:rgba(255,255,255,.16);font-weight:700;color:#193761'>📈<br><br>Smarter Insights.<br>Lower Return Rate.</div>", unsafe_allow_html=True)
if st.sidebar.button("↻  Làm mới dữ liệu"):
    query.clear()
if page == "📊  Return Insights":
    render_overview()
else:
    render_alerts()
