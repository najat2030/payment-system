import streamlit as st
import pandas as pd
import os

st.set_page_config(layout="wide")

# ================= عنوان متغير =================
month = st.text_input("📅 الشهر", "April 2026")

st.title(f"6.133531 حساب منطقة البحر الاحمر للتامين الصحي - {month} - اجمالى فواتير")

# ================= قاعدة البيانات =================
DB = "database.xlsx"

if not os.path.exists(DB):
    pd.DataFrame(columns=["Account","Spoc","Mobile","Previous"])\
        .to_excel(DB, sheet_name="master", index=False)

master = pd.read_excel(DB, sheet_name="master")

# ================= رفع البيانات =================
st.subheader("📂 رفع البيانات الأساسية (مرة واحدة)")

file = st.file_uploader("Upload Master Excel", type=["xlsx"])

if file:
    df_upload = pd.read_excel(file)
    df_upload.to_excel(DB, sheet_name="master", index=False)
    st.success("تم حفظ البيانات الأساسية")

# ================= إدخال القيم =================
st.subheader("✍️ تحديث القيم الحالية من OPay")

if not master.empty:

    input_df = st.data_editor(
        master[["Mobile","Previous"]].rename(columns={"Previous":"Current"}),
        use_container_width=True
    )

    # ================= المبلغ المجنب =================
    credit = st.number_input("💰 المبلغ المجنب (Credit)", value=0.0)

    if st.button("🚀 تحديث النظام"):

        df = master.merge(input_df, on="Mobile", how="left")

        df["Current"] = df["Current"].fillna(df["Previous"])

        # ================= حساب المدفوع =================
        df["Paid"] = df["Previous"] - df["Current"]

        # ================= Priority =================
        df["Priority"] = False

        edited_df = st.data_editor(
            df,
            column_config={
                "Priority": st.column_config.CheckboxColumn("أولوية الدفع")
            },
            use_container_width=True
        )

        # ================= ترتيب =================
        df = edited_df.sort_values(
            by=["Priority","Paid"],
            ascending=[False, False]
        )

        # ================= عرض التقرير =================
        st.subheader("📋 التقرير الأساسي")
        st.dataframe(df, use_container_width=True)

        # ================= حساب الإجماليات =================
        total_system = df["Current"].sum()
        total_paid = df["Paid"].sum()
        final_due = total_system - credit

        col1, col2, col3 = st.columns(3)

        col1.metric("💰 إجمالي السيستم", f"{int(total_system):,} جنيه")
        col2.metric("💸 إجمالي المدفوع", f"{int(total_paid):,} جنيه")
        col3.metric("📉 بعد خصم المجنب", f"{int(final_due):,} جنيه")

        # ================= تقرير الدفع =================
        payment_report = df[df["Current"] > 0][[
            "Current","Mobile","Account"
        ]]

        payment_report.columns = [
            "مبلغ مستحق",
            "Phone Sub Account",
            "Sub Account"
        ]

        payment_report = payment_report.sort_values(
            by="مبلغ مستحق",
            ascending=False
        )

        st.subheader("📄 تقرير الدفع")
        st.dataframe(payment_report, use_container_width=True)

        total_payment = payment_report["مبلغ مستحق"].sum()
        st.metric("💰 إجمالي المطلوب للدفع", f"{int(total_payment):,} جنيه")

        # ================= تحميل Excel =================
        payment_report.to_excel("payment_report.xlsx", index=False)

        with open("payment_report.xlsx","rb") as f:
            st.download_button(
                "📥 تحميل تقرير الدفع Excel",
                f,
                file_name="payment_report.xlsx"
            )

        # ================= تحديث القيم =================
        df["Previous"] = df["Current"]

        df[["Account","Spoc","Mobile","Previous"]]\
            .to_excel(DB, sheet_name="master", index=False)
