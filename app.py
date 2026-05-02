import streamlit as st
import pandas as pd
import os
from datetime import datetime
import plotly.graph_objects as go
from io import BytesIO
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

# ألوان احترافية: أزرق داكن ملكي + أبيض
PRIMARY_COLOR = "#1a237e"  # أزرق داكن ملكي
SECONDARY_COLOR = "#ffffff" # خلفية بيضاء
TEXT_COLOR = "#333333"
RED_COLOR = "#d32f2f"      # أحمر غامق للـ Overpayment
GREEN_COLOR = "#388e3c"    # أخضر للمدفوعات الطبيعية

# تطبيق CSS مخصص مع خط عربي جميل (Tajawal)
st.markdown(f"""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Tajawal:wght@400;500;700&display=swap');
    
    .main {{
        background-color: {SECONDARY_COLOR};
        font-family: 'Tajawal', sans-serif;
    }}
    
    [data-testid="stSidebar"] {{
        background-color: {PRIMARY_COLOR};
        font-family: 'Tajawal', sans-serif;
    }}
    
    [data-testid="stSidebar"] .stMarkdown h1, 
    [data-testid="stSidebar"] .stMarkdown h2,
    [data-testid="stSidebar"] .stMarkdown p,
    [data-testid="stSidebar"] label {{
        color: white !important;
        font-family: 'Tajawal', sans-serif;
    }}
    
    [data-testid="stSidebar"] .stButton > button {{
        background-color: rgba(255, 255, 255, 0.1);
        color: white;
        border: none;
        width: 100%;
        text-align: right;
        padding: 12px;
        margin-bottom: 8px;
        border-radius: 8px;
        font-family: 'Tajawal', sans-serif;
        font-weight: 500;
    }}
    
    [data-testid="stSidebar"] .stButton > button:hover {{
        background-color: rgba(255, 255, 255, 0.2);
    }}

    div[data-testid="stMetric"] {{
        background-color: white;
        padding: 25px;
        border-radius: 12px;
        box-shadow: 0 6px 12px rgba(0,0,0,0.08);
        text-align: center;
        border-top: 4px solid {PRIMARY_COLOR};
        font-family: 'Tajawal', sans-serif;
    }}
    
    div[data-testid="stMetric"] p {{
        font-size: 18px;
        color: {TEXT_COLOR};
        font-weight: 500;
    }}
    
    div[data-testid="stMetric"] div[data-testid="stMetricValue"] {{
        font-size: 28px;
        font-weight: bold;
        color: {PRIMARY_COLOR};
        margin-top: 8px;
    }}

    .dashboard-header {{
        display: flex;
        justify-content: space-between;
        align-items: center;
        background: linear-gradient(135deg, {PRIMARY_COLOR} 0%, #283593 100%);
        color: white;
        padding: 25px 35px;
        border-radius: 15px;
        margin-bottom: 25px;
        box-shadow: 0 8px 16px rgba(0,0,0,0.1);
        font-family: 'Tajawal', sans-serif;
    }}
    
    .dashboard-header h1 {{
        margin: 0;
        font-size: 32px;
        font-weight: 700;
        letter-spacing: 0.5px;
    }}
    
    .dashboard-header .date-info {{
        font-size: 16px;
        opacity: 0.95;
        text-align: left;
        line-height: 1.4;
    }}

    .stDataFrame {{
        border-radius: 12px;
        overflow: hidden;
        box-shadow: 0 6px 12px rgba(0,0,0,0.05);
        font-family: 'Tajawal', sans-serif;
    }}
    
    .stButton > button {{
        background-color: {PRIMARY_COLOR};
        color: white;
        border-radius: 8px;
        padding: 12px 24px;
        font-weight: 600;
        font-family: 'Tajawal', sans-serif;
        transition: all 0.3s ease;
    }}
    
    .stButton > button:hover {{
        background-color: #0d1642;
        transform: translateY(-2px);
        box-shadow: 0 4px 8px rgba(0,0,0,0.1);
    }}
</style>
""", unsafe_allow_html=True)

# ================== إدارة البيانات ==================
DB_FILE = "database.xlsx"

def load_data():
    """تحميل البيانات والتحقق من وجود عمود system"""
    if os.path.exists(DB_FILE):
        try:
            df = pd.read_excel(DB_FILE)
            # التحقق من وجود الأعمدة المطلوبة بما فيها system
            required_cols = ["Account No.", "Spoc", "Mobile", "Invoice_April_2026", "Previous", "system", "Type"]
            missing_cols = [col for col in required_cols if col not in df.columns]
            
            if missing_cols:
                st.error(f"⚠️ الأعمدة التالية مفقودة في ملف البيانات: {missing_cols}")
                st.info("💡 يرجى التأكد من أن ملف database.xlsx يحتوي على عمود باسم 'system' (بالإنجليزية وبأحرف صغيرة) بالإضافة للأعمدة الأخرى.")
                return pd.DataFrame()
            
            return df
        except Exception as e:
            st.error(f"❌ خطأ في قراءة ملف البيانات: {e}")
            return pd.DataFrame()
    else:
        st.warning("⚠️ لم يتم العثور على ملف 'database.xlsx'. يرجى رفعه إلى المستودع.")
        return pd.DataFrame()

def format_currency(value):
    """تنسيق الأرقام كعملة"""
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
    
    if not df.empty:
        # عرض الهيدر
        current_time = datetime.now().strftime('%Y-%m-%d %H:%M')
        st.markdown(f"""
        <div class="dashboard-header">
            <div>
                <h1>إجمالي فواتير - April 2026</h1>
                <p style="font-size: 18px; margin-top: 8px; opacity: 0.9;">حساب منطقة البحر الأحمر للتأمين الصحي - 6.133531</p>
            </div>
            <div class="date-info">
                <strong>آخر تحديث للنظام</strong><br>
                {current_time}
            </div>
        </div>
        """, unsafe_allow_html=True)

        # ================== الحسابات التلقائية ==================
        # المدفوع منذ آخر تحديث = Previous - system
        # ملاحظة: نستخدم عمود 'system' كما هو موجود في ملف الإكسل الخاص بكِ
        df["Paid_Since_Last_Update"] = df.apply(
            lambda row: 0 if row["Type"] == "NonPayment" else row["Previous"] - row["system"], axis=1
        )

        # Overpayment (إذا كان الناتج سالباً، يعني دفعنا أكثر من المطلوب)
        df["Overpayment"] = df["Paid_Since_Last_Update"].apply(lambda x: abs(x) if x < 0 else 0)

        # Collection (المبلغ المحصل فعلياً، لا يتجاوز الرصيد السابق)
        df["Collection"] = df.apply(
            lambda row: 0 if row["Type"] == "NonPayment" else max(0, min(row["Paid_Since_Last_Update"], row["Previous"])) , axis=1
        )

        # متبقي للدفع = الفاتورة - ما تم تسجيله في النظام
        df["Remaining_Due"] = df["Invoice_April_2026"] - df["system"]

        # ================== عرض المقاييس (Metrics) ==================
        normal_df = df[df['Type'] != 'NonPayment']
        
        total_paid = normal_df['Paid_Since_Last_Update'].sum()
        total_collection = normal_df['Collection'].sum()
        total_overpayment = normal_df['Overpayment'].sum()
        total_remaining = normal_df['Remaining_Due'].sum()

        c1, c2, c3, c4 = st.columns(4)
        with c1:
            st.metric(label="إجمالي المدفوع منذ آخر تحديث", value=f"{total_paid:,.0f} جنيه")
        with c2:
            st.metric(label="إجمالي التحصيل الفعلي", value=f"{total_collection:,.0f} جنيه")
        with c3:
            st.metric(label="إجمالي الدفع الزائد (Overpayment)", value=f"{total_overpayment:,.0f} جنيه", delta_color="inverse")
        with c4:
            st.metric(label="إجمالي المتبقي للدفع", value=f"{total_remaining:,.0f} جنيه")

        st.markdown("---")

        # ================== عرض الجدول النهائي ==================
        st.subheader("📋 تفاصيل الفواتير والمدفوعات بعد التحديث")

        report_df = df.copy()

        # تنسيق الأرقام لتظهر بشكل جميل
        numeric_cols = ['Previous', 'system', 'Paid_Since_Last_Update', 'Collection', 'Overpayment', 'Remaining_Due']
        for col in numeric_cols:
            report_df[col] = report_df[col].apply(format_currency)

        # ترتيب الأعمدة للعرض
        report_df = report_df[[
            "Account No.", 
            "Spoc", 
            "Mobile", 
            "Previous", 
            "system", 
            "Paid_Since_Last_Update", 
            "Overpayment", 
            "Remaining_Due", 
            "Type"
        ]]

        # تسمية الأعمدة بالعربية للعرض فقط
        report_df.rename(columns={
            "Account No.": "رقم الحساب",
            "Spoc": "اسم العميل/الجهة",
            "Mobile": "رقم الهاتف",
            "Previous": "الرصيد السابق",
            "system": "المبلغ على النظام (System)",
            "Paid_Since_Last_Update": "المدفوع منذ آخر تحديث",
            "Overpayment": "الدفع الزائد (Overpayment)",
            "Remaining_Due": "متبقي للدفع",
            "Type": "النوع"
        }, inplace=True)

        # تطبيق التنسيق الشرطي للألوان (أحمر للسالب، أخضر للموجب)
        def highlight_values(val):
            if isinstance(val, str):
                try:
                    # تنظيف القيمة من الفواصل لتحويلها لرقم
                    clean_val = val.replace(',', '')
                    num_val = float(clean_val)
                    
                    if num_val < 0:
                        return f'color: {RED_COLOR}; font-weight: bold; background-color: #ffebee;'
                    elif num_val > 0:
                        return f'color: {GREEN_COLOR};'
                    else:
                        return 'color: gray;'
                except:
                    return ''
            return ''

        columns_to_style = ['المدفوع منذ آخر تحديث', 'الدفع الزائد (Overpayment)', 'متبقي للدفع']
        existing_cols = [col for col in columns_to_style if col in report_df.columns]
        
        if existing_cols:
            styled_df = report_df.style.map(highlight_values, subset=existing_cols)
        else:
            styled_df = report_df.style

        st.dataframe(styled_df, use_container_width=True, hide_index=True)

        # إضافة صف الإجمالي في أسفل الجدول
        totals_row = {
            "رقم الحساب": "الإجمالي",
            "اسم العميل/الجهة": "",
            "رقم الهاتف": "",
            "الرصيد السابق": f"{df['Previous'].sum():,.0f}",
            "المبلغ على النظام (System)": f"{df['system'].sum():,.0f}",
            "المدفوع منذ آخر تحديث": f"{df['Paid_Since_Last_Update'].sum():,.0f}",
            "الدفع الزائد (Overpayment)": f"{df['Overpayment'].sum():,.0f}",
            "متبقي للدفع": f"{df['Remaining_Due'].sum():,.0f}",
            "النوع": ""
        }
        st.dataframe(pd.DataFrame([totals_row]), use_container_width=True, hide_index=True)

        st.markdown("---")

        # ================== قسم التصدير ==================
        st.subheader("📥 تصدير التقرير")
        exp_col1, exp_col2, exp_col3 = st.columns(3)
        
        with exp_col1:
            if st.button("تصدير Excel"):
                output = BytesIO()
                with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                    # نستخدم report_df لأنه يحتوي على الأسماء العربية والتنسيق
                    report_df.to_excel(writer, index=False, sheet_name='Report')
                    workbook = writer.book
                    worksheet = writer.sheets['Report']
                    
                    # تنسيق الهيدر
                    header_format = workbook.add_format({
                        'bold': True, 
                        'text_wrap': True, 
                        'valign': 'top', 
                        'fg_color': PRIMARY_COLOR, 
                        'font_color': 'white',
                        'border': 1,
                        'font_name': 'Arial'
                    })
                    for col_num, value in enumerate(report_df.columns.values):
                        worksheet.write(0, col_num, value, header_format)
                    
                    # تنسيقات الأرقام والألوان للإكسل
                    number_format = workbook.add_format({'num_format': '#,##0.00'})
                    red_format = workbook.add_format({'num_format': '#,##0.00', 'font_color': 'red', 'bg_color': '#ffebee'})
                    green_format = workbook.add_format({'num_format': '#,##0.00', 'font_color': 'green'})
                    
                    # تطبيق التنسيقات على الخلايا
                    for row_num in range(1, len(report_df) + 1):
                        # الأعمدة المهمة: المدفوع (5)، الدفع الزائد (6)، المتبقي (7)
                        for col_num in [5, 6, 7]:
                            val = report_df.iloc[row_num-1, col_num]
                            try:
                                num_val = float(str(val).replace(',', ''))
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
                    file_name="etisalat_report_april_2026_final.xlsx",
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
                
                # تحويل البيانات لقائمة لـ ReportLab
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
                        label="📄 تحميل ملف PDF",
                        data=f,
                        file_name="etisalat_report_april_2026_final.pdf",
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
                    file_name="etisalat_report_april_2026_final.png",
                    mime="image/png"
                )

    else:
        st.stop() # توقف إذا لم يتم تحميل البيانات

else:
    st.info(f"صفحة '{menu}' قيد الإنشاء.")
