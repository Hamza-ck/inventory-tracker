import streamlit as st
import datetime
import pandas as pd
from sheet_config import connect_sheet

st.set_page_config(page_title="Farhan Inventory", layout="wide")

# Connect to Google Sheet
sheet = connect_sheet("Inventory Tracker")
sales_log = sheet.worksheet("Sales_Log")
purchase_log = sheet.worksheet("Purchases_Log")

# Load purchase & sales data
purchase_data = purchase_log.get_all_records()
sales_data = sales_log.get_all_records()
df_pur = pd.DataFrame(purchase_data)
df_sale = pd.DataFrame(sales_data)

for df in [df_pur, df_sale]:
    df.columns = df.columns.str.strip()

# Clean & process data
df_pur['Total Value'] = df_pur['Total Value'].replace({'₹': ''}, regex=True).astype(float)
df_pur['Quantity'] = df_pur['Quantity'].astype(int)
df_pur['Purchase Price'] = df_pur['Purchase Price'].astype(float)
df_sale['Selling Price'] = df_sale['Selling Price'].astype(float)
df_sale['Quantity Sold'] = df_sale['Quantity Sold'].astype(int)

# Dashboard
st.title("📊 Farhan Inventory Dashboard")

total_products = df_pur['Quantity'].sum()
total_investment = df_pur['Total Value'].sum()
stock_left = total_products - df_sale['Quantity Sold'].sum()
total_sales = df_sale['Quantity Sold'].sum()
total_sales_value = (df_sale['Quantity Sold'] * df_sale['Selling Price']).sum()
net_profit = total_sales_value - total_investment

st.markdown("### Summary")
col1, col2, col3 = st.columns(3)
col1.metric("Total Products", total_products)
col2.metric("Total Investment", f"₹{total_investment:,.0f}")
col3.metric("Stock Left", stock_left)

col4, col5, col6 = st.columns(3)
col4.metric("Total Sales Qty", total_sales)
col5.metric("Total Sales Value", f"₹{total_sales_value:,.0f}")
col6.metric("Net Profit", f"₹{net_profit:,.0f}")

# Stock Table
st.markdown("### Current Stock Table")
stock = df_pur.groupby(['Model', 'Color'])['Quantity'].sum().reset_index()
sale_qty = df_sale.groupby(['Model', 'Color'])['Quantity Sold'].sum().reset_index()
stock = pd.merge(stock, sale_qty, on=['Model', 'Color'], how='left').fillna(0)
stock['Current Qty'] = stock['Quantity'] - stock['Quantity Sold']
stock = pd.merge(stock, df_pur[['Model', 'Color', 'Purchase Price']].drop_duplicates(), on=['Model', 'Color'], how='left')
stock = pd.merge(stock, df_sale[['Model', 'Color', 'Selling Price']].drop_duplicates(), on=['Model', 'Color'], how='left')
stock['Stock Value'] = stock['Current Qty'] * stock['Purchase Price']
stock['Status'] = stock['Current Qty'].apply(lambda x: "In Stock" if x > 5 else ("Low Stock" if x > 0 else "Out of Stock"))

st.dataframe(stock[['Model', 'Color', 'Current Qty', 'Purchase Price', 'Selling Price', 'Stock Value', 'Status']])

# Tabs for entry
tab1, tab2 = st.tabs(["➕ Add Purchase", "💸 Add Sale"])

# Model suggestion helper
def get_model_suggestions(typed_text, model_list):
    if len(typed_text) >= 3:
        return [m for m in model_list if typed_text.lower() in m.lower()]
    return []

# ---- PURCHASE FORM ----
with tab1:
    st.subheader("➕ Purchase Entry")
    with st.form("purchase_form"):
        model_input = st.text_input("Model Name")
        all_models = sorted(df_pur['Model'].unique())
        suggestions = get_model_suggestions(model_input, all_models)
        if suggestions:
            st.info("Suggestions: " + ", ".join(suggestions))

        color = st.text_input("Color")
        quantity = st.number_input("Quantity", min_value=1, step=1)
        price = st.number_input("Purchase Price per Unit", min_value=0.0, step=0.5)
        date = st.date_input("Purchase Date", value=datetime.date.today())
        supplier = st.text_input("Supplier Name")
        payment_method = st.selectbox("Payment Method", ["Cash", "UPI", "Card", "Bank Transfer"])

        submit = st.form_submit_button("Add Purchase Entry")

        if submit:
            total_value = quantity * price
            purchase_log.append_row([
                model_input, color, quantity, price, total_value,
                str(date), supplier, payment_method
            ])
            st.success(f"✔️ Purchase entry added for {model_input} ({quantity})")

# ---- SALES FORM ----
with tab2:
    st.subheader("💸 Sale Entry")
    with st.form("sales_form", clear_on_submit=True):
        model_input = st.text_input("Model Name (Sale)")
        all_models_sale = sorted(df_pur['Model'].unique())
        suggestions = get_model_suggestions(model_input, all_models_sale)
        if suggestions:
            st.info("Suggestions: " + ", ".join(suggestions))

        color = st.text_input("Color")
        quantity_sold = st.number_input("Quantity Sold", min_value=1, step=1)
        selling_price = st.number_input("Selling Price per Unit", min_value=0.0, step=0.5)
        date_of_sale = st.date_input("Date of Sale", value=datetime.date.today())
        customer_name = st.text_input("Customer Name")
        customer_phone = st.text_input("Customer Phone")
        payment_method = st.selectbox("Payment Method", ["Cash", "UPI", "Card", "Bank Transfer"])

        total_sale = quantity_sold * selling_price
        st.markdown(f"**Total Amount: ₹{total_sale:,.2f}**")

        submit_sale = st.form_submit_button("Submit Sale")

        if submit_sale:
            sales_log.append_row([
                str(date_of_sale), model_input, color, quantity_sold,
                selling_price, customer_name, payment_method, customer_phone,
                total_sale
            ])
            st.success("✔️ Sale entry submitted!")
            st.balloons()
