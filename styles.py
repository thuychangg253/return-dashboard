"""Styles for the reference-inspired E-commerce Returns Intelligence UI.

CSS changes appearance only; all numerical values come from loaded data.
"""

STYLES = r"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Be+Vietnam+Pro:wght@400;500;600;700;800&display=swap');
:root { --navy:#102C52; --navy2:#254B80; --ink:#101E39; --muted:#5A6B85; --blue:#317EE7; --blueSoft:#E7F1FF; --orange:#FFA94A; --orangeDeep:#EA9739; --surface:#F5F7FF; }
html, body { font-family:'Be Vietnam Pro','Segoe UI',Arial,sans-serif; }
/* ===== Local SHAP ===== */
.shap-prob{display:flex;align-items:center;gap:20px;padding:20px 22px;margin:8px 0 22px;
  background:linear-gradient(135deg,#F3F8FF,#FFF6EA);border:1px solid #E6ECF9;border-radius:20px;}
.shap-ring{position:relative;flex:0 0 86px;width:86px;height:86px;border-radius:50%;
  background:conic-gradient(#EA9739 calc(var(--ratio) * 1%),#D9E6FB 0);
  display:flex;align-items:center;justify-content:center;}
.shap-ring:after{content:"";position:absolute;inset:11px;border-radius:50%;background:#fff;}
.shap-ring b{position:relative;z-index:1;font-size:.95rem;font-weight:800;color:#102C52;}
.shap-prob-label{font-size:.85rem;font-weight:600;color:#5A6B85;}
.shap-prob-val{font-size:2.4rem;font-weight:800;letter-spacing:-.05em;line-height:1.25;color:#0B1936;}
.shap-badge{display:inline-block;margin-top:4px;padding:4px 12px;border-radius:50px;
  background:#FFE9CC;color:#9A5A0C;font-size:.76rem;font-weight:700;}
.shap-list{display:flex;flex-direction:column;gap:12px;margin-top:10px;}
.shap-row{display:grid;grid-template-columns:minmax(120px,1.1fr) 1.4fr auto;align-items:center;gap:12px;}
.shap-name{font-size:.9rem;font-weight:600;color:#172743;}
.shap-bar{height:10px;border-radius:10px;background:#EDF1FC;overflow:hidden;}
.shap-bar span{display:block;height:100%;border-radius:10px;background:linear-gradient(90deg,#FFA94A,#FF6B8B);}
.shap-val{font-size:.88rem;font-weight:800;color:#D6336C;min-width:62px;text-align:right;}
/* căn đầu ảnh waterfall ngang hàng với thẻ xác suất */
[data-testid="stElementContainer"]:has(.shap-plot-marker),
[data-testid="element-container"]:has(.shap-plot-marker){
  display:none !important;      /* ẩn phần tử đánh dấu để không tạo khoảng trống */
}
.shap-prob{margin-top:0 !important;}
/* khung cho ảnh waterfall */
[data-testid="stColumn"]:has(.shap-plot-marker) [data-testid="stImage"] img,
[data-testid="column"]:has(.shap-plot-marker) [data-testid="stImage"] img{
  background:#fff;border:1px solid #E6ECF9;border-radius:18px;padding:10px;
  box-shadow:0 8px 22px rgba(38,69,128,.06);
}
@media (max-width:760px){.shap-prob{flex-direction:column;align-items:flex-start;}
  .shap-row{grid-template-columns:1fr auto;}.shap-bar{grid-column:1 / -1;order:3;}}
/* ===== Sidebar: nút & caption luôn đọc được ===== */
[data-testid="stSidebar"] .stButton button,
[data-testid="stSidebar"] [data-testid="stBaseButton-secondary"],
[data-testid="stSidebar"] [data-testid="stBaseButton-primary"]{
  background:rgba(255,255,255,.16)!important;
  border:1px solid rgba(255,255,255,.55)!important;
  color:#FFFFFF!important;
  border-radius:12px;
  transition:.16s ease;
}
[data-testid="stSidebar"] .stButton button p,
[data-testid="stSidebar"] .stButton button span,
[data-testid="stSidebar"] [data-testid="stBaseButton-secondary"] p,
[data-testid="stSidebar"] [data-testid="stBaseButton-primary"] p{
  color:#FFFFFF!important;
  font-weight:600;
}
/* hover: chuyển sang cam, chữ đậm để vẫn đọc rõ */
[data-testid="stSidebar"] .stButton button:hover,
[data-testid="stSidebar"] [data-testid="stBaseButton-secondary"]:hover{
  background:linear-gradient(90deg,#FFC46E,#FFB454)!important;
  border-color:#FFB454!important;
}
[data-testid="stSidebar"] .stButton button:hover p,
[data-testid="stSidebar"] .stButton button:hover span,
[data-testid="stSidebar"] [data-testid="stBaseButton-secondary"]:hover p{
  color:#1D2B40!important;
}
[data-testid="stSidebar"] .stButton button:focus:not(:active){
  border-color:#FFB454!important;
  box-shadow:0 0 0 2px rgba(255,180,84,.35)!important;
}

/* chú thích "Nguồn: BigQuery Gold..." */
[data-testid="stSidebar"] [data-testid="stCaptionContainer"],
[data-testid="stSidebar"] [data-testid="stCaptionContainer"] p,
[data-testid="stSidebar"] [data-testid="stExpander"] small,
[data-testid="stSidebar"] [data-testid="stExpander"] [data-testid="stMarkdownContainer"] p{
  color:#DCEBFA!important;
  opacity:1!important;
}
/* chú thích trong nội dung expander (KHÔNG đụng vào tiêu đề summary) */
[data-testid="stSidebar"] [data-testid="stExpander"] [data-testid="stCaptionContainer"],
[data-testid="stSidebar"] [data-testid="stExpander"] [data-testid="stCaptionContainer"] p,
[data-testid="stSidebar"] [data-testid="stExpander"] details > div [data-testid="stMarkdownContainer"] p{
  color:#DCEBFA!important;
  opacity:1!important;
}

/* tiêu đề expander: nền kính mờ, chữ + mũi tên trắng */
[data-testid="stSidebar"] [data-testid="stExpander"] details summary{
  background:rgba(255,255,255,.12)!important;
  border-radius:12px;
}
[data-testid="stSidebar"] [data-testid="stExpander"] details summary:hover{
  background:rgba(255,255,255,.2)!important;
}
[data-testid="stSidebar"] [data-testid="stExpander"] details summary p,
[data-testid="stSidebar"] [data-testid="stExpander"] details summary span,
[data-testid="stSidebar"] [data-testid="stExpander"] details summary svg{
  color:#FFFFFF!important;
  fill:#FFFFFF!important;
  font-weight:600;
}
[data-testid="stSidebar"] [data-testid="stExpander"] details{
  background:transparent!important;
}
/* Không ép font mọi class st-* vì sẽ thay thế font của biểu tượng Streamlit. */
[data-testid="stAppViewContainer"]{ background: #F3F5FE !important; position:relative; }
[data-testid="stAppViewContainer"]:before{content:"";pointer-events:none;position:fixed;z-index:0;right:-175px;top:-175px;width:580px;height:470px;background:radial-gradient(circle at 72% 45%,rgba(255,167,65,.42) 0 19%,transparent 20%),radial-gradient(circle at 62% 53%,rgba(129,181,247,.44) 0 47%,transparent 47%),radial-gradient(circle at 73% 44%,rgba(184,218,252,.38) 0 62%,transparent 62%);border-radius:50%;opacity:.85;}
[data-testid="stHeader"]{background:rgba(243,245,254,.45);border:none;}
[data-testid="stDecoration"]{display:none;}
[data-testid="stSidebar"]{background:linear-gradient(150deg,#244578 0%,#2C568C 59%,#32679C 100%) !important;border-right:0;}
[data-testid="stSidebar"]:before{content:"";position:absolute;bottom:-160px;left:-185px;width:435px;height:475px;border-radius:50%;background:radial-gradient(circle,rgba(120,177,239,.42) 0 46%,transparent 47%);pointer-events:none;}
[data-testid="stSidebar"]:after{content:"";position:absolute;bottom:-160px;left:-130px;width:350px;height:285px;border-radius:50%;background:radial-gradient(circle,rgba(255,176,90,.41) 0 46%,transparent 47%);pointer-events:none;}
[data-testid="stSidebar"] > div{position:relative;z-index:1;}
[data-testid="stSidebar"] [data-testid="stMarkdownContainer"] p,
[data-testid="stSidebar"] [data-testid="stMarkdownContainer"] span,
[data-testid="stSidebar"] [data-testid="stWidgetLabel"] p,
[data-testid="stSidebar"] h1,
[data-testid="stSidebar"] h2 { color:#F8FBFF !important; }
[data-testid="stSidebar"] hr{border-color:rgba(255,255,255,.18);margin:17px 0;}
[data-testid="stSidebar"] [data-testid="stRadio"] [role="radiogroup"]{gap:9px;}
[data-testid="stSidebar"] [data-testid="stRadio"] [role="radiogroup"] label{
  display:flex;gap:10px;border-radius:15px;padding:13px 15px;border:1px solid transparent;
  color:white !important;transition:.16s ease;background:transparent;
}
[data-testid="stSidebar"] [data-testid="stRadio"] [role="radiogroup"] label:has(input:checked){background:linear-gradient(90deg,#FFC46E,#FFB454);box-shadow:0 5px 15px rgba(25,46,77,.15);}
[data-testid="stSidebar"] [data-testid="stRadio"] [role="radiogroup"] label:has(input:checked) p{color:#1D2B40 !important;font-weight:800;}
[data-testid="stSidebar"] [data-testid="stRadio"] [role="radiogroup"] label:not(:has(input:checked)):hover{background:rgba(255,255,255,.13);}
[data-testid="stSidebar"] [data-testid="stRadio"] [role="radiogroup"] label [data-testid="stMarkdownContainer"] p{font-size:.96rem;font-weight:600;}
[data-testid="stSidebar"] [data-testid="stRadio"] [role="radiogroup"] label [data-testid="stMarkdownContainer"] p{color:white !important;}
[data-testid="stSidebar"] [data-testid="stRadio"] [role="radiogroup"] label:has(input:checked) [data-testid="stMarkdownContainer"] p{color:#1D2B40 !important;}
[data-testid="stSidebar"] [data-testid="stRadio"] [role="radiogroup"] label>div:first-child{display:none;}
[data-testid="stSidebar"] [data-testid="stExpander"]{background:rgba(20,46,83,.15);border:1px solid rgba(255,255,255,.17);border-radius:12px;}
[data-testid="stSidebar"] [data-testid="stExpander"] details summary{color:#fff !important;}
[data-testid="stSidebar"] [data-testid="stExpander"] input, [data-testid="stSidebar"] [data-baseweb="select"] >div{background:#FCFCFF;border-radius:9px;}
[data-testid="stSidebar"] .stButton button{border-radius:10px;}
.block-container{max-width:1580px !important;padding:2.6rem 2.1rem 2.7rem !important;position:relative;z-index:1;}
[data-testid="stHorizontalBlock"]{gap:1.25rem;}
.brand-wrap{padding:21px 9px 7px;min-height:174px;}
.brand-bag{width:64px;height:75px;margin:0 auto 8px;display:block;filter:drop-shadow(0 5px 8px rgba(7,29,62,.19));}
.brand-name{font-size:1.13rem;line-height:1.55;font-weight:800;color:white;text-align:left;}
.brand-line{height:1px;background:rgba(255,255,255,.23);margin-top:20px;}
.sidebar-motto{margin-top:38px;padding:15px 13px;background:linear-gradient(145deg,rgba(203,225,249,.32),rgba(255,206,145,.14));border-radius:18px;color:#ECF7FF;font-weight:600;line-height:1.6;font-size:.93rem;}
.nav-footer{margin-top:8px;font-size:.7rem;color:#C8E0F6;line-height:1.4;}
.page-top{position:relative;padding:1px 0 18px;min-height:127px;}
.page-top .page-title{font-size:2rem;font-weight:800;color:#101A33;letter-spacing:-.04em;line-height:1.35;}
.page-top .page-sub{font-size:.97rem;font-weight:500;color:#495B73;margin-top:5px;max-width:790px;line-height:1.6;}
.page-top .scope-pill{position:absolute;right:5px;top:1px;display:inline-flex;gap:7px;align-items:center;background:rgba(255,255,255,.9);border:1px solid #EDF1FA;border-radius:50px;padding:9px 15px;color:#2F4565;font-size:.82rem;font-weight:700;box-shadow:0 6px 18px rgba(46,75,124,.06);}
.metric-card{min-height:177px;background:rgba(255,255,255,.97);border:1px solid rgba(227,233,248,.87);border-radius:23px;padding:21px 23px;position:relative;box-shadow:0 11px 26px rgba(42,74,133,.06);overflow:hidden;}
.metric-head{display:flex;align-items:center;gap:12px;color:#172740;font-size:.99rem;font-weight:700;min-height:44px;}
.metric-icon{display:flex;align-items:center;justify-content:center;width:42px;height:42px;border-radius:50%;font-size:22px;}
.metric-card.blue .metric-icon{background:#E6F0FF;}
.metric-card.orange .metric-icon{background:#FFF0DC;}
.metric-card.purple .metric-icon{background:#F1EBFF;}
.metric-val{font-weight:800;font-size:2.19rem;line-height:1.3;letter-spacing:-.055em;color:#0B1936;margin:18px 0 4px;}
.metric-caption{font-size:.72rem;color:#657891;margin-top:2px;max-width:92%;}
.metric-card.blue:after,.metric-card.orange:after{content:"";position:absolute;bottom:0;right:-12px;width:124px;height:38px;background:linear-gradient(165deg,transparent,rgba(93,167,234,.12));transform:skewY(-12deg);border-radius:55% 30% 0 0;}
.metric-card.orange:after{background:linear-gradient(165deg,transparent,rgba(255,183,96,.19));}
.metric-ring{position:absolute;right:21px;bottom:21px;width:57px;height:57px;border-radius:50%;background:conic-gradient(#236EDD calc(var(--ratio) * 1%),#CFE1FE 0);}
.metric-ring:after{content:"";position:absolute;inset:14px;border-radius:50%;background:#fff;}
.metric-watermark{position:absolute;right:20px;bottom:17px;font-size:49px;opacity:.22;}
.kpi-footnote{font-size:.75rem;color:#5D7088;margin-top:8px;}
.section-title{font-size:1.41rem;color:#111F39;font-weight:800;line-height:1.35;margin:0;}
.section-sub{font-size:.85rem;color:#708099;margin:6px 0 7px;}
.section-caption{font-weight:800;color:#172743;font-size:.98rem;margin:7px 0 4px;}
#MainMenu, footer{visibility:hidden;}
/* large white charts panel for Streamlit st.container(border=True) */
[data-testid="stVerticalBlockBorderWrapper"]:has([data-testid="stPlotlyChart"]){background:rgba(255,255,255,.98)!important;border:1px solid #E6ECF9!important;border-radius:23px!important;padding:18px 18px 4px!important;box-shadow:0 14px 30px rgba(38,69,128,.06)!important;}
[data-testid="stPlotlyChart"]{border:0!important;background:transparent!important;}
[data-testid="stPlotlyChart"] > div{border:none!important;}
[data-testid="stRadio"] [role="radiogroup"]{gap:0;}
[data-testid="stMain"] [data-testid="stRadio"] [role="radiogroup"]{padding:3px;border-radius:25px;background:#EDF1FC;display:inline-flex;gap:0;}
[data-testid="stMain"] [data-testid="stRadio"] [role="radiogroup"] label{padding:8px 14px;border-radius:21px;}
[data-testid="stMain"] [data-testid="stRadio"] [role="radiogroup"] label:has(input:checked){background:#235B9F;}
[data-testid="stMain"] [data-testid="stRadio"] [role="radiogroup"] label:has(input:checked) p{color:white!important;}
[data-testid="stMain"] [data-testid="stRadio"] [role="radiogroup"] label>div:first-child{display:none;}
[data-testid="stDataFrame"]{border-radius:15px;overflow:hidden;}
[data-testid="stDownloadButton"] button{background:#FFA846;color:#1F3047;border-radius:11px;border:0;font-weight:700;}
[data-testid="stTabs"] button{font-weight:700;}
[data-testid="stAlert"]{border-radius:13px;overflow-wrap:anywhere;}
[data-testid="stAlert"] p{line-height:1.55;white-space:normal;}
[data-testid="stExpander"] summary p{line-height:1.45;margin:0;}
.small-explainer{color:#63768C;font-size:.75rem;line-height:1.7;margin:14px 0;}
footer{display:none;}
@media (max-width:1180px){.page-top .scope-pill{position:static;margin-top:9px;}.page-top{min-height:unset;padding-bottom:22px;}.metric-val{font-size:1.7rem;}.metric-card{padding:16px;min-height:150px;}.block-container{padding:1.5rem 1rem!important;}}
@media (max-width:760px){.page-top .page-title{font-size:1.5rem;}.metric-card{min-height:135px;}.metric-ring{width:43px;height:43px;}.metric-ring:after{inset:11px;}}
</style>
"""
