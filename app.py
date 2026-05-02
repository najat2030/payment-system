import streamlit as st
import pandas as pd
import os
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle
from reportlab.lib import colors
import matplotlib.pyplot as plt

st.set_page_config(layout="wide")

DB = "database.xlsx"
PRIMARY = "#0B6B3A"  # Royal Green

# ================= STYLE =================
st.markdown(f"""
<style>
.stApp {{
    background-color: #f8f9fa;
    font-family: 'Tajawal', sans-serif;
}}
.card {{
    background: white;
    padding: 20px;
    border-radius: 15px;
    text-align: center;
    box-shadow: 0 4px 15px rgba(0,0,0,0.1);
}}
.card h3 {{
    color: {PRIMARY};
    margin-bottom: 10px;
}}
.card p {{
    font-size: 22px;
    font-weight: bold;
}}
</style>
""", unsafe_allow_html=True)

# ================= INIT DB =================
if not os.path.exists(DB):
    pd.DataFrame(columns=["Account","Spoc","Mobile","Previous","Invoice_April_2026","Type"])\
        .to_excel(DB, sheet_name="master", index=False)

st.title("📊 Telecom Payment System")

# ================= UPLOAD =================
st.subheader("📂 رفع البيانات الأساسية")
file = st.file_uploader("Upload Excel", type=["xlsx"])

if file:
    df_upload = pd.read_excel(file)

    if "Type" not in df_upload.columns:
        df_upload["Type"] = "Normal"

    df_upload = df_upload.fillna(0)
    df_upload = df_upload.replace("No Show", 0)

    df_upload.to_excel(DB, sheet_name="master", index=False)
    st.success("تم حفظ البيانات بنجاح")

    st.rerun()

# ================= LOAD =================
master = pd.read_excel(DB, sheet_name="master")

# ================= SESSION STATE =================
if "current_data" not in st.session_state:
    st.session_state.current_data = master[master["Type"] != "NonPayment"][["Mobile","Previous"]]\
        .rename(columns={"Previous":"Current"})

# ================= INPUT =================
st.subheader("✍️ تحديث القيم الحالية")

with st.form("update_form"):

    edited_df = st.data_editor(
        st.session_state.current_data,
        use_container_width=True,
        num_rows="dynamic"
    )

    submit = st.form_submit_button("🚀 تحديث النظام")

# ================= UPDATE =================
if submit:

    st.session_state.current_data = edited_df.copy()

    df = master.merge(st.session_state.current_data, on="Mobile", how="left")
    df["Current"] = df["Current"].fillna(df["Previous"])

    # ================= الحسابات =================
    df["Paid"] = df.apply(
        lambda row: 0 if row["Type"] == "NonPayment"
        else row["Previous"] - row["Current"],
        axis=1
    )

    df["Overpayment"] = df["Current"].apply(lambda x: abs(x) if x < 0 else 0)

    df["Collection"] = df.apply(
        lambda row: 0 if row["Type"] == "NonPayment"
        else min(row["Paid"], row["Previous"]),
        axis=1
    )

    df["Priority"] = False

    # ================= SAVE =================
    df.loc[df["Type"] != "NonPayment", "Previous"] = df["Current"]
    df.to_excel(DB, sheet_name="master", index=False)

    st.success("تم التحديث بنجاح ✅")

    # ================= DASHBOARD =================
    normal_df = df[df["Type"] != "NonPayment"]

    c1, c2, c3 = st.columns(3)
    c1.markdown(f'<div class="card"><h3>💰 المدفوع</h3><p>{int(normal_df["Paid"].sum()):,}</p></div>', unsafe_allow_html=True)
    c2.markdown(f'<div class="card"><h3>🟢 التحصيل</h3><p>{int(normal_df["Collection"].sum()):,}</p></div>', unsafe_allow_html=True)
    c3.markdown(f'<div class="card"><h3>🔴 Overpayment</h3><p>{int(normal_df["Overpayment"].sum()):,}</p></div>', unsafe_allow_html=True)

    # ================= STYLE TABLE =================
    def highlight(row):
        styles = []
        for col in row.index:
            style = ""
            if row["Type"] == "NonPayment":
                style = "background-color:#d4edda"
            if isinstance(row[col], (int, float)) and row[col] < 0:
                style = "color:red;font-weight:bold"
            styles.append(style)
        return styles

    st.subheader("📋 التقرير الأساسي")
    st.write(df.style.apply(highlight, axis=1).format("{:,.2f}"))

    # ================= PAYMENT REPORT =================
    def format_val(row):
        if row["Type"] == "NonPayment":
            return f"Non Payment - {row['Previous']}"
        return row["Current"]

    df["Display"] = df.apply(format_val, axis=1)

    payment = df[["Display","Mobile","Account"]]
    payment.columns = ["مبلغ مستحق","Phone","Account"]

    payment = payment.sort_values(by="مبلغ مستحق", ascending=False)

    total = normal_df["Current"].sum()

    st.subheader("📄 تقرير الدفع")
    st.dataframe(payment, use_container_width=True)
    st.metric("💰 إجمالي المطلوب", f"{int(total):,} جنيه")

    # ================= EXPORT =================
    payment.loc[len(payment)] = [total, "", "الإجمالي"]

    payment.to_excel("report.xlsx", index=False)
    with open("report.xlsx","rb") as f:
        st.download_button("📥 Excel", f)

    # PDF
    doc = SimpleDocTemplate("report.pdf")
    data = [payment.columns.tolist()] + payment.values.tolist()
    table = Table(data)
    table.setStyle(TableStyle([
        ('BACKGROUND',(0,0),(-1,0),colors.darkgreen),
        ('TEXTCOLOR',(0,0),(-1,0),colors.white),
        ('GRID',(0,0),(-1,-1),1,colors.black)
    ]))
    doc.build([table])
    with open("report.pdf","rb") as f:
        st.download_button("📄 PDF", f)

    # Image
    fig, ax = plt.subplots(figsize=(10,6))
    ax.axis('off')
    ax.table(cellText=payment.values, colLabels=payment.columns, loc='center')
    plt.savefig("report.png")
    with open("report.png","rb") as f:
        st.download_button("🖼️ صورة", f)
