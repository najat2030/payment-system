import streamlit as st
import pandas as pd
import os
from datetime import datetime
import plotly.express as px
import plotly.graph_objects as go
from io import BytesIO
import arabic_reshaper
from bidi.algorithm import get_display
from reportlab.lib import colors
from reportlab.lib.pagesizes import landscape, A4
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet

# ================== إعدادات الصفحة والثيم ==================
st.set_page_config(
    page_title="نظام فوتاير اتصالات",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ألوان مستوحاة من الصورة
PRIMARY_COLOR = "#006341"  # أخضر داكن
SECONDARY_COLOR = "#F0F2F6" # خلفية فاتحة
ACCENT_COLOR = "#E8F5E9"   # أخضر فاتح للخلفيات
TEXT_COLOR = "#333333"
RED_COLOR = "#D32F2F"
GREEN_COLOR = "#388E3C"

# تطبيق CSS مخصص لمحاكاة التصميم
st.markdown(f"""
<style>
    /* General Styling */
    .main {{
        background-color: {SECONDARY_COLOR};
    }}
    .stApp {{
        font-family: 'Tajawal', sans-serif;
    }}
    
    /* Sidebar Styling */
    [data-testid="stSidebar"] {{
        background-color: {PRIMARY_COLOR};
    }}
    [data-testid="stSidebar"] .stMarkdown h1, 
    [data-testid="stSidebar"] .stMarkdown h2,
    [data-testid="stSidebar"] .stMarkdown p,
    [data-testid="stSidebar"] label {{
        color: white !important;
    }}
    [data-testid="stSidebar"] .stButton > button {{
        background-color: rgba(255, 255, 255, 0.1);
        color: white;
        border: none;
        width: 100%;
        text-align: right;
        padding: 10px;
        margin-bottom: 5px;
    }}
    [data-testid="stSidebar"] .stButton > button:hover {{
        background-color: rgba(255, 255, 255, 0.2);
    }}

    /* Metric Cards Styling */
    div[data-testid="stMetric"] {{
        background-color: white;
        padding: 20px;
        border-radius: 10px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        text-align: center;
    }}
    div[data-testid="stMetric"] p {{
        font-size: 16px;
        color: {TEXT_COLOR};
    }}
    div[data-testid="stMetric"] div[data-testid="stMetricValue"] {{
        font-size: 24px;
        font-weight: bold;
        color: {PRIMARY_COLOR};
    }}

    /* Header Styling */
    .dashboard-header {{
        display: flex;
        justify-content: space-between;
        align-items: center;
        background-color: {PRIMARY_COLOR};
        color: white;
        padding: 15px 25px;
        border-radius: 10px;
        margin-bottom: 20px;
    }}
    .dashboard-header h1 {{
        margin: 0;
        font-size: 24px;
    }}
    .dashboard-header .date-info {{
        font-size: 14px;
        opacity: 0.9;
    }}

    /* Table Styling */
    .stDataFrame {{
        border-radius: 10px;
        overflow: hidden;
        box-shadow: 0 4px 6px rgba(0,0,0,0.05);
    }}
    
    /* Button Styling */
    .stButton > button {{
        background-color: {PRIMARY_COLOR};
        color: white;
        border-radius: 5px;
        padding: 10px 20px;
    }}
    .stButton > button:hover {{
        background-color: #004d33;
    }}
</style>
""", unsafe_allow_html=True)

# ================== إدارة البيانات ==================
DB_FILE = "database.xlsx"

def load_data():
    """تحميل البيانات من ملف إكسل أو عرض رسالة خطأ إذا لم يوجد."""
    if os.path.exists(DB_FILE):
        try:
            df = pd.read_excel(DB_FILE)
            # تأكد من وجود الأعمدة المطلوبة
            required_cols = ["Account No.", "Spoc", "Mobile", "Invoice_April_2026", "Previous", "Type"]
            missing_cols = [col for col in required_cols if col not in df.columns]
            if missing_cols:
                st.error(f"الأعمدة التالية مفقودة في ملف البيانات: {missing_cols}")
                return pd.DataFrame()
            return df
        except Exception as e:
            st.error(f"خطأ في قراءة ملف البيانات: {e}")
            return pd.DataFrame()
    else:
        st.warning("لم يتم العثور على ملف 'database.xlsx'. يرجى رفعه إلى المستودع.")
        return pd.DataFrame()

def save_data(df):
    """حفظ البيانات بعد التعديل."""
    df.to_excel(DB_FILE, index=False)

# ================== وظائف مساعدة للتنسيق والعرض ==================

def format_currency(value):
    """تنسيق الأرقام كعملة عربية."""
    if pd.isna(value):
        return "0.00"
    return f"{value:,.2f}"

def get_display_text(text):
    """دالة لعرض النصوص العربية بشكل صحيح في بعض المكتبات."""
    if not isinstance(text, str):
        return str(text)
    reshaped_text = arabic_reshaper.reshape(text)
    bidi_text = get_display(reshaped_text)
    return bidi_text

# ================== واجهة المستخدم الرئيسية ==================

# --- الشريط الجانبي ---
with st.sidebar:
    st.image("https://upload.wikimedia.org/wikipedia/commons/thumb/6/6a/Etisalat_logo.svg/1200px-Etisalat_logo.svg.png", width=150)
    st.markdown("---")
    menu = st.radio("القائمة", ["لوحة التحكم", "رفع تقرير جديد", "التقارير السابقة", "العملاء", "الإعدادات"])
    st.markdown("---")
    st.write("**مدير النظام**")
    st.write("Admin")
    if st.button("تسجيل خروج"):
        st.stop()

# --- المحتوى الرئيسي ---
if menu == "لوحة التحكم":
    # تحميل البيانات
    df = load_data()

    if df.empty:
        st.stop()

    # حساب القيم للمقاييس العلوية
    total_paid = df[df['Type'] != 'NonPayment']['Previous'].sum()
    total_due = df[df['Type'] != 'NonPayment']['Invoice_April_2026'].sum()
    num_customers = len(df)
    num_paid_customers = len(df[df['Type'] != 'NonPayment'])

    # عرض الهيدر
    current_time = datetime.now().strftime('%Y-%m-%d %H:%M')
    st.markdown(f"""
    <div class="dashboard-header">
        <div>
            <h1>إجمالي فواتير - April 2026</h1>
            <p class="date-info">حساب منطقة البحر الأحمر للتأمين الصحي - 6.133531</p>
        </div>
        <div class="date-info">
            آخر تحديث<br>
            {current_time}
        </div>
    </div>
    """, unsafe_allow_html=True)

    # عرض المقاييس (Metrics)
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.metric(label="إجمالي المدفوع", value=f"{total_paid:,.0f} جنيه", delta=None, delta_color="normal")
    with c2:
        st.metric(label="إجمالي مستحق الدفع", value=f"{total_due:,.0f} جنيه", delta=None, delta_color="inverse")
    with c3:
        st.metric(label="عدد العملاء", value=num_customers, delta=None)
    with c4:
        st.metric(label="عدد العملاء الذين دفعوا", value=num_paid_customers, delta=None)

    st.markdown("---")

    # أزرار الإجراءات
    col_btn1, col_btn2, col_btn3, col_btn4, col_btn5 = st.columns([1, 1, 1, 1, 1])
    with col_btn1:
        if st.button("رفع تقرير جديد"):
            st.info("خاصية رفع التقارير الجديدة قيد التطوير.")
    with col_btn2:
        if st.button("تحديث النظام"):
            st.rerun()
    with col_btn3:
        pass
    with col_btn4:
        pass
    with col_btn5:
        pass

    st.markdown("---")

    # عرض الجدول الرئيسي
    st.subheader("تفاصيل الفواتير والمدفوعات")
    
    # تحضير البيانات للعرض
    display_df = df.copy()
    display_df['Previous'] = display_df['Previous'].apply(format_currency)
    display_df['Invoice_April_2026'] = display_df['Invoice_April_2026'].apply(format_currency)
    
    # تسمية الأعمدة بالعربية للعرض
    display_df.rename(columns={
        "Account No.": "رقم الحساب",
        "Spoc": "اسم العميل/الجهة",
        "Mobile": "رقم الهاتف",
        "Previous": "المدفوع من آخر تحديث",
        "Invoice_April_2026": "الفاتورة الصادرة أبريل 2026",
        "Type": "النوع"
    }, inplace=True)

    # استخدام st.dataframe مع تنسيق شرطي بسيط
    st.dataframe(display_df, use_container_width=True, hide_index=True)

    st.markdown("---")

    # قسم التصدير
    st.subheader("تصدير التقرير")
    exp_col1, exp_col2, exp_col3 = st.columns(3)
    
    with exp_col1:
        if st.button("تصدير Excel"):
            output = BytesIO()
            with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                df.to_excel(writer, index=False, sheet_name='Report')
                workbook = writer.book
                worksheet = writer.sheets['Report']
                
                # تنسيق الهيدر
                header_format = workbook.add_format({'bold': True, 'text_wrap': True, 'valign': 'top', 'fg_color': '#006341', 'font_color': 'white'})
                for col_num, value in enumerate(df.columns.values):
                    worksheet.write(0, col_num, value, header_format)
                
                # تنسيق الأرقام
                number_format = workbook.add_format({'num_format': '#,##0.00'})
                for row_num in range(1, len(df) + 1):
                    for col_num in [3, 4]: # أعمدة Invoice_April_2026 و Previous
                        worksheet.write(row_num, col_num, df.iloc[row_num-1, col_num], number_format)
            
            st.download_button(
                label="📥 تحميل ملف Excel",
                data=output.getvalue(),
                file_name="etisalat_report_april_2026.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )

    with exp_col2:
        if st.button("تصدير PDF"):
            doc = SimpleDocTemplate("report.pdf", pagesize=landscape(A4))
            elements = []
            
            # عنوان التقرير
            styles = getSampleStyleSheet()
            title = Paragraph("تقرير فواتير أبريل 2026 - شركة اتصالات", styles['Title'])
            elements.append(title)
            elements.append(Spacer(1, 12))
            
            # تحويل البيانات إلى قائمة لجداول ReportLab
            data = [df.columns.tolist()] + df.values.tolist()
            
            # تنسيق الجدول
            table = Table(data)
            table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor(PRIMARY_COLOR)),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
                ('FONTSIZE', (0, 0), (-1, -1), 8),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                ('GRID', (0, 0), (-1, -1), 1, colors.black)
            ]))
            
            elements.append(table)
            doc.build(elements)
            
            with open("report.pdf", "rb") as f:
                st.download_button(
                    label=" تحميل ملف PDF",
                    data=f,
                    file_name="etisalat_report_april_2026.pdf",
                    mime="application/pdf"
                )

    with exp_col3:
        if st.button("تصدير صورة"):
            fig = go.Figure(data=[go.Table(
                header=dict(values=list(df.columns),
                            fill_color=PRIMARY_COLOR,
                            align='center',
                            font=dict(color='white', size=12)),
                cells=dict(values=[df[col] for col in df.columns],
                           fill_color='lavender',
                           align='center'))
            ])
            
            img_bytes = BytesIO()
            fig.write_image(img_bytes, format="png", scale=2)
            img_bytes.seek(0)
            
            st.download_button(
                label="🖼️ تحميل صورة التقرير",
                data=img_bytes,
                file_name="etisalat_report_april_2026.png",
                mime="image/png"
            )

else:
    st.info(f"صفحة '{menu}' قيد الإنشاء.")
