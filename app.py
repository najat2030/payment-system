import streamlit as st
import pandas as pd
import os
from datetime import datetime

st.set_page_config(layout="wide")

DB = "database.xlsx"

# إنشاء قاعدة بيانات لو مش موجودة
if not os.path.exists(DB):
    pd.DataFrame(columns=["Account","Spoc","Mobile","Previous"])\
        .to_excel(DB, sheet_name="master", index=False)

# تحميل البيانات
master = pd.read_excel(DB, sheet_name="master")

st.title("📊 Telecom Payment System")

# ================= Upload أول مرة =================
st.subheader("📂 رفع البيانات الأساسية")
file = st.file_uploader("Upload Excel", type=["xlsx"])

if file:
    df = pd.read_excel(file)
    df.to_excel(DB, sheet_name="master", index=False)
    st.success("تم حفظ البيانات")

# ================= إدخال القيم =================
st.subheader("✍️ تحديث القيم الحالية")

if not master.empty:
    input_df = st.data_editor(
        master[["Mobile","Previous"]].rename(columns={"Previous":"Current"}),
        use_container_width=True
    )

    if st.button("🚀 تحديث النظام"):

        df = master.merge(input_df, on="Mobile", how="left")

        df["Current"] = df["Current"].fillna(df["Previous"])

        df["Paid"] = df["Previous"] - df["Current"]

        df["Priority"] = False

        # تحديث القيم
        df["Previous"] = df["Current"]

        df[["Account","Spoc","Mobile","Previous"]]\
            .to_excel(DB, sheet_name="master", index=False)

        # ترتيب
        df = df.sort_values(by="Paid", ascending=False)

        st.subheader("📋 التقرير")
        st.dataframe(df, use_container_width=True)

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
        st.dataframe(payment_report)

        total = payment_report["مبلغ مستحق"].sum()

        st.metric("💰 إجمالي الدفع", f"{int(total):,} جنيه")

        payment_report.to_excel("payment_report.xlsx", index=False)

        with open("payment_report.xlsx","rb") as f:
            st.download_button("📥 تحميل التقرير", f)
