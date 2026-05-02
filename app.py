import streamlit as st
import pandas as pd
import os
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle
from reportlab.lib import colors
import matplotlib.pyplot as plt

st.set_page_config(layout="wide")

DB = "database.xlsx"

# ================= إنشاء قاعدة البيانات =================
if not os.path.exists(DB):
    pd.DataFrame(columns=["Account","Spoc","Mobile","Previous","Invoice_April_2026","Type"])\
        .to_excel(DB, sheet_name="master", index=False)

# ================= تحميل البيانات =================
master = pd.read_excel(DB, sheet_name="master")

st.title("📊 Telecom Payment System")

# ================= Upload =================
st.subheader("📂 رفع البيانات الأساسية")

file = st.file_uploader("Upload Excel", type=["xlsx"])

if file:
    df_upload = pd.read_excel(file)

    if "Type" not in df_upload.columns:
        df_upload["Type"] = "Normal"

    # تنظيف القيم
    df_upload = df_upload.fillna(0)

    # تحويل No Show إلى 0
    df_upload = df_upload.replace("No Show", 0)

    df_upload.to_excel(DB, sheet_name="master", index=False)
    st.success("تم حفظ البيانات بنجاح")

# ================= إدخال القيم =================
st.subheader("✍️ تحديث القيم الحالية")

if not master.empty:

    input_df = st.data_editor(
        master[master["Type"] != "NonPayment"][["Mobile","Previous"]]
        .rename(columns={"Previous":"Current"}),
        use_container_width=True
    )

    if st.button("🚀 تحديث النظام"):

        df = master.merge(input_df, on="Mobile", how="left")

        df["Current"] = df["Current"].fillna(df["Previous"])

        # ================= الحسابات =================
        df["Paid"] = df.apply(
            lambda row: 0 if row["Type"] == "NonPayment" else row["Previous"] - row["Current"],
            axis=1
        )

        df["Overpayment"] = df["Current"].apply(
            lambda x: abs(x) if x < 0 else 0
        )

        df["Collection"] = df.apply(
            lambda row: 0 if row["Type"] == "NonPayment"
            else min(row["Paid"], row["Previous"]),
            axis=1
        )

        # ================= Priority =================
        df["Priority"] = False

        df = st.data_editor(
            df,
            column_config={
                "Invoice_April_2026": st.column_config.NumberColumn("Invoice", disabled=True),
                "Priority": st.column_config.CheckboxColumn("🔥 أولوية")
            },
            use_container_width=True
        )

        # ================= تحديث Previous =================
        df.loc[df["Type"] != "NonPayment", "Previous"] = df["Current"]

        df[["Account","Spoc","Mobile","Previous","Invoice_April_2026","Type"]]\
            .to_excel(DB, sheet_name="master", index=False)

        # ================= ترتيب =================
        df = df.sort_values(by="Paid", ascending=False)

        st.subheader("📋 التقرير الأساسي")
        st.dataframe(df, use_container_width=True)

        # ================= الملخص =================
        normal_df = df[df["Type"] != "NonPayment"]

        col1, col2, col3 = st.columns(3)

        col1.metric("💰 إجمالي المدفوع", f"{int(normal_df['Paid'].sum()):,}")
        col2.metric("🟢 التحصيل الفعلي", f"{int(normal_df['Collection'].sum()):,}")
        col3.metric("🔴 Overpayment", f"{int(normal_df['Overpayment'].sum()):,}")

        # ================= تقرير الدفع =================
        def format_value(row):
            if row["Type"] == "NonPayment":
                return f"Non Payment - {row['Previous']}"
            return row["Current"]

        df["Display"] = df.apply(format_value, axis=1)

        payment_report = df[[
            "Display","Mobile","Account","Priority","Type"
        ]]

        payment_report.columns = [
            "مبلغ مستحق",
            "Phone Sub Account",
            "Sub Account",
            "Priority",
            "Type"
        ]

        # ترتيب
        payment_report = payment_report.sort_values(
            by="مبلغ مستحق",
            ascending=False
        )

        st.subheader("📄 تقرير الدفع")
        st.dataframe(payment_report, use_container_width=True)

        total = normal_df["Current"].sum()
        st.metric("💰 إجمالي المطلوب", f"{int(total):,} جنيه")

        # ================= Excel =================
        excel_df = payment_report.copy()

        # إضافة صف الإجمالي
        total_row = pd.DataFrame([{
            "مبلغ مستحق": total,
            "Phone Sub Account": "",
            "Sub Account": "الإجمالي",
            "Priority": "",
            "Type": ""
        }])

        excel_df = pd.concat([excel_df, total_row])

        excel_df.to_excel("payment_report.xlsx", index=False)

        with open("payment_report.xlsx","rb") as f:
            st.download_button("📥 تحميل Excel", f)

        # ================= PDF =================
        def generate_pdf(df):
            file = "report.pdf"
            doc = SimpleDocTemplate(file)

            data = [df.columns.tolist()] + df.values.tolist()

            table = Table(data)
            table.setStyle(TableStyle([
                ('BACKGROUND',(0,0),(-1,0),colors.darkred),
                ('TEXTCOLOR',(0,0),(-1,0),colors.white),
                ('ALIGN',(0,0),(-1,-1),'CENTER'),
                ('GRID',(0,0),(-1,-1),1,colors.black),
            ]))

            doc.build([table])
            return file

        pdf_file = generate_pdf(excel_df)

        with open(pdf_file,"rb") as f:
            st.download_button("📄 تحميل PDF", f)

        # ================= صورة =================
        def generate_image(df):
            fig, ax = plt.subplots(figsize=(10,6))
            ax.axis('off')

            table = ax.table(
                cellText=df.values,
                colLabels=df.columns,
                loc='center'
            )

            file = "report.png"
            plt.savefig(file, bbox_inches='tight')
            return file

        img_file = generate_image(excel_df)

        with open(img_file,"rb") as f:
            st.download_button("🖼️ تحميل صورة", f)
