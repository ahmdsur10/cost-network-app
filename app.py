import streamlit as st
import json, math, os, tempfile, zipfile
from io import BytesIO
import folium
from folium.plugins import Draw
from streamlit_folium import st_folium
import pandas as pd

st.set_page_config(page_title="حاسبة شبكات السيول", page_icon="🌊",
                   layout="wide", initial_sidebar_state="expanded")

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Cairo:wght@400;700;900&display=swap');
html,body,[class*="css"],.stApp{font-family:'Cairo',sans-serif!important;direction:rtl}
[data-testid="stSidebar"]{min-width:340px!important;max-width:380px!important;background:#f7f9fc!important}
.hdr{background:linear-gradient(135deg,#0a2a5e,#1a5fa8);color:#fff;padding:16px 22px;border-radius:12px;margin-bottom:14px;display:flex;align-items:center;justify-content:space-between}
.hdr h1{margin:0;font-size:1.35rem;font-weight:900}
.hdr p{margin:2px 0 0;font-size:.82rem;color:#b8d9f8}
.hdr .bdg{background:rgba(255,255,255,.18);border:1px solid rgba(255,255,255,.3);padding:5px 14px;border-radius:16px;font-size:.78rem;font-weight:700;white-space:nowrap}
.mc{background:#fff;border-radius:10px;padding:12px 16px;box-shadow:0 2px 8px rgba(0,0,0,.07);border-top:4px solid #1a5fa8;text-align:center}
.mc .v{font-size:1.45rem;font-weight:900;color:#0a2a5e}
.mc .l{font-size:.78rem;color:#6b7a99;margin-top:2px}
.res{background:linear-gradient(135deg,#0a2a5e,#1a5fa8);color:#fff!important;padding:18px 22px;border-radius:12px;font-size:1.05rem;font-weight:700;text-align:center;box-shadow:0 4px 16px rgba(26,95,168,.3);margin-top:10px;line-height:2}
.ib{background:#eaf4ff;border-right:4px solid #1a5fa8;border-radius:7px;padding:10px 14px;font-size:.85rem;color:#0a2a5e;margin-bottom:8px;direction:rtl;line-height:1.8}
.pc{background:#fff;border:1.5px solid #d0e4f7;border-right:5px solid #1a5fa8;border-radius:7px;padding:9px 13px;margin-bottom:7px;font-size:.84rem;color:#1a2a3a}
.pc b{color:#0a2a5e}.pc small{color:#888}.pc span{color:#c0392b;font-weight:900;font-size:.9rem}
.sig{background:#0a2a5e;color:#a8d0f0!important;text-align:center;padding:10px;border-radius:8px;margin-top:12px;font-size:.8rem}
.sig b{color:#fff!important}
.stButton>button{background:linear-gradient(135deg,#1a5fa8,#0a2a5e)!important;color:#fff!important;border:none!important;border-radius:9px!important;font-family:'Cairo',sans-serif!important;font-weight:700!important;font-size:.95rem!important;width:100%!important;padding:9px!important}
</style>
""", unsafe_allow_html=True)

RLAT, RLON = 24.7136, 46.6753

def hav(lon1,lat1,lon2,lat2):
    R=6371000; p1,p2=math.radians(lat1),math.radians(lat2)
    dp=math.radians(lat2-lat1); dl=math.radians(lon2-lon1)
    a=math.sin(dp/2)**2+math.cos(p1)*math.cos(p2)*math.sin(dl/2)**2
    return 2*R*math.asin(math.sqrt(a))

def length_m(coords):
    t=0.0
    for i in range(len(coords)-1):
        try: t+=hav(float(coords[i][0]),float(coords[i][1]),float(coords[i+1][0]),float(coords[i+1][1]))
        except: pass
    return t

def center(coords):
    v=[(float(c[0]),float(c[1])) for c in coords if len(c)>=2]
    if not v: return RLAT,RLON
    return sum(c[1] for c in v)/len(v), sum(c[0] for c in v)/len(v)

def parse_geom(geom):
    if not geom: return []
    t=geom.get("type",""); raw=geom.get("coordinates",[])
    pts = raw if t=="LineString" else [p for part in raw for p in part] if t=="MultiLineString" else []
    return [[float(c[0]),float(c[1])] for c in pts if isinstance(c,(list,tuple)) and len(c)>=2]

def load_geojson(text):
    try: gj=json.loads(text)
    except: st.error("خطأ في قراءة الملف"); return [],[]
    feats,all_c=[],[]
    for i,f in enumerate(gj.get("features",[])):
        if not isinstance(f,dict): continue
        coords=parse_geom(f.get("geometry") or {})
        if len(coords)<2: continue
        props=f.get("properties") or {}
        feats.append({"i":i,"lbl":f"خط #{i}","len":round(length_m(coords),2),"coords":coords,"props":props})
        all_c.extend(coords)
    return feats,all_c

def load_shp(zb):
    try: import shapefile
    except: st.error("مكتبة pyshp غير متاحة"); return [],[]
    try:
        with tempfile.TemporaryDirectory() as td:
            with zipfile.ZipFile(BytesIO(zb)) as z: z.extractall(td)
            shp=next((os.path.join(r,f) for r,_,fs in os.walk(td) for f in fs if f.lower().endswith(".shp")),None)
            if not shp: st.error("لم يُعثر على .shp"); return [],[]
            sf=shapefile.Reader(shp); fnames=[f[0] for f in sf.fields[1:]]
            feats,all_c=[],[]
            for i,sr in enumerate(sf.shapeRecords()):
                coords=[[float(p[0]),float(p[1])] for p in sr.shape.points if len(p)>=2]
                if len(coords)<2: continue
                props=dict(zip(fnames,sr.record))
                feats.append({"i":i,"lbl":f"خط #{i}","len":round(length_m(coords),2),"coords":coords,"props":props})
                all_c.extend(coords)
            return feats,all_c
    except Exception as e: st.error(f"خطأ: {e}"); return [],[]

# ── Session ──
for k,v in [("feats",[]),("ac",[])]:
    if k not in st.session_state: st.session_state[k]=v

# ── Sidebar ──
with st.sidebar:
    st.markdown('<div style="background:linear-gradient(135deg,#0a2a5e,#1a5fa8);color:#fff;padding:14px 18px;text-align:center;margin:-1px -1px 14px"><b style="font-size:1rem">🌊 حاسبة شبكات السيول</b><br><small style="color:#b8d9f8">Eng. Ahmed Adam</small></div>', unsafe_allow_html=True)

    st.markdown("**📂 رفع بيانات الشبكة**")
    up=st.file_uploader("GeoJSON أو Shapefile (zip)", type=["geojson","json","zip"], label_visibility="collapsed")
    if up:
        raw=up.read(); ext=up.name.lower().rsplit(".",1)[-1]
        with st.spinner("جاري التحميل..."):
            if ext in("geojson","json"): f,c=load_geojson(raw.decode("utf-8","ignore"))
            else: f,c=load_shp(raw)
        if f:
            st.session_state.feats=f; st.session_state.ac=c
            st.success(f"✅ {len(f)} خط")
        else:
            st.warning("لم تُوجد خطوط صالحة في الملف")

    if st.session_state.feats:
        tl=sum(x["len"] for x in st.session_state.feats)
        st.caption(f"📊 {len(st.session_state.feats)} خط — إجمالي {tl/1000:.2f} كم")

    st.markdown("---")
    st.markdown("**💲 أسعار إرشادية**")
    st.markdown("""
<div class="pc"><b>🔵 أنابيب — قطر 1400 ملم</b><br><span>4,004 ريال / متر</span></div>
<div class="pc"><b>🟠 قناة صندوقية — 1.8 × 1.4 م</b><br><span>9,336 ريال / متر</span></div>
<div class="pc"><b>🟢 قناة مفتوحة — عرض 12م / عمق 1.5م</b><br><span>13,052 ريال / متر</span></div>
<div class="sig"><b>Eng: Ahmed Adam</b><br>شبكات تصريف السيول © 2025</div>
""", unsafe_allow_html=True)

# ── Header ──
st.markdown("""
<div class="hdr">
  <div><h1>🌊 حاسبة تكلفة شبكات تصريف السيول</h1>
  <p>تحليل الشبكات · حساب الأطوال · تقدير التكاليف</p></div>
  <div class="bdg">Eng: Ahmed Adam</div>
</div>""", unsafe_allow_html=True)

tab1,tab2,tab3=st.tabs(["🗺️ خطوط الشبكة","✏️ رسم خط جديد","📊 جدول البيانات"])

# ══ TAB 1 ══
with tab1:
    feats=st.session_state.feats
    if not feats:
        st.markdown('<div class="ib">⬅️ ارفع ملف GeoJSON أو Shapefile من القائمة الجانبية للبدء.</div>', unsafe_allow_html=True)

    if feats:
        tl=sum(x["len"] for x in feats)
        c1,c2,c3=st.columns(3)
        c1.markdown(f'<div class="mc"><div class="v">{len(feats):,}</div><div class="l">عدد الخطوط</div></div>',unsafe_allow_html=True)
        c2.markdown(f'<div class="mc"><div class="v">{tl/1000:,.2f}</div><div class="l">إجمالي الطول (كم)</div></div>',unsafe_allow_html=True)
        c3.markdown(f'<div class="mc"><div class="v">{tl:,.0f}</div><div class="l">إجمالي الطول (م)</div></div>',unsafe_allow_html=True)
        st.markdown("<br>",unsafe_allow_html=True)

    # Map — بدون highlight ثانية لتسريع التحميل
    mc=list(center(st.session_state.ac)) if st.session_state.ac else [RLAT,RLON]
    mz=14 if st.session_state.ac else 14
    m1=folium.Map(location=mc,zoom_start=mz,tiles="OpenStreetMap",
                  prefer_canvas=True)   # prefer_canvas يسرّع رسم الخطوط
    folium.TileLayer(
        "https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}",
        attr="Esri",name="صورة فضائية").add_to(m1)
    folium.LayerControl(collapsed=True).add_to(m1)

    for f in feats:
        cll=[(c[1],c[0]) for c in f["coords"]]
        props_rows="".join(f"<tr><td style='color:#666;padding:1px 5px'>{k}</td><td style='font-weight:600;padding:1px 5px'>{v}</td></tr>"
                           for k,v in f["props"].items() if v not in(None,"","None"))
        popup=f"<div dir='rtl' style='font-family:Cairo,sans-serif;font-size:13px;min-width:180px'><b style='color:#1a5fa8'>خط #{f['i']}</b><br><b>الطول:</b> {f['len']:,.1f} م ({f['len']/1000:.3f} كم){'<table>'+props_rows+'</table>' if props_rows else ''}</div>"
        folium.PolyLine(cll,color="#1a5fa8",weight=3,opacity=.85,
                        tooltip=f"خط #{f['i']} | {f['len']:,.0f} م",
                        popup=folium.Popup(popup,max_width=260)).add_to(m1)

    st_folium(m1,width="100%",height=400,returned_objects=[],key="m1")

    if feats:
        st.markdown("### 📌 اختر الخطوط")
        st.markdown('<div class="ib">💡 اختر خطاً أو أكثر — رقم الخط مطابق لـ Index في الجدول والـ Popup</div>',unsafe_allow_html=True)
        opts=[f"خط #{f['i']}  ——  {f['len']:,.1f} م" for f in feats]
        sel=st.multiselect("ابحث واختر:",opts,placeholder="اكتب رقم الخط أو اختر...",key="sel1")
        sidx=[opts.index(s) for s in sel]
        sfeats=[feats[i] for i in sidx]
        stot=sum(x["len"] for x in sfeats)

        if sfeats:
            c1,c2=st.columns(2)
            c1.markdown(f'<div class="mc"><div class="v">{len(sfeats)}</div><div class="l">خطوط مختارة</div></div>',unsafe_allow_html=True)
            c2.markdown(f'<div class="mc"><div class="v">{stot:,.1f} م</div><div class="l">مجموع الأطوال</div></div>',unsafe_allow_html=True)
            st.markdown("<br>",unsafe_allow_html=True)

        st.markdown("### 💰 حساب التكلفة")
        cp,cb=st.columns([3,1])
        with cp:
            pr1=st.number_input("سعر المتر (ريال):",min_value=0.0,value=4004.0,
                                step=100.0,format="%.2f",key="pr1",
                                help="إرشادية: أنابيب 4,004 | صندوقية 9,336 | مفتوحة 13,052")
        with cb:
            st.markdown("<br>",unsafe_allow_html=True)
            if st.button("احسب 💰",key="b1"):
                if not sfeats:
                    st.warning("اختر خطاً أولاً")
                else:
                    cost=stot*pr1
                    info=" | ".join(f"خط #{f['i']} ({f['len']:,.0f}م)" for f in sfeats)
                    st.markdown(f"""<div class="res">
{info}<br>📏 مجموع الأطوال: <b>{stot:,.2f} م</b> ({stot/1000:.3f} كم)<br>
💲 سعر المتر: <b>{pr1:,.2f} ريال</b><br>━━━━━━━━━━━━━━━━━<br>
💰 التكلفة الإجمالية: <b style="font-size:1.25rem">{cost:,.2f} ريال</b><br>
≈ <b>{cost/1e6:.3f} مليون ريال</b></div>""",unsafe_allow_html=True)

# ══ TAB 2 ══
with tab2:
    st.markdown("### ✏️ ارسم خطاً على الخريطة")
    st.markdown("""<div class="ib" style="text-align:right">
<b>📌 خطوات الرسم:</b><br>
<b>١.</b> انقر أيقونة <b>رسم الخط</b> في يسار الخريطة<br>
<b>٢.</b> انقر لتحديد نقاط المسار<br>
<b>٣.</b> انقر <b>مرتين</b> لإنهاء الرسم<br>
<b>٤.</b> أدخل السعر ثم اضغط احسب
</div>""",unsafe_allow_html=True)

    mc2=list(center(st.session_state.ac)) if st.session_state.ac else [RLAT,RLON]
    m2=folium.Map(location=mc2,zoom_start=14,tiles="OpenStreetMap",prefer_canvas=True)
    folium.TileLayer(
        "https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}",
        attr="Esri",name="صورة فضائية").add_to(m2)

    for f in st.session_state.feats:
        folium.PolyLine([(c[1],c[0]) for c in f["coords"]],
                        color="#7aadda",weight=2,opacity=.5,
                        tooltip=f"خط #{f['i']}").add_to(m2)

    Draw(draw_options={
        "polyline":{"shapeOptions":{"color":"#e74c3c","weight":4,"opacity":.9}},
        "polygon":False,"circle":False,"rectangle":False,
        "circlemarker":False,"marker":False},
        edit_options={"edit":True,"remove":True}).add_to(m2)
    folium.LayerControl(collapsed=True).add_to(m2)

    md2=st_folium(m2,width="100%",height=460,key="m2")

    dlen=0.0
    if md2 and md2.get("all_drawings"):
        for drw in md2["all_drawings"]:
            g=drw.get("geometry") or {}
            if g.get("type")=="LineString":
                c=g.get("coordinates",[])
                if len(c)>=2: dlen+=length_m(c)

    if dlen>0:
        c1,c2=st.columns(2)
        c1.markdown(f'<div class="mc"><div class="v">{dlen:,.2f}</div><div class="l">الطول (م)</div></div>',unsafe_allow_html=True)
        c2.markdown(f'<div class="mc"><div class="v">{dlen/1000:.3f}</div><div class="l">الطول (كم)</div></div>',unsafe_allow_html=True)
        st.markdown("<br>",unsafe_allow_html=True)

        cp2,cb2=st.columns([3,1])
        with cp2:
            pr2=st.number_input("سعر المتر (ريال):",min_value=0.0,value=4004.0,
                                step=100.0,format="%.2f",key="pr2",
                                help="إرشادية: أنابيب 4,004 | صندوقية 9,336 | مفتوحة 13,052")
        with cb2:
            st.markdown("<br>",unsafe_allow_html=True)
            if st.button("احسب 💰",key="b2"):
                cost2=dlen*pr2
                st.markdown(f"""<div class="res">
✏️ خط مرسوم يدوياً<br>📏 الطول: <b>{dlen:,.2f} م</b> ({dlen/1000:.3f} كم)<br>
💲 سعر المتر: <b>{pr2:,.2f} ريال</b><br>━━━━━━━━━━━━━━━━━<br>
💰 التكلفة: <b style="font-size:1.25rem">{cost2:,.2f} ريال</b><br>
≈ <b>{cost2/1e6:.3f} مليون ريال</b></div>""",unsafe_allow_html=True)
    else:
        st.markdown('<div class="ib">☝️ استخدم أداة الرسم في يسار الخريطة لرسم خط جديد.</div>',unsafe_allow_html=True)

# ══ TAB 3 ══
with tab3:
    feats=st.session_state.feats
    if not feats:
        st.markdown('<div class="ib">⬅️ ارفع ملف من القائمة الجانبية لعرض الجدول.</div>',unsafe_allow_html=True)
    else:
        rows=[]
        for f in feats:
            r={"رقم الخط":f["i"],"الطول (م)":f["len"],"الطول (كم)":round(f["len"]/1000,4)}
            r.update({str(k):v for k,v in f["props"].items()})
            rows.append(r)
        df=pd.DataFrame(rows)
        st.markdown(f"### 📋 بيانات الشبكة — {len(feats)} خط")
        st.dataframe(df,use_container_width=True,height=500)
        st.download_button("⬇️ تحميل CSV",
            df.to_csv(index=False,encoding="utf-8-sig").encode("utf-8-sig"),
            "flood_network.csv","text/csv")
