import streamlit as st
import pandas as pd
import os
import numpy as np
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
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
# ملاحظة: لاستخدام خط عربي في ReportLab، يجب تحميل ملف خط (.ttf) ودعمه.
# للتبسيط، سنستخدم الخط الافتراضي الذي قد لا يدعم العربية بشكل كامل في الجداول المعقدة.
# لحل مشكلة العربية في PDF بشكل مثالي، يُنصح باستخدام مكتبات أخرى أو خطوط مدمجة تدعم unicode.
# هنا سنحاول استخدام نهج مبسط.

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
        font-family: 'Tajawal', sans-serif; /* Assuming a font is available or using default */
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

# ================== إدارة البيانات (Mock Data for Demo) ==================
DB_FILE = "telecom_data.xlsx"

def load_data():
    """تحميل البيانات من ملف إكسل أو إنشاء بيانات تجريبية إذا لم يوجد الملف."""
    if os.path.exists(DB_FILE):
        try:
            df = pd.read_excel(DB_FILE)
            return df
        except Exception as e:
            st.error(f"خطأ في قراءة ملف البيانات: {e}")
            return create_mock_data()
    else:
        return create_mock_data()

def create_mock_data():
    """إنشاء بيانات تجريبية تحاكي الهيكل المطلوب."""
    data = {
        "Account No.": [6133531, 61335317567, 61335317568, 61335317569, 61335317570, 61335317571, 61335317572, 613353116737, 61335317574, 61335317575, 61335317576, 61335318491],
        "Spoc": ["منافذنا", "المكتب", "منافذ 3", "منافذنا ٢", "منافذ كوم امبو", "Omar Sayed", "Non Payment", "هيئات الدردقة", "منافذ ؟", "Suspend", "Ahmad Bakry", "هيئات اخرى"],
        "Phone Sub Account": ["01121800500", "01157000776", "01102030200", "01140095047", "01125101080", "01158111464", "-", "01100230713", "01146636611", "01155666925", "01123662616", "01158226650"],
        "Previous Balance": [10000, 0, 0, 0, 0, 1800, 0, 200, 0, 1462.39, 0, 5961.11],
        "Invoice April 2026": [101722.75, 76567.16, 84700.04, 70934.15, 41159.21, 331849.58, 0, 160348.81, 4040.54, -867.39, 16839.79, 171360.40],
        "System": [42494.75, 34595.16, 7193.96, 42813.58, -1800.00, 197797.58, 101680.29, 76608.81, 0.00, -1462.39, 20.35, 27319.40],
        "Type": ["Normal"] * 11 + ["NonPayment"]
    }
    df = pd.DataFrame(data)
    # إعادة ترتيب الأعمدة لتطابق الصورة تقريباً
    df = df[["Account No.", "Spoc", "Phone Sub Account", "Previous Balance", "Invoice April 2026", "System", "Type"]]
    df.to_excel(DB_FILE, index=False)
    return df

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
    st.image("https://upload.wikimedia.org/wikipedia/commons/thumb/6/6a/Etisalat_logo.svg/1200px-Etisalat_logo.svg.png", width=150) # شعار تقريبي
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

    # حساب القيم للمقاييس العلوية
    total_paid = df[df['Type'] != 'NonPayment']['Previous Balance'].sum()
    total_due = df[df['Type'] != 'NonPayment']['Invoice April 2026'].sum()
    num_customers = len(df)
    num_paid_customers = len(df[df['Type'] != 'NonPayment'])

    # عرض الهيدر
    st.markdown("""
    <div class="dashboard-header">
        <div>
            <h1>إجمالي فواتير - April 2026</h1>
            <p class="date-info">حساب منطقة البحر الأحمر للتأمين الصحي - 6.133531</p>
        </div>
        <div class="date-info">
            آخر تحديث<br>
            {datetime.now().strftime('%Y-%m-%d %H:%M')}
        </div>
    </div>
    """.format(datetime=datetime.now()), unsafe_allow_html=True)

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
        pass # Placeholder for Excel button logic later
    with col_btn4:
        pass # Placeholder for PDF button logic later
    with col_btn5:
        pass # Placeholder for Image button logic later

    st.markdown("---")

    # عرض الجدول الرئيسي
    st.subheader("تفاصيل الفواتير والمدفوعات")
    
    # تحضير البيانات للعرض
    display_df = df.copy()
    display_df['Previous Balance'] = display_df['Previous Balance'].apply(format_currency)
    display_df['Invoice April 2026'] = display_df['Invoice April 2026'].apply(format_currency)
    display_df['System'] = display_df['System'].apply(format_currency)
    
    # تسمية الأعمدة بالعربية للعرض
    display_df.rename(columns={
        "Account No.": "رقم الحساب",
        "Spoc": "اسم العميل/الجهة",
        "Phone Sub Account": "رقم الهاتف",
        "Previous Balance": "المدفوع من آخر تحديث",
        "Invoice April 2026": "الفاتورة الصادرة أبريل 2026",
        "System": "النظام",
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
                    for col_num in range(3, 6): # أعمدة الأرقام
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
                ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'), # خط افتراضي، قد لا يدعم العربية
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
