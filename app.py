import streamlit as st
import pandas as pd
import os
from datetime import datetime
import plotly.graph_objects as go
from io import BytesIO

# ================== إعدادات الصفحة والثيم ==================
st.set_page_config(
    page_title="تحديث مدفوعات اتصالات",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ألوان احترافية
PRIMARY_COLOR = "#1a237e"
SECONDARY_COLOR = "#ffffff"
TEXT_COLOR = "#333333"
RED_COLOR = "#d32f2f"
GREEN_COLOR = "#388e3c"

st.markdown(f"""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Tajawal:wght@400;500;700&display=swap');
    .main {{ background-color: {SECONDARY_COLOR}; font-family: 'Tajawal', sans-serif; }}
    [data-testid="stSidebar"] {{ background-color: {PRIMARY_COLOR}; }}
    .dashboard-header {{ 
        background: linear-gradient(135deg, {PRIMARY_COLOR} 0%, #283593 100%); 
        color: white; padding: 25px; border-radius: 15px; margin-bottom: 25px; 
    }}
    div[data-testid="stMetric"] {{ 
        background-color: white; padding: 20px; border-radius: 12px; 
        box-shadow: 0 4px 8px rgba(0,0,0,0.05); border-top: 4px solid {PRIMARY_COLOR}; 
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
            
            # إذا لم يكن عمود previous_system موجوداً، ننشئه من عمود system الحالي
            if "previous_system" not in df.columns:
                df["previous_system"] = df["system"].copy()
            
            return df
        except Exception as e:
            st.error(f"❌ خطأ في قراءة ملف البيانات: {e}")
            return pd.DataFrame()
    else:
        st.warning("⚠️ ملف 'database.xlsx' غير موجود.")
        return pd.DataFrame()

def format_currency(value):
    if pd.isna(value): return "0.00"
    return f"{value:,.2f}"

# ================== واجهة المستخدم ==================
with st.sidebar:
    st.image("https://upload.wikimedia.org/wikipedia/commons/thumb/6/6a/Etisalat_logo.svg/1200px-Etisalat_logo.svg.png", width=150)
    st.markdown("---")
    menu = st.radio("القائمة", ["لوحة التحكم", "العملاء", "الإعدادات"])

if menu == "لوحة التحكم":
    df = load_data()
    
    if not df.empty:
        current_time = datetime.now().strftime('%Y-%m-%d %H:%M')
        st.markdown(f"""
        <div class="dashboard-header">
            <h1>تحديث مدفوعات اتصالات - April 2026</h1>
            <p>حساب منطقة البحر الأحمر للتأمين الصحي | آخر تحديث: {current_time}</p>
        </div>
        """, unsafe_allow_html=True)

        st.subheader("✍️ تحديث المبالغ من تطبيق OPay")
        
        # عرض الجدول القابل للتعديل
        editable_df = df[["Account No.", "Spoc", "Mobile", "system", "previous_system", "Type"]].copy()
        
        edited_df = st.data_editor(
            editable_df,
            use_container_width=True,
            hide_index=True,
            column_config={
                "system": st.column_config.NumberColumn("المبلغ الحالي (System)", format="%.2f"),
                "previous_system": st.column_config.NumberColumn("المبلغ السابق", disabled=True),
                "Account No.": st.column_config.TextColumn("رقم الحساب", disabled=True),
                "Spoc": st.column_config.TextColumn("الجهة", disabled=True),
                "Type": st.column_config.TextColumn("النوع", disabled=True)
            }
        )

        if st.button("🚀 تحديث وحساب التحصيلات"):
            updated_df = df.copy()
            
            # تحديث القيم باستخدام الخريطة (Map) لتجنب KeyError
            updates = edited_df.set_index("Account No.")["system"].to_dict()
            updated_df["system"] = updated_df["Account No."].map(updates).fillna(updated_df["system"])

            # الحسابات الأساسية[cite: 1]
            # المدفوع = القديم - الجديد
            updated_df["Paid_Since_Last_Update"] = updated_df.apply(
                lambda row: 0 if row["Type"] == "NonPayment" else (row["previous_system"] - row["system"]), axis=1
            )
            
            # المتبقي = الفاتورة - الجديد
            updated_df["Remaining_Due"] = updated_df["Invoice_April_2026"] - updated_df["system"]
            updated_df["Overpayment"] = updated_df["Paid_Since_Last_Update"].apply(lambda x: abs(x) if x < 0 else 0)

            # عرض الملخص (Metrics)[cite: 1]
            c1, c2, c3 = st.columns(3)
            with c1: st.metric("إجمالي التحصيل اللحظي", f"{updated_df['Paid_Since_Last_Update'].sum():,.2f} ج.م")
            with c2: st.metric("إجمالي المتبقي", f"{updated_df['Remaining_Due'].sum():,.2f} ج.م")
            with c3: st.metric("عدد العمليات", len(updated_df[updated_df['Paid_Since_Last_Update'] > 0]))

            st.markdown("---")
            st.subheader("📋 تقرير التفاصيل النهائي")
            st.dataframe(updated_df, use_container_width=True, hide_index=True)

            # تحضير ملف التحميل[cite: 1]
            # لجعل التحديث القادم صحيحاً، نجعل الـ system الحالي هو الـ previous_system للمرة القادمة
            db_to_save = updated_df.copy()
            db_to_save["previous_system"] = db_to_save["system"]
            
            output = BytesIO()
            with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                db_to_save.to_excel(writer, index=False)
            
            st.success("✅ تم التحديث! حملي الملف وارفعيه لـ GitHub")
            st.download_button(
                label="📥 تحميل ملف database.xlsx المحدث",
                data=output.getvalue(),
                file_name="database.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
    else:
        st.error("لم يتم تحميل أي بيانات. تأكدي من رفع ملف database.xlsx")
