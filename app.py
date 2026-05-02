import streamlit as st
import pandas as pd
import os
from datetime import datetime
from io import BytesIO

# ================== إعدادات الصفحة ==================
st.set_page_config(page_title="تحديث مدفوعات اتصالات", layout="wide")

st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Tajawal:wght@400;700&display=swap');
    body, div, h1, p, span, .stMetric { font-family: 'Tajawal', sans-serif; direction: rtl; text-align: right; }
    .stMetric { background-color: #ffffff; border: 2px solid #1a237e; border-radius: 15px; padding: 20px; box-shadow: 0 4px 8px rgba(0,0,0,0.05); }
</style>
""", unsafe_allow_html=True)

# ================== إدارة البيانات ==================
DB_FILE = "database.xlsx"

def load_data():
    if os.path.exists(DB_FILE):
        df = pd.read_excel(DB_FILE)
        # توحيد نوع رقم الحساب لضمان الربط الصحيح
        df["Account No."] = df["Account No."].astype(str)
        # إنشاء عمود النظام السابق إذا لم يوجد
        if "previous_system" not in df.columns:
            df["previous_system"] = df["system"].copy()
        return df
    return pd.DataFrame()

df = load_data()

if not df.empty:
    st.title("📊 نظام تحديث التحصيل الدوري")
    
    # 1. إدخال المبالغ الجديدة (الشاشة التي تستخدمينها)
    st.subheader("✍️ إدخال المبالغ الحالية من تطبيق OPay")
    
    # تحضير جدول التعديل
    edit_df = df[["Account No.", "Spoc", "system", "previous_system"]].copy()
    
    edited_data = st.data_editor(
        edit_df,
        use_container_width=True,
        hide_index=True,
        column_config={
            "Account No.": "رقم الحساب",
            "Spoc": "الجهة",
            "system": st.column_config.NumberColumn("المبلغ الحالي (System)", format="%.2f"),
            "previous_system": st.column_config.NumberColumn("المبلغ السابق", disabled=True)
        }
    )

    if st.button("🚀 تحديث وحساب التحصيلات"):
        # تحديث قيم السيستم في الـ DataFrame الأصلي
        updates = edited_data.set_index("Account No.")["system"].to_dict()
        df["system"] = df["Account No."].map(updates).fillna(df["system"])
        
        # 2. الحسابات الذكية (تطبيق شروطك الخاصة)
        # حساب مدفوعات اليوم (مع استبعاد الحساب المستثنى والـ NonPayment)
        def calculate_daily_payment(row):
            # استبعاد الحساب رقم 6.133531.7572 أو أي NonPayment
            if row["Account No."] == "6.133531.7572" or row["Type"] == "NonPayment":
                return 0
            return max(0, row["previous_system"] - row["system"])

        df["مدفوعات اليوم"] = df.apply(calculate_daily_payment, axis=1)
        
        # حساب مستحق الدفع (الفاتورة - السيستم)[cite: 1]
        df["مستحق الدفع"] = df["Invoice_April_2026"] - df["system"]

        # 3. عرض الكروت (Metrics) كما في الصورة[cite: 1]
        c1, c2, c3 = st.columns(3)
        with c1:
            st.metric("إجمالي التحصيل اللحظي", f"{df['مدفوعات اليوم'].sum():,.2f} ج.م")
        with c2:
            st.metric("إجمالي المتبقي", f"{df['system'].sum():,.2f} ج.م")
        with c3:
            # عد العمليات التي حدث فيها دفع فعلي[cite: 1]
            active_payments = len(df[df['مدفوعات اليوم'] > 0])
            st.metric("عدد العمليات", active_payments)

        st.markdown("---")
        
        # 4. التقرير النهائي (بالتنسيق والمسميات المطلوبة للجروب)[cite: 1]
        st.subheader("📋 التقرير النهائي (تنسيق العرض)")
        
        report_display = df.copy()
        # إعادة تسمية الأعمدة لتطابق التقرير المطلوب[cite: 1]
        report_display = report_display.rename(columns={
            "Account No.": "Account No.",
            "Spoc": "Spoc",
            "Mobile": "Phone Sub Account",
            "Invoice_April_2026": "الفاتورة الصادرة ابريل ٢٠٢٦",
            "system": "System",
            "مستحق الدفع": "مستحق الدفع",
            "مدفوعات اليوم": "مدفوعات اليوم"
        })
        
        # اختيار الأعمدة بالترتيب الذي ظهر في صورتك[cite: 1]
        final_cols = ["Account No.", "Spoc", "Phone Sub Account", "الفاتورة الصادرة ابريل ٢٠٢٦", "System", "مستحق الدفع", "مدفوعات اليوم"]
        st.dataframe(report_display[final_cols].style.format(precision=2), use_container_width=True, hide_index=True)

        # 5. حفظ وترحيل البيانات[cite: 1]
        df["previous_system"] = df["system"] # السيستم الحالي يصبح سابقاً للمرة القادمة[cite: 1]
        
        output = BytesIO()
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            df.to_excel(writer, index=False)
        
        st.success("✅ تم تحديث البيانات بنجاح.")
        st.download_button(
            "📥 تحميل ملف قاعدة البيانات المحدث (database.xlsx)",
            data=output.getvalue(),
            file_name="database.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
else:
    st.error("تأكدي من رفع ملف database.xlsx في المسار الصحيح.")
