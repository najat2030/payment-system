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
RED_COLOR = "#D32F2F"      # أحمر غامق للـ Overpayment
GREEN_COLOR = "#388E3C"    # أخضر للمدفوعات الطبيعية
YELLOW_COLOR = "#FFEB3B"   # أصفر للزيادات (اختياري)

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

    /* تنسيق خاص لـ Overpayment */
    .overpayment {{
        color: {RED_COLOR} !important;
        font-weight: bold !important;
        background-color: #ffebee !important;
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

def save_data(df):
    df.to_excel(DB_FILE, index=False)

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

    # ================== قسم تحديث القيم الحالية ==================
    st.subheader("✍️ تحديث القيم الحالية (الرصيد الجديد)")

    # إنشاء نسخة editable من البيانات
    editable_df = df[["Account No.", "Spoc", "Mobile", "Previous", "Type"]].copy()
    editable_df.rename(columns={"Previous": "Current"}, inplace=True)

    # إخفاء صفوف NonPayment من التعديل (أو يمكن تركها حسب الرغبة)
    editable_df = editable_df[editable_df["Type"] != "NonPayment"]

    # استخدام data_editor للسماح بالتعديل المباشر
    edited_df = st.data_editor(
        editable_df,
        use_container_width=True,
        hide_index=True,
        column_config={
            "Current": st.column_config.NumberColumn(
                "الرصيد الحالي",
                help="أدخل الرصيد الجديد لهذا الحساب",
                min_value=0,
                step=0.01,
                format="%.2f"
            )
        }
    )

    # زر لتحديث النظام
    if st.button("🚀 تحديث النظام وحساب المدفوعات"):
        # دمج البيانات المعدلة مع الأصلية
        updated_df = df.merge(edited_df[["Account No.", "Current"]], on="Account No.", how="left")
        
        # إذا لم يتم تعديل بعض الصفوف، نحتفظ بالقيمة القديمة
        updated_df["Current"] = updated_df["Current"].fillna(updated_df["Previous"])

        # حساب المبلغ المدفوع = Previous - Current
        # إذا كان Current > Previous → النتيجة سالبة → Overpayment
        updated_df["Paid"] = updated_df.apply(
            lambda row: 0 if row["Type"] == "NonPayment" else row["Previous"] - row["Current"], axis=1
        )

        # حساب Overpayment (إذا كان Paid سالباً)
        updated_df["Overpayment"] = updated_df["Paid"].apply(lambda x: abs(x) if x < 0 else 0)

        # حساب Collection (المبلغ الذي تم تحصيله فعلياً، لا يتجاوز Previous)
        updated_df["Collection"] = updated_df.apply(
            lambda row: 0 if row["Type"] == "NonPayment" else min(row["Paid"], row["Previous"]) if row["Paid"] > 0 else 0, axis=1
        )

        # حفظ البيانات المحدثة (اختياري — يمكنك إلغاء التعليق إذا أردت الحفظ الدائم)
        # save_data(updated_df)

        # ================== عرض المقاييس بعد التحديث ==================
        normal_df = updated_df[updated_df['Type'] != 'NonPayment']
        total_paid = normal_df['Paid'].sum()
        total_collection = normal_df['Collection'].sum()
        total_overpayment = normal_df['Overpayment'].sum()

        c1, c2, c3, c4 = st.columns(4)
        with c1:
            st.metric(label="إجمالي المدفوع", value=f"{total_paid:,.0f} جنيه")
        with c2:
            st.metric(label="إجمالي التحصيل", value=f"{total_collection:,.0f} جنيه")
        with c3:
            st.metric(label="إجمالي Overpayment", value=f"{total_overpayment:,.0f} جنيه", delta_color="inverse")
        with c4:
            st.metric(label="عدد العملاء", value=len(normal_df))

        st.markdown("---")

        # ================== عرض الجدول النهائي ==================
        st.subheader("تفاصيل الفواتير والمدفوعات بعد التحديث")

        # تحضير الجدول للعرض
        report_df = updated_df.copy()

        # إضافة عمود "System" (نفترض أنه يساوي Previous إلا إذا كان NonPayment)
        report_df['System'] = report_df.apply(
            lambda row: 0 if row['Type'] == 'NonPayment' else row['Previous'], axis=1
        )

        # إضافة عمود "مستحق الدفع" = Invoice - System
        report_df['مستحق الدفع'] = report_df['Invoice_April_2026'] - report_df['System']

        # تنسيق الأرقام
        for col in ['Previous', 'Current', 'Paid', 'Collection', 'Overpayment', 'System', 'مستحق الدفع']:
            report_df[col] = report_df[col].apply(format_currency)

        # إعادة ترتيب الأعمدة
        report_df = report_df[[
            "Account No.", 
            "Spoc", 
            "Mobile", 
            "Previous", 
            "Current", 
            "Paid", 
            "Overpayment", 
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
            "Previous": "الرصيد السابق",
            "Current": "الرصيد الحالي",
            "Paid": "المبلغ المدفوع",
            "Overpayment": "الدفع الزائد (Overpayment)",
            "System": "مبالغ مجنبية زيرو خصم",
            "Invoice_April_2026": "الفاتورة الصادرة أبريل 2026",
            "مستحق الدفع": "مستحق الدفع",
            "Type": "النوع"
        }, inplace=True)

        # تطبيق التنسيق الشرطي للألوان
        def highlight_values(val):
            if isinstance(val, str):
                try:
                    num_val = float(val.replace(',', ''))
                    if num_val < 0:
                        return f'color: {RED_COLOR}; font-weight: bold; background-color: #ffebee;'
                    elif num_val > 0:
                        return f'color: {GREEN_COLOR};'
                    else:
                        return 'color: gray;'
                except:
                    return ''
            return ''

        styled_df = report_df.style.applymap(highlight_values, subset=['المبلغ المدفوع', 'الدفع الزائد (Overpayment)', 'مستحق الدفع'])

        st.dataframe(styled_df, use_container_width=True, hide_index=True)

        # إضافة صف الإجمالي
        totals_row = {
            "رقم الحساب": "إجمالي",
            "اسم العميل/الجهة": "",
            "رقم الهاتف": "",
            "الرصيد السابق": f"{updated_df['Previous'].sum():,.0f}",
            "الرصيد الحالي": f"{updated_df['Current'].sum():,.0f}",
            "المبلغ المدفوع": f"{updated_df['Paid'].sum():,.0f}",
            "الدفع الزائد (Overpayment)": f"{updated_df['Overpayment'].sum():,.0f}",
            "مبالغ مجنبية زيرو خصم": f"{updated_df['System'].sum():,.0f}",
            "الفاتورة الصادرة أبريل 2026": f"{updated_df['Invoice_April_2026'].sum():,.0f}",
            "مستحق الدفع": f"{(updated_df['Invoice_April_2026'] - updated_df['System']).sum():,.0f}",
            "النوع": ""
        }
        st.dataframe(pd.DataFrame([totals_row]), use_container_width=True, hide_index=True)

        st.markdown("---")

        # قسم التصدير (نفس الكود السابق لكن مع الأعمدة الجديدة)
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
                    red_format = workbook.add_format({'num_format': '#,##0.00', 'font_color': 'red', 'bg_color': '#ffebee'})
                    green_format = workbook.add_format({'num_format': '#,##0.00', 'font_color': 'green'})
                    
                    for row_num in range(1, len(report_df) + 1):
                        for col_num in [5, 6, 9]: # الأعمدة الرقمية المهمة (Paid, Overpayment, مستحق الدفع)
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
                    file_name="etisalat_report_april_2026_updated.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )

        with exp_col2:
            if st.button("تصدير PDF"):
                doc = SimpleDocTemplate("report.pdf", pagesize=landscape(A4))
                elements = []
                
                styles = getSampleStyleSheet()
                title = Paragraph("تقرير فواتير أبريل 2026 - شركة اتصالات (محدث)", styles['Title'])
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
                        file_name="etisalat_report_april_2026_updated.pdf",
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
                    file_name="etisalat_report_april_2026_updated.png",
                    mime="image/png"
                )

    else:
        st.info("اضغط على زر 'تحديث النظام وحساب المدفوعات' لرؤية النتائج بعد إدخال القيم الجديدة.")

else:
    st.info(f"صفحة '{menu}' قيد الإنشاء.")
