import streamlit as st
import pandas as pd
import plotly.express as px
import re

# Title
st.title("🧪 INFUGEN Pharma Extractor")
st.markdown("An all-in-one tool for extracting human-use pharmaceutical APIs, analyzing top traded items, and identifying key customers — adaptable for any country dataset.")

# Upload Excel file
uploaded_file = st.file_uploader("Upload Pharmaceutical Trade Excel File", type=["xlsx"])

if uploaded_file:
    df = pd.read_excel(uploaded_file, sheet_name=0)

    # Clean numeric columns
    for col in ["Quantity", "FOB (INR)", "Item Rate(INR)"]:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)

    # Extract API from Product Name (simple heuristic)
    def extract_api(product_name):
        return re.split(r"[-+/() ]", str(product_name).upper())[0]

    df["API"] = df["Product Name"].apply(extract_api)

    # Convert INR to USD if applicable
    if "FOB (INR)" in df.columns:
        df["FOB (USD)"] = df["FOB (INR)"] * 0.012
    elif "FOB (USD)" not in df.columns:
        df["FOB (USD)"] = 0

    # Filter to include only human-use APIs (handle NaN safely)
    human_keywords = ["TABLET", "CAPSULE", "INJECTION", "SYRUP", "CREAM", "OINTMENT", "DROPS"]
    df_human = df[df["Product Name"].fillna("").str.upper().str.contains('|'.join(human_keywords), na=False)]

    # Sidebar filters
    with st.sidebar:
        st.header("Filters")
        unique_customers = df_human["Foreign Company"].dropna().unique()
        selected_customer = st.selectbox("Select a Customer (optional)", ["All"] + sorted(unique_customers.tolist()))

        unique_apis = df_human["API"].dropna().unique()
        selected_api = st.selectbox("Select an API (optional)", ["All"] + sorted(unique_apis.tolist()))

    # Apply filters
    filtered_df = df_human.copy()
    if selected_customer != "All":
        filtered_df = filtered_df[filtered_df["Foreign Company"] == selected_customer]

    if selected_api != "All":
        filtered_df = filtered_df[filtered_df["API"] == selected_api]

    # Replace bar charts with tables for these two sections

    st.subheader("📦 Top 10 Human-use Products by FOB (USD)")
    top_products_value = filtered_df.groupby("Product Name")["FOB (USD)"].sum().nlargest(10).reset_index()
    st.dataframe(top_products_value.style.format({"FOB (USD)": "${:,.2f}"}))

    st.subheader("⚖️ Top 10 Human-use Products by Quantity")
    top_products_qty = filtered_df.groupby("Product Name")["Quantity"].sum().nlargest(10).reset_index()
    st.dataframe(top_products_qty.style.format({"Quantity": "{:,.0f}"}))

    st.subheader("🧪 Top 5 Human-use APIs by Value & Volume")
    top_mol_value = filtered_df.groupby("API")["FOB (USD)"].sum().nlargest(5).reset_index()
    top_mol_qty = filtered_df.groupby("API")["Quantity"].sum().nlargest(5).reset_index()

    col1, col2 = st.columns(2)
    with col1:
        st.markdown("**Top 5 APIs by Value (USD)**")
        st.dataframe(top_mol_value)
    with col2:
        st.markdown("**Top 5 APIs by Quantity**")
        st.dataframe(top_mol_qty)

    st.subheader("🏆 Top 10 Importing Customers (Human-use)")
    top_customers = filtered_df.groupby("Foreign Company")["FOB (USD)"].sum().nlargest(10).reset_index()
    st.dataframe(top_customers)

    # Export section
    st.download_button("📅 Download Human-use Dataset", data=filtered_df.to_csv(index=False), file_name="humanuse_data.csv", mime="text/csv")

else:
    st.info("Please upload a pharmaceutical trade Excel file to begin analysis.")
