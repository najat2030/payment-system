import streamlit as st
import pandas as pd
import os
from datetime import datetime
from io import BytesIO

# ================== إعدادات الصفحة والثيم ==================
st.set_page_config(
    page_title="تحديث مدفوعات اتصالات",
    page_icon="📊",
    layout="wide"
)

# ألوان احترافية (أزرق داكن ملكي)
PRIMARY_COLOR = "#1a237e"

st.markdown(f"""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Tajawal:wght@400;500;700&display=swap');
    .main {{ background-color: #ffffff; font-family: 'Tajawal', sans-serif; direction: rtl; }}
    .dashboard-header {{ 
        background: linear-gradient(135deg, {PRIMARY_COLOR} 0%, #283593 100%); 
        color: white; padding: 25px; border-radius: 15px; margin-bottom: 25px; text-align: center;
    }}
    div[data-testid="stMetric"] {{ 
        background-color: white; padding: 20px; border-radius: 12px; 
        box-shadow: 0 4px 8px rgba(0,0,0,0.05); border-top: 4px solid {PRIMARY_COLOR}; text-align: center;
    }}
</style>
""", unsafe_allow_html=True)

# ================== إدارة البيانات ==================
DB_FILE = "database.xlsx"

def load_data():
    if os.path.exists(DB_FILE):
        try:
            df = pd.read_excel(DB_FILE)
            # التأكد من تحويل أرقام الحسابات لنصوص لضمان دقة الربط
            df["Account No."] = df["Account No."].astype(str)
            # إنشاء عمود النظام السابق إذا لم يكن موجوداً
            if "previous_system" not in df.columns:
                df["previous_system"] = df["system"].copy()
            return df
        except Exception as e:
            st.error(f"❌ خطأ في قراءة ملف البيانات: {e}")
            return pd.DataFrame()
    return pd.DataFrame()

# ================== واجهة المستخدم الرئيسية ==================
df = load_data()

if not df.empty:
    current_time = datetime.now().strftime('%Y-%m-%d %H:%M')
    st.markdown(f"""
    <div class="dashboard-header">
        <h1>نظام تحديث التحصيل الدوري - April 2026</h1>
        <p>آخر تحديث للنظام: {current_time}</p>
    </div>
    """, unsafe_allow_html=True)

    st.subheader("✍️ إدخال قيم System من تطبيق OPay")
    
    # الجدول القابل للتعديل (نسخة من جدولك الأصلي)
    # نعرض الأعمدة الأساسية فقط لتجنب لخبطة العرض
    editable_df = df[["Account No.", "Spoc", "system", "previous_system"]].copy()
    
    edited_df = st.data_editor(
        editable_df,
        use_container_width=True,
        hide_index=True,
        column_config={
            "system": st.column_config.NumberColumn("المبلغ على النظام (System) - الجديد", format="%.2f"),
            "previous_system": st.column_config.NumberColumn("المبلغ على النظام (System) - السابق", disabled=True),
            "Account No.": st.column_config.TextColumn("رقم الحساب", disabled=True),
            "Spoc": st.column_config.TextColumn("اسم العميل", disabled=True)
        }
    )

    if st.button("🚀 تحديث النظام وحساب المدفوعات"):
        # حل مشكلة الـ KeyError باستخدام الـ Mapping بدلاً من الـ Merge
        updated_df = df.copy()
        system_updates = edited_df.set_index("Account No.")["system"].to_dict()
        updated_df["system"] = updated_df["Account No."].map(system_updates).fillna(updated_df["system"])

        # الحسابات التلقائية بناءً على شروطك
        # 1. حساب مدفوعات اليوم مع استثناء الحساب الخاص
        def calc_daily_pay(row):
            # استثناء حساب المديونية القديمة والحسابات من نوع NonPayment[cite: 1]
            if str(row["Account No."]) == "6.133531.7572" or row["Type"] == "NonPayment":
                return 0
            return max(0, row["previous_system"] - row["system"])

        updated_df["مدفوعات اليوم"] = updated_df.apply(calc_daily_pay, axis=1)

        # 2. حساب متبقي للدفع (الفاتورة - النظام الحالي)[cite: 1]
        updated_df["Remaining_Due"] = updated_df["Invoice_April_2026"] - updated_df["system"]

        # عرض المقاييس (Metrics) بنفس الشكل المطلوب[cite: 1]
        c1, c2, c3 = st.columns(3)
        with c1:
            st.metric(label="إجمالي التحصيل اللحظي", value=f"{updated_df['مدفوعات اليوم'].sum():,.2f} ج.م")
        with c2:
            st.metric(label="إجمالي المتبقي", value=f"{updated_df['system'].sum():,.2f} ج.م")
        with c3:
            st.metric(label="عدد العمليات", value=len(updated_df[updated_df['مدفوعات اليوم'] > 0]))

        st.markdown("---")
        st.subheader("📋 تفاصيل التقرير النهائي")
        
        # عرض الجدول النهائي بنفس ترتيب الأعمدة في صورتك[cite: 1]
        # (رقم الحساب، Spoc، رقم الهاتف، الفاتورة، System، متبقي للدفع، مدفوعات اليوم)[cite: 1]
        display_report = updated_df.copy()
        display_report = display_report.rename(columns={
            "Mobile": "Phone Sub Account",
            "Invoice_April_2026": "الفاتورة الصادرة ابريل ٢٠٢٦",
            "system": "System",
            "Remaining_Due": "مستحق الدفع"
        })
        
        cols_to_show = ["Account No.", "Spoc", "Phone Sub Account", "الفاتورة الصادرة ابريل ٢٠٢٦", "System", "مستحق الدفع", "مدفوعات اليوم"]
        st.dataframe(display_report[cols_to_show].style.format(precision=2), use_container_width=True, hide_index=True)

        # تحضير ملف الإكسيل للتحميل (ترحيل البيانات)[cite: 1]
        # نجعل النظام الحالي هو "السابق" للمرة القادمة[cite: 1]
        updated_df["previous_system"] = updated_df["system"]
        
        output = BytesIO()
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            updated_df.to_excel(writer, index=False)
        
        st.success("✅ تم تحديث الحسابات. يرجى تحميل الملف ورفعه لـ GitHub.")
        st.download_button(
            label="📥 تحميل ملف database.xlsx المحدث",
            data=output.getvalue(),
            file_name="database.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
else:
    st.error("⚠️ يرجى التأكد من وجود ملف database.xlsx في المستودع.")
