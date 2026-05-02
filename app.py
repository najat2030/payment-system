import streamlit as st
import pandas as pd
import os

st.set_page_config(layout="wide")

# ================= العنوان =================
month = st.text_input("📅 الشهر", "April 2026")
st.title(f"6.133531 حساب منطقة البحر الاحمر للتامين الصحي - {month} - اجمالى فواتير")

# ================= قاعدة البيانات =================
DB = "database.xlsx"

if not os.path.exists(DB):
    pd.DataFrame(columns=["Account","Spoc","Mobile","Previous","Invoice"])\
        .to_excel(DB, sheet_name="master", index=False)

master = pd.read_excel(DB, sheet_name="master")

# ================= تأكيد وجود Invoice =================
if "Invoice" not in master.columns:
    master["Invoice"] = 0

# تنظيف القيم
master["Invoice"] = pd.to_numeric(master["Invoice"], errors="coerce").fillna(0)
master["Previous"] = pd.to_numeric(master["Previous"], errors="coerce").fillna(0)

# ================= رفع البيانات =================
st.subheader("📂 رفع البيانات الأساسية (مرة واحدة)")
file = st.file_uploader("Upload Master Excel", type=["xlsx"])

if file:
    df_upload = pd.read_excel(file)

    if "Invoice" not in df_upload.columns:
        df_upload["Invoice"] = 0

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

    # ================= الحسابات المستثناة =================
    excluded_accounts = st.multiselect(
        "🚫 اختاري الحسابات المستثناة",
        master["Account"].unique()
    )

    if st.button("🚀 تحديث النظام"):

        df = master.merge(input_df, on="Mobile", how="left")

        df["Current"] = pd.to_numeric(df["Current"], errors="coerce").fillna(df["Previous"])

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

        st.dataframe(
            df[["Account","Spoc","Mobile","Invoice","Current","Paid","Priority"]],
            use_container_width=True
        )

        # ================= الحسابات =================
        total_system = df["Current"].sum()
        excluded_total = df[df["Account"].isin(excluded_accounts)]["Current"].sum()
        net_due = total_system - excluded_total
        final_due = net_due - credit

        # ================= عرض الإجماليات =================
        st.subheader("📊 الإجماليات")

        col1, col2, col3, col4 = st.columns(4)

        col1.metric("إجمالي السيستم", f"{int(total_system):,} جنيه")
        col2.metric("المستثنى", f"{int(excluded_total):,} جنيه")
        col3.metric("بعد الاستثناء", f"{int(net_due):,} جنيه")
        col4.metric("بعد خصم المجنب", f"{int(final_due):,} جنيه")

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

        df[["Account","Spoc","Mobile","Previous","Invoice"]]\
            .to_excel(DB, sheet_name="master", index=False)
