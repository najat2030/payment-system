import streamlit as st
import pandas as pd
import os
from datetime import datetime
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

# ألوان جديدة: أحمر ملكي + أبيض
PRIMARY_COLOR = "#8B0000"  # أحمر ملكي
SECONDARY_COLOR = "#FFFFFF" # خلفية بيضاء
ACCENT_COLOR = "#F8F9FA"   # رمادي فاتح للخلفيات
TEXT_COLOR = "#333333"
RED_COLOR = "#D32F2F"
GREEN_COLOR = "#388E3C"
YELLOW_COLOR = "#FFEB3B"

# تطبيق CSS مخصص
st.markdown(f"""
<style>
    .main {{
        background-color: {SECONDARY_COLOR};
    }}
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

    div[data-testid="stMetric"] {{
        background-color: white;
        padding: 20px;
        border-radius: 10px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        text-align: center;
        border-left: 5px solid {PRIMARY_COLOR};
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

    .dashboard-header {{
        display: flex;
        justify-content: space-between;
        align-items: center;
        background-color: {PRIMARY_COLOR};
        color: white;
        padding: 20px 30px;
        border-radius: 10px;
        margin-bottom: 20px;
        box-shadow: 0 4px 8px rgba(0,0,0,0.1);
    }}
    .dashboard-header h1 {{
        margin: 0;
        font-size: 28px;
        font-weight: bold;
    }}
    .dashboard-header .date-info {{
        font-size: 14px;
        opacity: 0.9;
        text-align: left;
    }}

    .stDataFrame {{
        border-radius: 10px;
        overflow: hidden;
        box-shadow: 0 4px 6px rgba(0,0,0,0.05);
    }}
    
    .stButton > button {{
        background-color: {PRIMARY_COLOR};
        color: white;
        border-radius: 5px;
        padding: 10px 20px;
        font-weight: bold;
    }}
    .stButton > button:hover {{
        background-color: #6d0000;
    }}
</style>
""", unsafe_allow_html=True)

# ================== إدارة البيانات ==================
DB_FILE = "database.xlsx"

def load_data():
    if os.path.exists(DB_FILE):
        try:
            df = pd.read_excel(DB_FILE)
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

def format_currency(value):
    if pd.isna(value):
        return "0.00"
    return f"{value:,.2f}"

# ================== واجهة المستخدم الرئيسية ==================

with st.sidebar:
    st.image("https://upload.wikimedia.org/wikipedia/commons/thumb/6/6a/Etisalat_logo.svg/1200px-Etisalat_logo.svg.png", width=150)
    st.markdown("---")
    menu = st.radio("القائمة", ["لوحة التحكم", "رفع تقرير جديد", "التقارير السابقة", "العملاء", "الإعدادات"])
    st.markdown("---")
    st.write("**مدير النظام**")
    st.write("Admin")
    if st.button("تسجيل خروج"):
        st.stop()

if menu == "لوحة التحكم":
    df = load_data()
    if df.empty:
        st.stop()

    # حساب القيم الأساسية
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
            <p style="font-size: 16px; margin-top: 5px;">حساب منطقة البحر الأحمر للتأمين الصحي - 6.133531</p>
        </div>
        <div class="date-info">
            آخر تحديث<br>
            {current_time}
        </div>
    </div>
    """, unsafe_allow_html=True)

    # المقاييس العلوية
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.metric(label="إجمالي المدفوع", value=f"{total_paid:,.0f} جنيه")
    with c2:
        st.metric(label="إجمالي مستحق الدفع", value=f"{total_due:,.0f} جنيه")
    with c3:
        st.metric(label="عدد العملاء", value=num_customers)
    with c4:
        st.metric(label="عدد العملاء الذين دفعوا", value=num_paid_customers)

    st.markdown("---")

    # أزرار الإجراءات
    col_btn1, col_btn2 = st.columns(2)
    with col_btn1:
        if st.button("رفع تقرير جديد"):
            st.info("خاصية رفع التقارير الجديدة قيد التطوير.")
    with col_btn2:
        if st.button("تحديث النظام"):
            st.rerun()

    st.markdown("---")

    # تحضير الجدول المتقدم
    st.subheader("تفاصيل الفواتير والمدفوعات")

    # إنشاء نسخة للعمل عليها
    report_df = df.copy()

    # إضافة عمود "System" (مبالغ مجنبية زيرو خصم) — هنا نفترض أنه يساوي Previous إلا إذا كان NonPayment
    report_df['System'] = report_df.apply(
        lambda row: 0 if row['Type'] == 'NonPayment' else row['Previous'], axis=1
    )

    # إضافة عمود "مستحق الدفع" = Invoice - System
    report_df['مستحق الدفع'] = report_df['Invoice_April_2026'] - report_df['System']

    # تنسيق الأرقام
    for col in ['Previous', 'Invoice_April_2026', 'System', 'مستحق الدفع']:
        report_df[col] = report_df[col].apply(format_currency)

    # إعادة ترتيب الأعمدة لتطابق التقرير اليدوي
    report_df = report_df[[
        "Account No.", 
        "Spoc", 
        "Mobile", 
        "System", 
        "Invoice_April_2026", 
        "مستحق الدفع", 
        "Type"
    ]]

    # تسمية الأعمدة بالعربية
    report_df.rename(columns={
        "Account No.": "رقم الحساب",
        "Spoc": "اسم العميل/الجهة",
        "Mobile": "رقم الهاتف",
        "System": "مبالغ مجنبية زيرو خصم",
        "Invoice_April_2026": "الفاتورة الصادرة أبريل 2026",
        "مستحق الدفع": "مستحق الدفع",
        "Type": "النوع"
    }, inplace=True)

    # عرض الجدول مع تنسيق شرطي (ألوان حسب القيمة)
    def highlight_negative(val):
        if isinstance(val, str):
            try:
                num_val = float(val.replace(',', ''))
                if num_val < 0:
                    return f'color: {RED_COLOR}; font-weight: bold;'
                elif num_val > 0:
                    return f'color: {GREEN_COLOR};'
                else:
                    return 'color: gray;'
            except:
                return ''
        return ''

    styled_df = report_df.style.applymap(highlight_negative, subset=['مبالغ مجنبية زيرو خصم', 'الفاتورة الصادرة أبريل 2026', 'مستحق الدفع'])

    st.dataframe(styled_df, use_container_width=True, hide_index=True)

    # إضافة صف الإجمالي
    totals_row = {
        "رقم الحساب": "إجمالي المديونية على السيستم",
        "اسم العميل/الجهة": "",
        "رقم الهاتف": "",
        "مبالغ مجنبية زيرو خصم": f"{df['Previous'].sum():,.0f}",
        "الفاتورة الصادرة أبريل 2026": f"{df['Invoice_April_2026'].sum():,.0f}",
        "مستحق الدفع": f"{(df['Invoice_April_2026'] - df['Previous']).sum():,.0f}",
        "النوع": ""
    }
    st.dataframe(pd.DataFrame([totals_row]), use_container_width=True, hide_index=True)

    st.markdown("---")

    # قسم التصدير
    st.subheader("تصدير التقرير")
    exp_col1, exp_col2, exp_col3 = st.columns(3)
    
    with exp_col1:
        if st.button("تصدير Excel"):
            output = BytesIO()
            with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                report_df.to_excel(writer, index=False, sheet_name='Report')
                workbook = writer.book
                worksheet = writer.sheets['Report']
                
                header_format = workbook.add_format({
                    'bold': True, 
                    'text_wrap': True, 
                    'valign': 'top', 
                    'fg_color': PRIMARY_COLOR, 
                    'font_color': 'white',
                    'border': 1
                })
                for col_num, value in enumerate(report_df.columns.values):
                    worksheet.write(0, col_num, value, header_format)
                
                number_format = workbook.add_format({'num_format': '#,##0.00'})
                red_format = workbook.add_format({'num_format': '#,##0.00', 'font_color': 'red'})
                green_format = workbook.add_format({'num_format': '#,##0.00', 'font_color': 'green'})
                
                for row_num in range(1, len(report_df) + 1):
                    for col_num in [3, 4, 5]: # الأعمدة الرقمية
                        val = report_df.iloc[row_num-1, col_num]
                        try:
                            num_val = float(val.replace(',', ''))
                            if num_val < 0:
                                worksheet.write(row_num, col_num, num_val, red_format)
                            elif num_val > 0:
                                worksheet.write(row_num, col_num, num_val, green_format)
                            else:
                                worksheet.write(row_num, col_num, num_val, number_format)
                        except:
                            worksheet.write(row_num, col_num, val, number_format)
            
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
            
            styles = getSampleStyleSheet()
            title = Paragraph("تقرير فواتير أبريل 2026 - شركة اتصالات", styles['Title'])
            elements.append(title)
            elements.append(Spacer(1, 12))
            
            data = [report_df.columns.tolist()] + report_df.values.tolist()
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
                header=dict(values=list(report_df.columns),
                            fill_color=PRIMARY_COLOR,
                            align='center',
                            font=dict(color='white', size=12)),
                cells=dict(values=[report_df[col] for col in report_df.columns],
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
