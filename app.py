import streamlit as st
import pandas as pd
import os

st.set_page_config(layout="wide")

# ================= STYLE =================
st.markdown("""
<style>
.stApp { background-color: #f8f9fa; font-family: 'Tajawal', sans-serif; }

h1 {
    color: #0B6B3A;
    text-align: center;
    font-weight: 800;
}

thead tr th {
    background-color: #0B6B3A !important;
    color: white !important;
    text-align: center !important;
    font-size: 14px !important;
}

td { text-align: center; }

[data-testid="stMetric"] {
    background: white;
    border: 1px solid #0B6B3A;
    padding: 10px;
    border-radius: 10px;
}
</style>
""", unsafe_allow_html=True)

# ================= SETTINGS =================
month = st.text_input("📅 الشهر", "April 2026")

lang = st.radio("🌍 اللغة", ["عربي", "English"], horizontal=True)

st.title(f"6.133531 حساب منطقة البحر الاحمر للتامين الصحي - {month} - اجمالى فواتير")

# ================= DB =================
DB = "database.xlsx"

if not os.path.exists(DB):
    pd.DataFrame(columns=["Account","Spoc","Mobile","Previous","Invoice"])\
        .to_excel(DB, sheet_name="master", index=False)

master = pd.read_excel(DB, sheet_name="master")

if "Invoice" not in master.columns:
    master["Invoice"] = 0

master["Invoice"] = pd.to_numeric(master["Invoice"], errors="coerce").fillna(0)
master["Previous"] = pd.to_numeric(master["Previous"], errors="coerce").fillna(0)

# ================= Upload =================
st.subheader("📂 رفع البيانات الأساسية")

file = st.file_uploader("Upload Master Excel", type=["xlsx"])

if file:
    df_upload = pd.read_excel(file)
    if "Invoice" not in df_upload.columns:
        df_upload["Invoice"] = 0
    df_upload.to_excel(DB, sheet_name="master", index=False)
    st.success("تم حفظ البيانات")

# ================= INPUT =================
st.subheader("✍️ تحديث القيم الحالية")

if not master.empty:

    input_df = st.data_editor(
        master[["Mobile","Previous"]].rename(columns={"Previous":"Current"}),
        use_container_width=True
    )

    credit = st.number_input("💰 المبلغ المجنب", value=0.0)

    excluded_accounts = st.multiselect(
        "🚫 الحسابات المستثناة",
        master["Account"].unique()
    )

    if st.button("🚀 تحديث النظام"):

        df = master.merge(input_df, on="Mobile", how="left")

        df["Current"] = pd.to_numeric(df["Current"], errors="coerce").fillna(df["Previous"])
        df["Paid"] = df["Previous"] - df["Current"]

        df["Priority"] = False

        edited_df = st.data_editor(
            df,
            column_config={
                "Priority": st.column_config.CheckboxColumn("أولوية")
            },
            use_container_width=True
        )

        df = edited_df.sort_values(by=["Priority","Paid"], ascending=[False, False])

        # ================= RENAME =================
        display_df = df.copy()

        if lang == "عربي":
            display_df = display_df.rename(columns={
                "Account": "Account No.",
                "Spoc": "Spoc",
                "Mobile": "Phone Sub Account",
                "Invoice": f"الفاتورة الصادرة {month}",
                "Current": "مستحق الدفع",
                "Paid": "المدفوع",
                "Priority": "أولوية"
            })

            cols = ["Account No.","Spoc","Phone Sub Account",
                    f"الفاتورة الصادرة {month}","مستحق الدفع","المدفوع","أولوية"]

        else:
            display_df = display_df.rename(columns={
                "Account": "Account No.",
                "Spoc": "Spoc",
                "Mobile": "Phone Sub Account",
                "Invoice": f"Issued Invoice {month}",
                "Current": "Amount Due",
                "Paid": "Paid",
                "Priority": "Priority"
            })

            cols = ["Account No.","Spoc","Phone Sub Account",
                    f"Issued Invoice {month}","Amount Due","Paid","Priority"]

        # ================= FORMAT =================
        for col in display_df.columns:
            if col not in ["Account No.","Spoc","Phone Sub Account","Priority"]:
                display_df[col] = pd.to_numeric(display_df[col], errors="coerce").fillna(0)
                display_df[col] = display_df[col].map("{:,.0f}".format)

        # ================= STYLE =================
        def highlight(row):
            if row.iloc[-1] == True:
                return ["background-color: #d4edda"] * len(row)
            return [""] * len(row)

        styled = display_df[cols].style.apply(highlight, axis=1)

        st.subheader("📋 التقرير الأساسي")
        st.dataframe(styled, use_container_width=True)

        # ================= الحسابات =================
        total_system = df["Current"].sum()
        excluded_total = df[df["Account"].isin(excluded_accounts)]["Current"].sum()
        net_due = total_system - excluded_total
        final_due = net_due - credit

        st.subheader("📊 الإجماليات")

        c1, c2, c3, c4 = st.columns(4)

        c1.metric("إجمالي السيستم", f"{int(total_system):,}")
        c2.metric("المستثنى", f"{int(excluded_total):,}")
        c3.metric("بعد الاستثناء", f"{int(net_due):,}")
        c4.metric("بعد المجنب", f"{int(final_due):,}")

        # ================= تقرير الدفع =================
        payment_report = df[df["Current"] > 0][["Current","Mobile","Account"]]

        if lang == "عربي":
            payment_report.columns = ["مبلغ مستحق","Phone Sub Account","Account No."]
        else:
            payment_report.columns = ["Amount Due","Phone Sub Account","Account No."]

        payment_report = payment_report.sort_values(by=payment_report.columns[0], ascending=False)

        st.subheader("📄 تقرير الدفع")
        st.dataframe(payment_report, use_container_width=True)

        total_payment = payment_report.iloc[:,0].sum()
        st.metric("💰 الإجمالي", f"{int(total_payment):,}")

        # ================= تحميل =================
        payment_report.to_excel("payment_report.xlsx", index=False)

        with open("payment_report.xlsx","rb") as f:
            st.download_button("📥 تحميل Excel", f)

        # ================= تحديث =================
        df["Previous"] = df["Current"]

        df[["Account","Spoc","Mobile","Previous","Invoice"]]\
            .to_excel(DB, sheet_name="master", index=False)
