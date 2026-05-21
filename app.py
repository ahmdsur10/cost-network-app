import streamlit as st
import json
import math
import os
import tempfile
import zipfile
from io import BytesIO
import folium
from folium.plugins import Draw, MeasureControl
from streamlit_folium import st_folium
import pandas as pd

# ─── Page Config ───────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="حاسبة تكلفة شبكات السيول",
    page_icon="🌊",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─── CSS ───────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Cairo:wght@400;600;700;900&display=swap');

html, body, [class*="css"], .stApp {
    font-family: 'Cairo', sans-serif !important;
    direction: rtl;
}

/* ── Sidebar ── */
[data-testid="stSidebar"] {
    min-width: 380px !important;
    max-width: 420px !important;
    background: #f7f9fc !important;
    border-left: 3px solid #d0e4f7;
}
[data-testid="stSidebar"] > div { padding-top: 0 !important; }

.sidebar-header {
    background: linear-gradient(135deg, #0a2a5e 0%, #1a5fa8 100%);
    color: white;
    padding: 18px 20px 14px;
    margin: -1px -1px 16px -1px;
    text-align: center;
}
.sidebar-header h2 { margin: 0; font-size: 1.15rem; font-weight: 900; color: #fff; }
.sidebar-header p  { margin: 4px 0 0; font-size: 0.78rem; color: #b8d9f8; }

.section-title {
    background: #1a5fa8;
    color: white !important;
    padding: 7px 14px;
    border-radius: 8px;
    font-weight: 700;
    font-size: 0.92rem;
    margin: 14px 0 10px;
    display: block;
}

.price-card {
    background: #fff;
    border: 1.5px solid #d0e4f7;
    border-right: 5px solid #1a5fa8;
    border-radius: 8px;
    padding: 10px 14px;
    margin-bottom: 8px;
    font-size: 0.88rem;
    color: #1a2a3a;
    direction: rtl;
}
.price-card .p-name { font-weight: 700; color: #0a2a5e; font-size: 0.9rem; }
.price-card .p-spec { color: #5a7a9a; font-size: 0.8rem; margin: 2px 0; }
.price-card .p-price { color: #c0392b; font-weight: 900; font-size: 0.95rem; }

.upload-zone {
    background: #eaf4ff;
    border: 2px dashed #1a5fa8;
    border-radius: 10px;
    padding: 14px;
    text-align: center;
    color: #1a5fa8;
    font-size: 0.85rem;
    margin-bottom: 10px;
}

.sig-box {
    background: #0a2a5e;
    color: #a8d0f0 !important;
    text-align: center;
    padding: 12px;
    border-radius: 10px;
    margin-top: 16px;
    font-size: 0.82rem;
}
.sig-box b { color: #ffffff !important; font-size: 0.95rem; }

/* ── Main area ── */
.main { background: #f0f4fa; }

.app-header {
    background: linear-gradient(135deg, #0a2a5e 0%, #1a5fa8 60%, #0e4080 100%);
    color: white;
    padding: 20px 28px;
    border-radius: 14px;
    margin-bottom: 16px;
    display: flex;
    align-items: center;
    justify-content: space-between;
    box-shadow: 0 6px 24px rgba(10,42,94,0.22);
    direction: rtl;
}
.app-header h1 { margin: 0; font-size: 1.55rem; font-weight: 900; color: #fff; }
.app-header p  { margin: 4px 0 0; font-size: 0.88rem; color: #a8c8f0; }
.app-header .badge {
    background: rgba(255,255,255,0.18);
    border: 1px solid rgba(255,255,255,0.35);
    color: #e8f4ff;
    padding: 6px 16px;
    border-radius: 20px;
    font-size: 0.82rem;
    white-space: nowrap;
    font-weight: 700;
}

.metric-card {
    background: white;
    border-radius: 12px;
    padding: 14px 18px;
    box-shadow: 0 2px 12px rgba(0,0,0,0.07);
    border-top: 4px solid #1a5fa8;
    text-align: center;
    direction: rtl;
}
.metric-card .val { font-size: 1.55rem; font-weight: 900; color: #0a2a5e; }
.metric-card .lbl { font-size: 0.8rem; color: #6b7a99; margin-top: 3px; }

.result-box {
    background: linear-gradient(135deg, #0a2a5e, #1a5fa8);
    color: white !important;
    padding: 20px 24px;
    border-radius: 14px;
    font-size: 1.1rem;
    font-weight: 700;
    text-align: center;
    box-shadow: 0 4px 20px rgba(26,95,168,0.35);
    margin-top: 12px;
    direction: rtl;
    line-height: 1.9;
}

.info-box {
    background: #eaf4ff;
    border-right: 4px solid #1a5fa8;
    border-radius: 8px;
    padding: 12px 16px;
    font-size: 0.88rem;
    color: #0a2a5e;
    margin-bottom: 10px;
    direction: rtl;
    text-align: right;
    line-height: 1.8;
}

.warn-box {
    background: #fff8e1;
    border-right: 4px solid #f9a825;
    border-radius: 8px;
    padding: 10px 14px;
    font-size: 0.87rem;
    color: #5d4037;
    margin-bottom: 8px;
    direction: rtl;
}

/* Tabs */
.stTabs [data-baseweb="tab-list"] {
    background: #e4edf8;
    border-radius: 10px;
    padding: 4px;
    gap: 4px;
}
.stTabs [data-baseweb="tab"] {
    border-radius: 8px;
    font-family: 'Cairo', sans-serif !important;
    font-weight: 700;
    font-size: 0.95rem;
}
.stTabs [aria-selected="true"] {
    background: #1a5fa8 !important;
    color: white !important;
}

/* Buttons */
.stButton > button {
    background: linear-gradient(135deg, #1a5fa8, #0a2a5e) !important;
    color: white !important;
    border: none !important;
    border-radius: 10px !important;
    font-family: 'Cairo', sans-serif !important;
    font-weight: 700 !important;
    font-size: 1rem !important;
    width: 100% !important;
    padding: 10px 20px !important;
    box-shadow: 0 3px 10px rgba(26,95,168,0.3) !important;
    transition: all 0.2s !important;
}
.stButton > button:hover {
    transform: translateY(-1px) !important;
    box-shadow: 0 5px 16px rgba(26,95,168,0.45) !important;
}

.stNumberInput input { font-family: 'Cairo', sans-serif !important; font-size: 1rem !important; }
.stMultiSelect { font-family: 'Cairo', sans-serif !important; }
.stSelectbox  { font-family: 'Cairo', sans-serif !important; }
</style>
""", unsafe_allow_html=True)

# ─── Constants ─────────────────────────────────────────────────────────────────
RIYADH_LAT, RIYADH_LON = 24.7136, 46.6753
DEFAULT_ZOOM = 14

# ─── Helpers ───────────────────────────────────────────────────────────────────
def haversine(lon1, lat1, lon2, lat2):
    R = 6371000
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi   = math.radians(lat2 - lat1)
    dlambda= math.radians(lon2 - lon1)
    a = math.sin(dphi/2)**2 + math.cos(phi1)*math.cos(phi2)*math.sin(dlambda/2)**2
    return 2 * R * math.asin(math.sqrt(a))

def line_length_m(coords):
    """حساب طول الخط من قائمة إحداثيات [lon, lat]"""
    total = 0.0
    if not coords or len(coords) < 2:
        return 0.0
    for i in range(len(coords) - 1):
        c0, c1 = coords[i], coords[i+1]
        # تأكد أن الإحداثيات أرقام وليست قوائم فارغة
        try:
            total += haversine(float(c0[0]), float(c0[1]), float(c1[0]), float(c1[1]))
        except (TypeError, IndexError, ValueError):
            continue
    return total

def get_center(coords_all):
    valid = []
    for c in coords_all:
        try:
            valid.append((float(c[0]), float(c[1])))
        except (TypeError, IndexError, ValueError):
            pass
    if not valid:
        return RIYADH_LAT, RIYADH_LON
    lons = [c[0] for c in valid]
    lats = [c[1] for c in valid]
    return sum(lats)/len(lats), sum(lons)/len(lons)

def extract_coords_from_geometry(geom):
    """استخراج الإحداثيات بأمان من أي نوع هندسي خطي"""
    if geom is None:
        return []
    gtype = geom.get("type", "")
    raw   = geom.get("coordinates", [])

    coords = []
    if gtype == "LineString":
        coords = raw
    elif gtype == "MultiLineString":
        for part in raw:
            coords.extend(part)
    # تصفية: كل إحداثية يجب أن تكون قائمة/tuple بطول >= 2
    clean = []
    for c in coords:
        if isinstance(c, (list, tuple)) and len(c) >= 2:
            try:
                clean.append([float(c[0]), float(c[1])])
            except (TypeError, ValueError):
                pass
    return clean

def load_geojson_data(raw_text):
    """تحميل GeoJSON وإرجاع قائمة features وكل الإحداثيات"""
    try:
        gj = json.loads(raw_text)
    except json.JSONDecodeError as e:
        st.error(f"خطأ في قراءة ملف GeoJSON: {e}")
        return [], []

    features   = []
    coords_all = []
    raw_features = gj.get("features", [])

    for idx, feat in enumerate(raw_features):
        if not isinstance(feat, dict):
            continue
        geom  = feat.get("geometry") or {}
        props = feat.get("properties") or {}

        coords = extract_coords_from_geometry(geom)
        if len(coords) < 2:
            continue

        length = line_length_m(coords)
        features.append({
            "index":    idx,
            "id_label": f"خط #{idx}",
            "length_m": round(length, 2),
            "coords":   coords,
            "properties": props,
        })
        coords_all.extend(coords)

    return features, coords_all

def load_shapefile_from_zip(zip_bytes):
    """تحميل Shapefile من ملف zip"""
    try:
        import shapefile
    except ImportError:
        st.error("مكتبة pyshp غير متاحة — يرجى رفع ملف GeoJSON.")
        return [], []

    try:
        with tempfile.TemporaryDirectory() as tmpdir:
            with zipfile.ZipFile(BytesIO(zip_bytes)) as z:
                z.extractall(tmpdir)
            shp_file = None
            for root, _, files in os.walk(tmpdir):
                for f in files:
                    if f.lower().endswith(".shp"):
                        shp_file = os.path.join(root, f)
                        break
                if shp_file:
                    break
            if not shp_file:
                st.error("لم يُعثر على ملف .shp داخل الضغط.")
                return [], []

            sf = shapefile.Reader(shp_file)
            features   = []
            coords_all = []
            field_names = [f[0] for f in sf.fields[1:]]

            for idx, shape_rec in enumerate(sf.shapeRecords()):
                pts = shape_rec.shape.points
                coords = [[float(p[0]), float(p[1])] for p in pts if len(p) >= 2]
                if len(coords) < 2:
                    continue
                props  = dict(zip(field_names, shape_rec.record))
                length = line_length_m(coords)
                features.append({
                    "index":    idx,
                    "id_label": f"خط #{idx}",
                    "length_m": round(length, 2),
                    "coords":   coords,
                    "properties": props,
                })
                coords_all.extend(coords)
            return features, coords_all
    except Exception as e:
        st.error(f"خطأ في قراءة Shapefile: {e}")
        return [], []

# ─── Session State ─────────────────────────────────────────────────────────────
for key, default in [("features", []), ("coords_all", [])]:
    if key not in st.session_state:
        st.session_state[key] = default

# ─── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("""
    <div class="sidebar-header">
        <h2>🌊 حاسبة تكلفة شبكات السيول</h2>
        <p>تطوير: Eng. Ahmed Adam</p>
    </div>
    """, unsafe_allow_html=True)

    # Upload
    st.markdown('<span class="section-title">📂 رفع بيانات الشبكة</span>', unsafe_allow_html=True)
    st.markdown("""
    <div class="upload-zone">
        📁 GeoJSON &nbsp;|&nbsp; Shapefile (.zip)<br>
        <small>ارفع ملف يحتوي على خطوط شبكة التصريف</small>
    </div>
    """, unsafe_allow_html=True)

    uploaded = st.file_uploader(
        "اختر الملف",
        type=["geojson", "json", "zip"],
        label_visibility="collapsed",
    )

    if uploaded:
        ext = uploaded.name.lower().rsplit(".", 1)[-1]
        raw = uploaded.read()
        with st.spinner("⏳ جاري تحميل البيانات..."):
            if ext in ("geojson", "json"):
                feats, ca = load_geojson_data(raw.decode("utf-8", errors="ignore"))
            else:
                feats, ca = load_shapefile_from_zip(raw)

        if feats:
            st.session_state.features  = feats
            st.session_state.coords_all = ca
            st.success(f"✅ تم تحميل **{len(feats)}** خط بنجاح!")
        else:
            st.warning("⚠️ لم يتم العثور على خطوط صالحة في الملف.\nتأكد أن الملف يحتوي على LineString أو MultiLineString.")

    # Stats
    if st.session_state.features:
        feats_sb = st.session_state.features
        total_len_sb = sum(f["length_m"] for f in feats_sb)
        c1, c2 = st.columns(2)
        with c1:
            st.metric("عدد الخطوط", len(feats_sb))
        with c2:
            st.metric("إجمالي الطول", f"{total_len_sb/1000:.1f} كم")

    st.markdown("---")

    # Price reference
    st.markdown('<span class="section-title">💲 الأسعار الإرشادية (ريال/متر)</span>', unsafe_allow_html=True)
    st.markdown("""
    <div class="price-card">
        <div class="p-name">🔵 أنابيب تصريف</div>
        <div class="p-spec">قطر 1400 ملم</div>
        <div class="p-price">4,004 ريال / متر</div>
    </div>
    <div class="price-card">
        <div class="p-name">🟠 قناة صندوقية (Box Culvert)</div>
        <div class="p-spec">أبعاد: 1.8 × 1.4 متر</div>
        <div class="p-price">9,336 ريال / متر</div>
    </div>
    <div class="price-card">
        <div class="p-name">🟢 قناة مفتوحة</div>
        <div class="p-spec">عرض 12م — عمق 1.5م</div>
        <div class="p-price">13,052 ريال / متر</div>
    </div>
    <div class="warn-box">
        ⚠️ الأسعار تقريبية وللاسترشاد فقط،<br>وقد تختلف حسب الموقع والظروف.
    </div>
    """, unsafe_allow_html=True)

    st.markdown("""
    <div class="sig-box">
        <b>Eng: Ahmed Adam</b><br>
        نظام تحليل شبكات تصريف السيول<br>
        <small>جميع الحقوق محفوظة © 2025</small>
    </div>
    """, unsafe_allow_html=True)

# ─── Header ────────────────────────────────────────────────────────────────────
st.markdown("""
<div class="app-header">
  <div>
    <h1>🌊 حاسبة تكلفة شبكات تصريف السيول</h1>
    <p>تحليل الشبكات &nbsp;•&nbsp; حساب الأطوال &nbsp;•&nbsp; تقدير التكاليف</p>
  </div>
  <div class="badge">Eng: Ahmed Adam</div>
</div>
""", unsafe_allow_html=True)

# ─── Tabs ──────────────────────────────────────────────────────────────────────
tab1, tab2, tab3 = st.tabs([
    "🗺️ حساب تكلفة خطوط الشبكة",
    "✏️ رسم خط جديد وحساب تكلفته",
    "📊 جدول بيانات الشبكة",
])

# ══════════════════════════════════════════════════════════════════════════════
# TAB 1
# ══════════════════════════════════════════════════════════════════════════════
with tab1:
    feats = st.session_state.features

    if not feats:
        st.markdown("""
        <div class="info-box">
            ⬅️ <b>ابدأ برفع ملف البيانات من القائمة الجانبية</b><br>
            يدعم التطبيق ملفات: GeoJSON (.geojson / .json) أو Shapefile مضغوط (.zip)
        </div>
        """, unsafe_allow_html=True)

    # Metrics
    if feats:
        total_len = sum(f["length_m"] for f in feats)
        c1, c2, c3 = st.columns(3)
        with c1:
            st.markdown(f'<div class="metric-card"><div class="val">{len(feats):,}</div><div class="lbl">إجمالي الخطوط</div></div>', unsafe_allow_html=True)
        with c2:
            st.markdown(f'<div class="metric-card"><div class="val">{total_len/1000:,.2f}</div><div class="lbl">إجمالي الطول (كم)</div></div>', unsafe_allow_html=True)
        with c3:
            st.markdown(f'<div class="metric-card"><div class="val">{total_len:,.0f}</div><div class="lbl">إجمالي الطول (م)</div></div>', unsafe_allow_html=True)
        st.markdown("<br>", unsafe_allow_html=True)

    # ── Map 1 ──
    if st.session_state.coords_all:
        map_center = get_center(st.session_state.coords_all)
        map_zoom   = 14
    else:
        map_center = (RIYADH_LAT, RIYADH_LON)
        map_zoom   = DEFAULT_ZOOM

    m1 = folium.Map(
        location=list(map_center),
        zoom_start=map_zoom,
        tiles="OpenStreetMap",
    )
    folium.TileLayer(
        tiles="https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}",
        attr="Esri", name="صورة فضائية",
    ).add_to(m1)
    folium.TileLayer("CartoDB positron", name="خريطة فاتحة").add_to(m1)
    folium.LayerControl(collapsed=False).add_to(m1)

    for f in feats:
        coords_ll = [(c[1], c[0]) for c in f["coords"]]
        props_html = "".join(
            f"<tr><td style='padding:2px 6px;color:#555'>{k}</td><td style='padding:2px 6px;font-weight:600'>{v}</td></tr>"
            for k, v in f["properties"].items()
            if v not in (None, "", "None")
        )
        popup_html = f"""
        <div dir='rtl' style='font-family:Cairo,sans-serif;min-width:200px;font-size:13px'>
            <div style='background:#1a5fa8;color:#fff;padding:6px 10px;border-radius:4px;margin-bottom:6px;font-weight:900'>
                خط #{f['index']}
            </div>
            <b>الطول:</b> {f['length_m']:,.1f} م
            &nbsp;({f['length_m']/1000:.3f} كم)<br>
            {'<table style="margin-top:6px;width:100%">' + props_html + '</table>' if props_html else ''}
        </div>
        """
        folium.PolyLine(
            coords_ll,
            color="#1a5fa8", weight=3.5, opacity=0.9,
            tooltip=folium.Tooltip(f"خط #{f['index']}  |  {f['length_m']:,.0f} م", sticky=True),
            popup=folium.Popup(popup_html, max_width=280),
        ).add_to(m1)

    st_folium(m1, width="100%", height=430, returned_objects=[], key="map1")

    # ── Selection & Cost ──
    if feats:
        st.markdown("### 📌 اختر الخطوط لحساب تكلفتها")
        st.markdown("""
        <div class="info-box">
            💡 يمكنك اختيار <b>خط واحد أو أكثر</b> — رقم الخط مطابق لرقم الـ Index في الجدول والـ Popup<br>
            🔍 اكتب رقم الخط في مربع البحث للانتقال إليه مباشرة
        </div>
        """, unsafe_allow_html=True)

        options = [f"خط #{f['index']}  ——  {f['length_m']:,.1f} م" for f in feats]
        selected_labels = st.multiselect(
            "🔍 ابحث واختر الخطوط:",
            options=options,
            placeholder="اكتب رقم الخط أو اختر من القائمة...",
            key="line_sel",
        )

        sel_indices = [options.index(s) for s in selected_labels]
        sel_feats   = [feats[i] for i in sel_indices]
        total_sel   = sum(f["length_m"] for f in sel_feats)

        if sel_feats:
            c1, c2 = st.columns(2)
            with c1:
                st.markdown(f'<div class="metric-card"><div class="val">{len(sel_feats)}</div><div class="lbl">عدد الخطوط المختارة</div></div>', unsafe_allow_html=True)
            with c2:
                st.markdown(f'<div class="metric-card"><div class="val">{total_sel:,.1f} م</div><div class="lbl">مجموع الأطوال</div></div>', unsafe_allow_html=True)
            st.markdown("<br>", unsafe_allow_html=True)

            # Highlight map
            m1b = folium.Map(location=list(map_center), zoom_start=map_zoom, tiles="OpenStreetMap")
            for f in feats:
                cll = [(c[1], c[0]) for c in f["coords"]]
                is_sel = f in sel_feats
                folium.PolyLine(
                    cll,
                    color="#e74c3c" if is_sel else "#b0c0d8",
                    weight=6 if is_sel else 2,
                    opacity=1.0 if is_sel else 0.45,
                    tooltip=folium.Tooltip(f"خط #{f['index']}" + (" ✅ مختار" if is_sel else ""), sticky=True),
                ).add_to(m1b)
            st_folium(m1b, width="100%", height=300, returned_objects=[], key="map1b")

        st.markdown("### 💰 احسب التكلفة الإجمالية")
        col_p, col_b = st.columns([3, 1])
        with col_p:
            price1 = st.number_input(
                "سعر المتر الواحد (ريال):",
                min_value=0.0, value=4004.0, step=100.0,
                format="%.2f", key="price1",
                help="أسعار إرشادية ← أنابيب 1400ملم: 4,004  |  قناة صندوقية: 9,336  |  قناة مفتوحة: 13,052",
            )
        with col_b:
            st.markdown("<br>", unsafe_allow_html=True)
            calc1 = st.button("احسب 💰", key="calc1")

        if calc1:
            if not sel_feats:
                st.warning("⚠️ الرجاء اختيار خط واحد على الأقل قبل الحساب.")
            else:
                cost = total_sel * price1
                lines_str = "  |  ".join([f"خط #{f['index']} ({f['length_m']:,.0f}م)" for f in sel_feats])
                st.markdown(f"""
<div class="result-box">
    📋 الخطوط المختارة:<br>
    <span style="font-size:0.88rem;font-weight:400">{lines_str}</span><br><br>
    📏 مجموع الأطوال: <b>{total_sel:,.2f} متر</b>  ({total_sel/1000:.3f} كم)<br>
    💲 سعر المتر: <b>{price1:,.2f} ريال</b><br>
    ━━━━━━━━━━━━━━━━━━━━━━━<br>
    💰 التكلفة الإجمالية: <b style="font-size:1.3rem">{cost:,.2f} ريال</b><br>
    ≈ <b>{cost/1_000_000:.3f} مليون ريال</b>
</div>
""", unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════════════════
# TAB 2 – Draw
# ══════════════════════════════════════════════════════════════════════════════
with tab2:
    st.markdown("### ✏️ ارسم خطاً على الخريطة وقيس طوله")

    st.markdown("""
    <div class="info-box" style="text-align:right;direction:rtl">
        <b>📌 تعليمات الرسم (خطوة بخطوة):</b><br>
        <b>١.</b> انقر على أيقونة <b>رسم الخط</b> في شريط الأدوات على <b>يسار</b> الخريطة<br>
        <b>٢.</b> انقر على الخريطة لتحديد أول نقطة للخط<br>
        <b>٣.</b> استمر بالنقر لإضافة نقاط على طول المسار المطلوب<br>
        <b>٤.</b> انقر <b>مرتين</b> على آخر نقطة لإنهاء الرسم<br>
        <b>٥.</b> سيظهر الطول وحقل إدخال السعر تلقائياً أسفل الخريطة<br>
        <b>٦.</b> أدخل السعر ثم اضغط <b>"احسب التكلفة"</b>
    </div>
    """, unsafe_allow_html=True)

    if st.session_state.coords_all:
        map_center2 = get_center(st.session_state.coords_all)
        map_zoom2   = 14
    else:
        map_center2 = (RIYADH_LAT, RIYADH_LON)
        map_zoom2   = DEFAULT_ZOOM

    m2 = folium.Map(
        location=list(map_center2),
        zoom_start=map_zoom2,
        tiles="OpenStreetMap",
    )
    folium.TileLayer(
        tiles="https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}",
        attr="Esri", name="صورة فضائية",
    ).add_to(m2)
    folium.TileLayer("CartoDB positron", name="خريطة فاتحة").add_to(m2)

    # Existing network
    for f in st.session_state.features:
        cll = [(c[1], c[0]) for c in f["coords"]]
        folium.PolyLine(
            cll, color="#7aadda", weight=2, opacity=0.55,
            tooltip=folium.Tooltip(f"خط #{f['index']}", sticky=True),
        ).add_to(m2)

    Draw(
        draw_options={
            "polyline": {
                "shapeOptions": {"color": "#e74c3c", "weight": 4, "opacity": 0.9},
                "metric": True,
            },
            "polygon": False, "circle": False, "rectangle": False,
            "circlemarker": False, "marker": False,
        },
        edit_options={"edit": True, "remove": True},
    ).add_to(m2)

    MeasureControl(
        primary_length_unit="meters",
        secondary_length_unit="kilometers",
        active_color="#e74c3c",
        completed_color="#c0392b",
    ).add_to(m2)
    folium.LayerControl(collapsed=False).add_to(m2)

    map2_data = st_folium(m2, width="100%", height=480, key="map2")

    # Calc drawn length
    drawn_len = 0.0
    if map2_data and map2_data.get("all_drawings"):
        for drw in map2_data["all_drawings"]:
            geom = drw.get("geometry") or {}
            if geom.get("type") == "LineString":
                c = geom.get("coordinates", [])
                if len(c) >= 2:
                    drawn_len += line_length_m(c)

    if drawn_len > 0:
        c1, c2 = st.columns(2)
        with c1:
            st.markdown(f'<div class="metric-card"><div class="val">{drawn_len:,.2f}</div><div class="lbl">طول الخط المرسوم (متر)</div></div>', unsafe_allow_html=True)
        with c2:
            st.markdown(f'<div class="metric-card"><div class="val">{drawn_len/1000:.3f}</div><div class="lbl">طول الخط المرسوم (كم)</div></div>', unsafe_allow_html=True)
        st.markdown("<br>", unsafe_allow_html=True)

        st.markdown("### 💰 احسب تكلفة الخط المرسوم")
        col_p2, col_b2 = st.columns([3, 1])
        with col_p2:
            price2 = st.number_input(
                "سعر المتر الواحد (ريال):",
                min_value=0.0, value=4004.0, step=100.0,
                format="%.2f", key="price2",
                help="أسعار إرشادية: أنابيب 4,004  |  قناة صندوقية 9,336  |  قناة مفتوحة 13,052",
            )
        with col_b2:
            st.markdown("<br>", unsafe_allow_html=True)
            calc2 = st.button("احسب التكلفة 💰", key="calc2")

        if calc2:
            cost2 = drawn_len * price2
            st.markdown(f"""
<div class="result-box">
    ✏️ خط مرسوم يدوياً على الخريطة<br><br>
    📏 الطول: <b>{drawn_len:,.2f} متر</b>  ({drawn_len/1000:.3f} كم)<br>
    💲 سعر المتر: <b>{price2:,.2f} ريال</b><br>
    ━━━━━━━━━━━━━━━━━━━━━━━<br>
    💰 التكلفة الإجمالية: <b style="font-size:1.3rem">{cost2:,.2f} ريال</b><br>
    ≈ <b>{cost2/1_000_000:.3f} مليون ريال</b>
</div>
""", unsafe_allow_html=True)
    else:
        st.markdown("""
        <div class="warn-box">
            ☝️ لم يتم رسم أي خط بعد.<br>
            استخدم أداة الرسم في يسار الخريطة لرسم خط جديد.
        </div>
        """, unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════════════════
# TAB 3 – Table
# ══════════════════════════════════════════════════════════════════════════════
with tab3:
    feats = st.session_state.features
    if not feats:
        st.markdown("""
        <div class="info-box">
            ⬅️ ارفع ملف بيانات من القائمة الجانبية لعرض الجدول.<br>
            يمكنك بعدها تحميل الجدول بصيغة CSV.
        </div>
        """, unsafe_allow_html=True)
    else:
        rows = []
        for f in feats:
            row = {
                "رقم الخط (Index)": f["index"],
                "الطول (م)":         f["length_m"],
                "الطول (كم)":        round(f["length_m"]/1000, 4),
            }
            for k, v in f["properties"].items():
                row[str(k)] = v
            rows.append(row)

        df = pd.DataFrame(rows)
        st.markdown(f"### 📋 جدول بيانات الشبكة — {len(feats)} خط")
        st.dataframe(df, use_container_width=True, height=520)

        csv_bytes = df.to_csv(index=False, encoding="utf-8-sig").encode("utf-8-sig")
        st.download_button(
            label="⬇️ تحميل الجدول (CSV)",
            data=csv_bytes,
            file_name="flood_network_data.csv",
            mime="text/csv",
        )
