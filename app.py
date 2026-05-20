import streamlit as st
import json
import math
import os
import tempfile
import zipfile
from io import StringIO, BytesIO
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

# ─── Custom CSS ────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Cairo:wght@400;600;700;900&display=swap');

html, body, [class*="css"] {
    font-family: 'Cairo', sans-serif;
    direction: rtl;
}

/* Sidebar width */
[data-testid="stSidebar"] {
    min-width: 370px !important;
    max-width: 420px !important;
    background: linear-gradient(160deg, #0a1628 0%, #0d2240 60%, #0a1628 100%);
}
[data-testid="stSidebar"] * {
    color: #e0eaff !important;
    font-family: 'Cairo', sans-serif !important;
}
[data-testid="stSidebar"] .stMarkdown h1,
[data-testid="stSidebar"] .stMarkdown h2,
[data-testid="stSidebar"] .stMarkdown h3 {
    color: #5bc8f5 !important;
}

/* Main background */
.main { background: #f0f4fa; }

/* Header */
.app-header {
    background: linear-gradient(135deg, #0a1628 0%, #1a3a6b 50%, #0d2f5e 100%);
    color: white;
    padding: 22px 30px;
    border-radius: 14px;
    margin-bottom: 18px;
    display: flex;
    align-items: center;
    justify-content: space-between;
    box-shadow: 0 6px 24px rgba(10,22,40,0.25);
}
.app-header h1 { margin: 0; font-size: 1.7rem; font-weight: 900; color: #fff; }
.app-header p  { margin: 4px 0 0; font-size: 0.95rem; color: #a8c8f0; }
.app-header .badge {
    background: #1d6fa4;
    color: #e0f4ff;
    padding: 4px 14px;
    border-radius: 20px;
    font-size: 0.8rem;
    white-space: nowrap;
}

/* Metric cards */
.metric-row { display: flex; gap: 14px; margin-bottom: 16px; flex-wrap: wrap; }
.metric-card {
    background: white;
    border-radius: 12px;
    padding: 16px 20px;
    flex: 1;
    min-width: 150px;
    box-shadow: 0 2px 12px rgba(0,0,0,0.07);
    border-top: 4px solid #1a6fbf;
    text-align: center;
}
.metric-card .val { font-size: 1.6rem; font-weight: 900; color: #0a1628; }
.metric-card .lbl { font-size: 0.82rem; color: #6b7a99; margin-top: 2px; }

/* Result box */
.result-box {
    background: linear-gradient(135deg, #0a3d62, #1a6fbf);
    color: white !important;
    padding: 20px 24px;
    border-radius: 14px;
    font-size: 1.2rem;
    font-weight: 700;
    text-align: center;
    box-shadow: 0 4px 20px rgba(26,111,191,0.35);
    margin-top: 10px;
}

/* Price reference */
.price-ref {
    background: #fff8e1;
    border-right: 4px solid #f9a825;
    border-radius: 8px;
    padding: 12px 16px;
    margin-bottom: 10px;
    font-size: 0.88rem;
    color: #5d4037;
}

/* Signature */
.signature {
    text-align: center;
    color: #8899bb;
    font-size: 0.78rem;
    padding: 10px;
    border-top: 1px solid #d0d9ee;
    margin-top: 10px;
}

/* Tab style */
.stTabs [data-baseweb="tab-list"] {
    background: #e8eef8;
    border-radius: 10px;
    padding: 4px;
    gap: 4px;
}
.stTabs [data-baseweb="tab"] {
    border-radius: 8px;
    font-family: 'Cairo', sans-serif;
    font-weight: 600;
    font-size: 0.95rem;
}
.stTabs [aria-selected="true"] {
    background: #1a6fbf !important;
    color: white !important;
}

/* Info box */
.info-box {
    background: #e3f0ff;
    border-right: 4px solid #1a6fbf;
    border-radius: 8px;
    padding: 10px 14px;
    font-size: 0.88rem;
    color: #1a3a6b;
    margin-bottom: 8px;
}

/* Stbutton */
.stButton>button {
    background: linear-gradient(135deg, #1a6fbf, #0a3d62);
    color: white;
    border: none;
    border-radius: 10px;
    padding: 10px 24px;
    font-family: 'Cairo', sans-serif;
    font-weight: 700;
    font-size: 1rem;
    width: 100%;
    cursor: pointer;
    transition: all 0.2s;
    box-shadow: 0 3px 10px rgba(26,111,191,0.3);
}
.stButton>button:hover {
    background: linear-gradient(135deg, #2280d2, #1a4a7a);
    transform: translateY(-1px);
}

/* Number input */
.stNumberInput input {
    font-family: 'Cairo', sans-serif;
    font-size: 1rem;
    text-align: center;
}

/* Multiselect */
.stMultiSelect [data-baseweb="select"] {
    font-family: 'Cairo', sans-serif;
}
</style>
""", unsafe_allow_html=True)

# ─── Helpers ───────────────────────────────────────────────────────────────────
RIYADH_LAT, RIYADH_LON = 24.7136, 46.6753

def haversine(lon1, lat1, lon2, lat2):
    R = 6371000
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)
    a = math.sin(dphi/2)**2 + math.cos(phi1)*math.cos(phi2)*math.sin(dlambda/2)**2
    return 2 * R * math.asin(math.sqrt(a))

def line_length_m(coords):
    total = 0.0
    for i in range(len(coords) - 1):
        total += haversine(coords[i][0], coords[i][1], coords[i+1][0], coords[i+1][1])
    return total

def get_center(coords_all):
    if not coords_all:
        return RIYADH_LAT, RIYADH_LON
    lats = [c[1] for c in coords_all]
    lons = [c[0] for c in coords_all]
    return sum(lats)/len(lats), sum(lons)/len(lons)

def load_geojson_data(raw_text):
    gj = json.loads(raw_text)
    features = []
    coords_all = []
    for idx, feat in enumerate(gj.get("features", [])):
        geom = feat.get("geometry", {})
        props = feat.get("properties", {}) or {}
        coords = []
        if geom.get("type") == "LineString":
            coords = geom.get("coordinates", [])
        elif geom.get("type") == "MultiLineString":
            for part in geom.get("coordinates", []):
                coords.extend(part)
        if coords:
            length = line_length_m(coords)
            features.append({
                "index": idx,
                "id_label": f"خط #{idx}",
                "length_m": round(length, 2),
                "coords": coords,
                "properties": props,
            })
            coords_all.extend(coords)
    return features, coords_all

def load_shapefile_from_zip(zip_bytes):
    """Load shapefile from zip using only built-in tools (no fiona/geopandas)."""
    try:
        import shapefile  # pyshp
    except ImportError:
        st.error("مكتبة pyshp غير متاحة. يرجى رفع ملف GeoJSON بدلاً من ذلك.")
        return None, None

    with tempfile.TemporaryDirectory() as tmpdir:
        with zipfile.ZipFile(BytesIO(zip_bytes)) as z:
            z.extractall(tmpdir)
        shp_file = None
        for f in os.listdir(tmpdir):
            if f.endswith(".shp"):
                shp_file = os.path.join(tmpdir, f)
                break
        if not shp_file:
            st.error("لم يتم العثور على ملف .shp داخل الضغط")
            return None, None

        sf = shapefile.Reader(shp_file)
        features = []
        coords_all = []
        for idx, shape_rec in enumerate(sf.shapeRecords()):
            shp = shape_rec.shape
            props = dict(zip([f[0] for f in sf.fields[1:]], shape_rec.record))
            coords = [(pt[0], pt[1]) for pt in shp.points]
            if coords:
                length = line_length_m(coords)
                features.append({
                    "index": idx,
                    "id_label": f"خط #{idx}",
                    "length_m": round(length, 2),
                    "coords": coords,
                    "properties": props,
                })
                coords_all.extend(coords)
        return features, coords_all

# ─── Session State ─────────────────────────────────────────────────────────────
if "features" not in st.session_state:
    st.session_state.features = []
if "coords_all" not in st.session_state:
    st.session_state.coords_all = []
if "drawn_length" not in st.session_state:
    st.session_state.drawn_length = 0.0

# ─── Header ────────────────────────────────────────────────────────────────────
st.markdown("""
<div class="app-header">
  <div>
    <h1>🌊 حاسبة تكلفة شبكات تصريف السيول</h1>
    <p>تحليل الشبكات • حساب الأطوال • تقدير التكاليف</p>
  </div>
  <div class="badge">Eng: Ahmed Adam</div>
</div>
""", unsafe_allow_html=True)

# ─── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("## 📂 رفع بيانات الشبكة")
    uploaded = st.file_uploader(
        "اختر ملف GeoJSON أو Shapefile (zip)",
        type=["geojson", "json", "zip"],
        help="ارفع ملف GeoJSON أو Shapefile مضغوطاً (zip يحتوي على .shp .dbf .shx)"
    )
    if uploaded:
        ext = uploaded.name.lower().split(".")[-1]
        raw = uploaded.read()
        with st.spinner("جاري تحميل البيانات..."):
            if ext in ("geojson", "json"):
                feats, ca = load_geojson_data(raw.decode("utf-8", errors="ignore"))
            else:
                feats, ca = load_shapefile_from_zip(raw)
        if feats:
            st.session_state.features = feats
            st.session_state.coords_all = ca
            st.success(f"✅ تم تحميل {len(feats)} خط بنجاح!")

    st.markdown("---")
    st.markdown("## 💲 الأسعار الإرشادية")
    st.markdown("""
<div class="price-ref">
🔵 <b>أنابيب قطر 1400 ملم</b><br>
&nbsp;&nbsp;&nbsp;سعر المتر: <b>4,004 ريال</b>
</div>
<div class="price-ref">
🟠 <b>قناة صندوقية (1.8 × 1.4 م)</b><br>
&nbsp;&nbsp;&nbsp;سعر المتر: <b>9,336 ريال</b>
</div>
<div class="price-ref">
🟢 <b>قناة مفتوحة (عرض 12م، عمق 1.5م)</b><br>
&nbsp;&nbsp;&nbsp;سعر المتر: <b>13,052 ريال</b>
</div>
""", unsafe_allow_html=True)

    st.markdown("---")
    st.markdown("""
<div class="signature">
🛠️ تطوير: <b>Eng: Ahmed Adam</b><br>
نظام تحليل شبكات تصريف السيول<br>
جميع الحقوق محفوظة © 2025
</div>
""", unsafe_allow_html=True)

# ─── Main Tabs ─────────────────────────────────────────────────────────────────
tab1, tab2, tab3 = st.tabs(["🗺️ حساب تكلفة خطوط الشبكة", "✏️ رسم خط جديد وحساب تكلفته", "📊 جدول بيانات الشبكة"])

# ══════════════════════════════════════════════════════════════════════════════
# TAB 1 – Network Lines
# ══════════════════════════════════════════════════════════════════════════════
with tab1:
    feats = st.session_state.features

    if not feats:
        st.markdown("""
<div class="info-box">
⬅️ ابدأ برفع ملف GeoJSON أو Shapefile من القائمة الجانبية.
</div>
""", unsafe_allow_html=True)

    # Metrics row
    if feats:
        total_len = sum(f["length_m"] for f in feats)
        col1, col2, col3 = st.columns(3)
        with col1:
            st.markdown(f'<div class="metric-card"><div class="val">{len(feats)}</div><div class="lbl">إجمالي الخطوط</div></div>', unsafe_allow_html=True)
        with col2:
            st.markdown(f'<div class="metric-card"><div class="val">{total_len/1000:.2f}</div><div class="lbl">إجمالي الطول (كم)</div></div>', unsafe_allow_html=True)
        with col3:
            st.markdown(f'<div class="metric-card"><div class="val">{total_len:.0f}</div><div class="lbl">إجمالي الطول (م)</div></div>', unsafe_allow_html=True)

    # Map
    center_lat = RIYADH_LAT
    center_lon = RIYADH_LON
    if st.session_state.coords_all:
        center_lat, center_lon = get_center(st.session_state.coords_all)

    m1 = folium.Map(location=[center_lat, center_lon], zoom_start=18,
                    tiles="CartoDB positron")
    folium.TileLayer("OpenStreetMap", name="خريطة شارع", show=False).add_to(m1)
    folium.TileLayer(
        tiles="https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}",
        attr="Esri", name="صورة فضائية", show=False
    ).add_to(m1)

    selected_set = set()
    for f in feats:
        coords_latlon = [(c[1], c[0]) for c in f["coords"]]
        props_txt = "<br>".join([f"<b>{k}</b>: {v}" for k, v in f["properties"].items()]) if f["properties"] else ""
        popup_html = f"""
        <div dir='rtl' style='font-family:Cairo,sans-serif;min-width:180px'>
            <b style='color:#1a6fbf;font-size:1.1em'>خط #{f['index']}</b><br>
            <b>الطول:</b> {f['length_m']:,.1f} م ({f['length_m']/1000:.3f} كم)<br>
            {props_txt}
        </div>
        """
        folium.PolyLine(
            coords_latlon,
            color="#1a6fbf", weight=3, opacity=0.85,
            tooltip=f"خط #{f['index']} | {f['length_m']:,.0f} م",
            popup=folium.Popup(popup_html, max_width=260)
        ).add_to(m1)

    folium.LayerControl().add_to(m1)
    st_folium(m1, width="100%", height=420, returned_objects=[], key="map1")

    # Line selection
    if feats:
        st.markdown("### 📌 اختر خطوطاً لحساب تكلفتها")
        st.markdown('<div class="info-box">💡 يمكنك اختيار خط واحد أو أكثر. رقم الخط يطابق رقم الـ index في الجدول.</div>', unsafe_allow_html=True)

        options = [f"{f['id_label']}  —  {f['length_m']:,.1f} م" for f in feats]
        selected_labels = st.multiselect(
            "🔍 ابحث واختر الخطوط:",
            options=options,
            placeholder="اكتب رقم الخط للبحث أو اختر من القائمة...",
            key="line_sel"
        )

        sel_indices = [options.index(s) for s in selected_labels]
        sel_feats = [feats[i] for i in sel_indices]
        total_sel_len = sum(f["length_m"] for f in sel_feats)

        if sel_feats:
            st.markdown(f'<div class="metric-card" style="text-align:center;margin:8px 0"><div class="val">{total_sel_len:,.1f} م</div><div class="lbl">مجموع أطوال الخطوط المختارة</div></div>', unsafe_allow_html=True)

            # Highlight selected lines on a separate map
            m1b = folium.Map(location=[center_lat, center_lon], zoom_start=18,
                             tiles="CartoDB positron")
            for f in feats:
                coords_latlon = [(c[1], c[0]) for c in f["coords"]]
                is_sel = f in sel_feats
                folium.PolyLine(
                    coords_latlon,
                    color="#e74c3c" if is_sel else "#aab8cc",
                    weight=5 if is_sel else 2,
                    opacity=1.0 if is_sel else 0.5,
                    tooltip=f"خط #{f['index']}",
                ).add_to(m1b)
            st_folium(m1b, width="100%", height=300, returned_objects=[], key="map1b")

        st.markdown("### 💰 احسب التكلفة")
        col_p, col_b = st.columns([3, 1])
        with col_p:
            price1 = st.number_input(
                "سعر المتر الواحد (ريال):",
                min_value=0.0, value=4004.0, step=100.0,
                format="%.2f", key="price1",
                help="أسعار إرشادية: أنابيب 4004 | قناة صندوقية 9336 | قناة مفتوحة 13052"
            )
        with col_b:
            st.markdown("<br>", unsafe_allow_html=True)
            calc1 = st.button("احسب التكلفة 💰", key="calc1")

        if calc1:
            if not sel_feats:
                st.warning("⚠️ الرجاء اختيار خط واحد على الأقل.")
            else:
                total_cost = total_sel_len * price1
                lines_info = " | ".join([f"خط #{f['index']} ({f['length_m']:,.0f}م)" for f in sel_feats])
                st.markdown(f"""
<div class="result-box">
    📏 الخطوط المختارة: {lines_info}<br>
    مجموع الأطوال: <b>{total_sel_len:,.2f} م</b> ({total_sel_len/1000:.3f} كم)<br>
    سعر المتر: <b>{price1:,.2f} ريال</b><br>
    ━━━━━━━━━━━━━━━━━<br>
    💰 التكلفة الإجمالية: <b>{total_cost:,.2f} ريال</b><br>
    ≈ <b>{total_cost/1_000_000:.3f} مليون ريال</b>
</div>
""", unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════════════════
# TAB 2 – Draw New Line
# ══════════════════════════════════════════════════════════════════════════════
with tab2:
    st.markdown("### ✏️ ارسم خطاً على الخريطة وقيس طوله")
    st.markdown("""
<div class="info-box">
📌 <b>تعليمات الرسم:</b><br>
1. انقر على أيقونة <b>الخط</b> في شريط الأدوات (يسار الخريطة)<br>
2. انقر على الخريطة لتحديد نقاط الخط<br>
3. انقر <b>مرتين</b> لإنهاء الرسم<br>
4. ستظهر النتيجة تلقائياً أدناه
</div>
""", unsafe_allow_html=True)

    center_lat2 = RIYADH_LAT
    center_lon2 = RIYADH_LON
    if st.session_state.coords_all:
        center_lat2, center_lon2 = get_center(st.session_state.coords_all)

    m2 = folium.Map(location=[center_lat2, center_lon2], zoom_start=18,
                    tiles="CartoDB positron")
    folium.TileLayer("OpenStreetMap", name="خريطة شارع", show=False).add_to(m2)
    folium.TileLayer(
        tiles="https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}",
        attr="Esri", name="صورة فضائية", show=False
    ).add_to(m2)

    # Draw existing network lightly
    for f in st.session_state.features:
        coords_latlon = [(c[1], c[0]) for c in f["coords"]]
        folium.PolyLine(coords_latlon, color="#aab8cc", weight=2, opacity=0.5,
                        tooltip=f"خط #{f['index']}").add_to(m2)

    draw = Draw(
        draw_options={
            "polyline": {"shapeOptions": {"color": "#e74c3c", "weight": 4}},
            "polygon": False, "circle": False, "rectangle": False,
            "circlemarker": False, "marker": False,
        },
        edit_options={"edit": True, "remove": True}
    )
    draw.add_to(m2)
    MeasureControl(primary_length_unit="meters", secondary_length_unit="kilometers").add_to(m2)
    folium.LayerControl().add_to(m2)

    map2_data = st_folium(m2, width="100%", height=480, key="map2")

    # Extract drawn line
    drawn_len = 0.0
    drawn_coords = []
    if map2_data and map2_data.get("all_drawings"):
        drawings = map2_data["all_drawings"]
        for drw in drawings:
            geom = drw.get("geometry", {})
            if geom.get("type") == "LineString":
                c = geom.get("coordinates", [])
                if len(c) >= 2:
                    drawn_coords = c
                    drawn_len += line_length_m(c)

    if drawn_len > 0:
        st.markdown(f'<div class="metric-card" style="margin:8px 0"><div class="val">{drawn_len:,.2f} م</div><div class="lbl">طول الخط المرسوم ({drawn_len/1000:.3f} كم)</div></div>', unsafe_allow_html=True)

        col_p2, col_b2 = st.columns([3, 1])
        with col_p2:
            price2 = st.number_input(
                "سعر المتر الواحد (ريال):",
                min_value=0.0, value=4004.0, step=100.0,
                format="%.2f", key="price2",
                help="أسعار إرشادية: أنابيب 4004 | قناة صندوقية 9336 | قناة مفتوحة 13052"
            )
        with col_b2:
            st.markdown("<br>", unsafe_allow_html=True)
            calc2 = st.button("احسب التكلفة 💰", key="calc2")

        if calc2:
            total_cost2 = drawn_len * price2
            st.markdown(f"""
<div class="result-box">
    ✏️ خط مرسوم يدوياً<br>
    الطول: <b>{drawn_len:,.2f} م</b> ({drawn_len/1000:.3f} كم)<br>
    سعر المتر: <b>{price2:,.2f} ريال</b><br>
    ━━━━━━━━━━━━━━━━━<br>
    💰 التكلفة الإجمالية: <b>{total_cost2:,.2f} ريال</b><br>
    ≈ <b>{total_cost2/1_000_000:.3f} مليون ريال</b>
</div>
""", unsafe_allow_html=True)
    else:
        st.markdown('<div class="info-box">⬆️ ارسم خطاً على الخريطة لتظهر نتائج الطول والتكلفة هنا.</div>', unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════════════════
# TAB 3 – Data Table
# ══════════════════════════════════════════════════════════════════════════════
with tab3:
    feats = st.session_state.features
    if not feats:
        st.markdown('<div class="info-box">⬅️ ارفع ملف بيانات من القائمة الجانبية لعرض الجدول.</div>', unsafe_allow_html=True)
    else:
        rows = []
        for f in feats:
            row = {"رقم الخط (Index)": f["index"], "الطول (م)": f["length_m"], "الطول (كم)": round(f["length_m"]/1000, 3)}
            row.update(f["properties"])
            rows.append(row)
        df = pd.DataFrame(rows)
        st.markdown(f"### 📋 جدول بيانات الشبكة ({len(feats)} خط)")
        st.dataframe(df, use_container_width=True, height=500)

        csv = df.to_csv(index=False, encoding="utf-8-sig")
        st.download_button(
            "⬇️ تحميل الجدول (CSV)",
            data=csv.encode("utf-8-sig"),
            file_name="flood_network_data.csv",
            mime="text/csv"
        )
