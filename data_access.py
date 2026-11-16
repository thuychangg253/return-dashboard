"""BigQuery Gold-only data access, based on the user's original Streamlit source.

History: ml_return_train aggregated in BigQuery.
Risk: ml_return_test INNER JOIN return_risk_scores.
No CSV, no Fact join, no recalculating risk scores.
"""
import re
import pandas as pd

DIMS = {
    "product_category": "Danh mục sản phẩm",
    "shipping_method": "Phương thức vận chuyển",
    "payment_method": "Phương thức thanh toán",
    "device_type": "Thiết bị",
}
UNKNOWN = "Không xác định"
FLAG_COLUMNS = [
    "flag_age_under_18", "flag_bad_price", "flag_bad_discount",
    "flag_bad_views", "flag_rating_out_of_range",
    "flag_bad_return_rate", "flag_bad_session",
]
FLAG_COUNT_COLUMNS = [f"{f}_count" for f in FLAG_COLUMNS]
HISTORY_COLUMNS = [*DIMS, "orders", "returns", "price_flags", "flag_any_silver_count", *FLAG_COUNT_COLUMNS]
ALERT_COLUMNS = ["order_id", "risk_score", *DIMS]


def gold_name(project, dataset="Dataset3_Gold"):
    for name in (project, dataset):
        if not re.fullmatch(r"[A-Za-z0-9_-]+", name):
            raise ValueError("Project ID hoặc Dataset không hợp lệ")
    return f"{project}.{dataset}"


def _active_flag(field):
    return f"LOWER(TRIM(CAST({field} AS STRING))) IN ('1', 'true')"


def history_sql(project, dataset="Dataset3_Gold"):
    """Original source: read labeled ML Gold data and aggregate on BigQuery.

    Additional seven count columns serve the new Data Overview page, without
    fetching 200,000 individual orders or modifying the original BI semantics.
    """
    gold = gold_name(project, dataset)
    dims = ", ".join(f"COALESCE({f}, '{UNKNOWN}') AS {f}" for f in DIMS)
    flag_projection = ",\n             ".join(FLAG_COLUMNS)
    flag_count_sql = ",\n             ".join(
        f"COUNTIF({_active_flag(f)}) AS {f}_count" for f in FLAG_COLUMNS
    )
    any_flag = " OR ".join(_active_flag(f) for f in FLAG_COLUMNS)
    return f"""
        WITH labeled_orders AS (
          SELECT {dims},
                 LOWER(TRIM(CAST(returned_status AS STRING))) AS return_label,
                 {flag_projection}
          FROM `{gold}.ml_return_train`
        )
        SELECT product_category, shipping_method, payment_method, device_type,
               COUNT(*) AS orders,
               COUNTIF(return_label IN ('1','true')) AS returns,
               COUNTIF({_active_flag('flag_bad_price')}) AS price_flags,
               COUNTIF({any_flag}) AS flag_any_silver_count,
               {flag_count_sql}
        FROM labeled_orders
        WHERE return_label IN ('0','1','false','true')
        GROUP BY 1,2,3,4
    """


def alerts_sql(project, dataset="Dataset3_Gold"):
    """Preserves the old source's join and risk-score semantics exactly."""
    gold = gold_name(project, dataset)
    dims = ", ".join(f"COALESCE(t.{f}, '{UNKNOWN}') AS {f}" for f in DIMS)
    return f"""
      SELECT CAST(t.order_id AS STRING) AS order_id, s.risk_score, {dims}
      FROM `{gold}.ml_return_test` AS t
      INNER JOIN `{gold}.return_risk_scores` AS s
        ON CAST(t.order_id AS STRING) = CAST(s.order_id AS STRING)
      WHERE s.risk_score BETWEEN 0 AND 1
    """


def validate_history(df):
    if not set(HISTORY_COLUMNS).issubset(df.columns):
        raise ValueError("Kết quả ml_return_train thiếu cột thống kê")
    for col in ("orders", "returns", "price_flags", "flag_any_silver_count", *FLAG_COUNT_COLUMNS):
        df[col] = pd.to_numeric(df[col],errors='raise').astype('int64')
    if not ((df['returns'] >= 0) & (df['returns'] <= df['orders'])).all():
        raise ValueError("Số hoàn trả không hợp lệ")
    if not ((df['price_flags'] >= 0) & (df['price_flags'] <= df['orders'])).all():
        raise ValueError("Số cờ giá không hợp lệ")
    if df['orders'].sum() <= 0:
        raise ValueError("Không có dữ liệu có nhãn hợp lệ từ ml_return_train")
    return df


def validate_alerts(df):
    if not set(ALERT_COLUMNS).issubset(df.columns):
        raise ValueError("Kết quả Risk Alerts thiếu cột")
    df['order_id'] = df['order_id'].astype('string')
    df['risk_score'] = pd.to_numeric(df['risk_score'],errors='raise')
    if df['order_id'].isna().any() or not df['order_id'].is_unique:
        raise ValueError("Bảng score join ra mã đơn bị trùng/thiếu. Kiểm tra order_id trên BigQuery")
    if not df['risk_score'].between(0,1).all():
        raise ValueError("Risk score nằm ngoài 0–1 hoặc bị thiếu")
    return df


def group_stats(df, field):
    if df.empty:
        return pd.DataFrame(columns=[field,"orders","returns","rate"])
    groups=df.groupby(field,as_index=False,dropna=False,observed=True)[["orders","returns"]].sum()
    groups=groups[groups.orders>0].copy()
    groups['rate']=groups.returns / groups.orders * 100
    return groups.sort_values('rate',ascending=False)


def make_summary(df):
    n=int(df['orders'].sum()) if len(df) else 0
    r=int(df['returns'].sum()) if len(df) else 0
    flagged=int(df['flag_any_silver_count'].sum()) if len(df) else 0
    return {'orders':n,'returns':r,'rate':100*r/n if n else 0,
            'flagged':flagged,'flagged_pct':100*flagged/n if n else 0}
