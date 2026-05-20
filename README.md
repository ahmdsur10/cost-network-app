# 🌊 حاسبة تكلفة شبكات تصريف السيول

**تطوير: Eng. Ahmed Adam**

تطبيق ويب لتحليل شبكات تصريف السيول وحساب تكاليف التنفيذ.

---

## 🚀 خطوات النشر على Streamlit Cloud

### 1. إنشاء مستودع GitHub

```bash
# إنشاء مجلد المشروع
mkdir flood-network-app
cd flood-network-app

# نسخ الملفات إليه
# app.py
# requirements.txt
# README.md
# sample_data.geojson

# تهيئة Git
git init
git add .
git commit -m "Initial commit - Flood Network Cost Calculator"
```

### 2. رفع على GitHub

1. اذهب إلى https://github.com وسجّل الدخول
2. انقر **New repository**
3. اسم المستودع: `flood-network-app`
4. اتركه **Public**
5. انقر **Create repository**
6. نفّذ:

```bash
git remote add origin https://github.com/YOUR_USERNAME/flood-network-app.git
git branch -M main
git push -u origin main
```

### 3. النشر على Streamlit Cloud

1. اذهب إلى https://share.streamlit.io
2. سجّل الدخول بحساب GitHub
3. انقر **New app**
4. اختر:
   - **Repository**: `YOUR_USERNAME/flood-network-app`
   - **Branch**: `main`
   - **Main file path**: `app.py`
5. انقر **Deploy!**

✅ سيكون تطبيقك متاحاً على:
`https://YOUR_USERNAME-flood-network-app-app-XXXXX.streamlit.app`

---

## 📦 المكتبات المستخدمة

| المكتبة | الاستخدام | ملاحظة |
|---------|-----------|--------|
| `streamlit` | واجهة التطبيق | ✅ مدعومة |
| `folium` | الخرائط التفاعلية | ✅ مدعومة |
| `streamlit-folium` | دمج Folium مع Streamlit | ✅ مدعومة |
| `pandas` | جداول البيانات | ✅ مدعومة |
| `pyshp` | قراءة Shapefile | ✅ خفيفة وبدون Fiona |

> ⚠️ **مهم**: لا نستخدم `geopandas` أو `fiona` أو `gdal` لأنها تسبب مشاكل في النشر.

---

## 📁 هيكل الملفات

```
flood-network-app/
├── app.py              # التطبيق الرئيسي
├── requirements.txt    # المكتبات المطلوبة
├── README.md           # هذا الملف
└── sample_data.geojson # بيانات تجريبية
```

---

## 💡 الأسعار الإرشادية

| النوع | المواصفات | سعر المتر (ريال) |
|-------|-----------|-----------------|
| أنابيب | قطر 1400 ملم | 4,004 |
| قناة صندوقية | 1.8 × 1.4 م | 9,336 |
| قناة مفتوحة | عرض 12م، عمق 1.5م | 13,052 |

---

## 🔧 تشغيل محلياً

```bash
pip install -r requirements.txt
streamlit run app.py
```

---

*جميع الحقوق محفوظة © 2025 - Eng: Ahmed Adam*
