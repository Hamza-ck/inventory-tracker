import streamlit as st
import datetime
import pandas as pd
import plotly.express as px
from sheet_config import connect_sheet

st.set_page_config(
    page_title="Farhan Inventory",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
    <style>
    :root {
        --primary: #0a3b45;
        --secondary: #4dacb9;
        --accent: #68bbc7;
        --light: #a8d5db;
        --lighter: #cce6ea;
        --white: #f5fbfc;
        --text: #003039;
        --success: #3e8d63;
        --warning: #d9a42e;
    }

    body {
        background-color: var(--primary);
        color: var(--white);
    }

    .container {
        max-width: 1200px;
        margin: 0 auto;
        padding: 20px;
    }

    .navbar {
        background-color: var(--secondary);
        color: var(--text);
        padding: 12px 20px;
        border-radius: 8px;
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 20px;
        box-shadow: 0 4px 15px rgba(0, 0, 0, 0.1);
    }

    .navbar h1 {
        font-size: 24px;
        font-weight: 600;
    }

    .navbar-actions {
        display: flex;
        gap: 10px;
    }

    .button {
        background-color: var(--accent);
        color: var(--text);
        border: none;
        border-radius: 6px;
        padding: 8px 16px;
        cursor: pointer;
        display: flex;
        align-items: center;
        gap: 6px;
        font-weight: 500;
        transition: all 0.2s ease;
        box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
    }

    .button:hover {
        background-color: var(--light);
        transform: translateY(-2px);
    }

    .button.primary {
        background-color: var(--secondary);
    }

    .button.primary:hover {
        background-color: var(--accent);
    }

    .dashboard {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
        gap: 15px;
        margin-bottom: 20px;
    }

    .stat-card {
        background-color: var(--light);
        color: var(--text);
        border-radius: 8px;
        padding: 16px;
        text-align: center;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        transition: transform 0.3s ease;
    }

    .stat-card:hover {
        transform: translateY(-5px);
    }

    .stat-card.highlight {
        background-color: var(--accent);
        grid-column: span 2;
    }

    .content-card {
        background-color: var(--accent);
        border-radius: 12px;
        padding: 20px;
        margin-bottom: 20px;
        box-shadow: 0 6px 12px rgba(0, 0, 0, 0.15);
    }

    .form-grid {
        display: grid;
        grid-template-columns: 1fr 1fr;
        gap: 16px;
    }

    .form-group label {
        font-weight: 500;
        color: var(--text);
    }

    .form-control {
        width: 100%;
        padding: 10px;
        border: 1px solid var(--light);
        border-radius: 6px;
        background-color: var(--white);
        color: var(--text);
        font-size: 16px;
    }

    .form-actions {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-top: 20px;
    }

    .total-amount {
        font-size: 18px;
        font-weight: 600;
        color: var(--text);
    }

    </style>
""", unsafe_allow_html=True)

# Connect to the sheet
sheet = connect_sheet("Inventory Tracker")
sales_log = sheet.worksheet("Sales_Log")
purchase_log = sheet.worksheet("Purchases_Log")

# Sidebar navigation
page = st.sidebar.radio("Go to", ["Inventory Dashboard", "Add Purchase", "Add Sale"])

if page == "Inventory Dashboard":
    st.title("📊 Inventory Dashboard")
    # Load data
    purchase_data = purchase_log.get_all_records()
    sales_data = sales_log.get_all_records()
    df_pur = pd.DataFrame(purchase_data)
    df_pur.columns = df_pur.columns.astype(str).str.strip()
    if 'Model' not in df_pur.columns:
        st.error(f"No Data Found {list(df_pur.columns)}")
        st.stop()
    if not df_pur.empty:
        df_pur['Total Value'] = df_pur['Total Value'].replace({'₹': ''}, regex=True).astype(float)
        df_pur['Purchase Price'] = df_pur['Purchase Price'].replace({'₹': ''}, regex=True).astype(float)
    df_pur['Date'] = pd.to_datetime(df_pur['Date']).dt.date  # Ensure 'Date' is datetime.date
    df_sale = pd.DataFrame(sales_data)
    df_sale.columns = df_sale.columns.astype(str).str.strip()

    # Always show total purchase and sales summary (not filtered)
    total_purchase_qty = df_pur['Quantity'].sum() if not df_pur.empty else 0
    total_purchase_value = df_pur['Total Value'].sum() if not df_pur.empty else 0
    total_sales_qty = df_sale['Quantity Sold'].sum() if not df_sale.empty else 0
    total_sales_value = df_sale['Selling Price'].astype(float).mul(df_sale['Quantity Sold']).sum() if not df_sale.empty else 0
    net_profit = total_sales_value - total_purchase_value

    st.markdown("### Summary (All Data)")
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Total Stock Purchased", f"{total_purchase_qty}")
    col2.metric("Total Investment", f"₹{total_purchase_value:,.0f}")
    col3.metric("Total Sales Qty", f"{total_sales_qty}")
    col4.metric("Total Sales Value", f"₹{total_sales_value:,.0f}")
    st.metric("Net Profit", f"₹{net_profit:,.0f}")

    # Calculate left stock (total purchased - total sold)
    left_stock = total_purchase_qty - total_sales_qty
    st.metric("Left Stock", f"{left_stock}")

    # Sidebar filters
    models = sorted(df_pur['Model'].unique())
    colors = sorted(df_pur['Color'].unique())
    date_min = min(df_pur['Date']) if not df_pur.empty else None
    date_max = max(df_pur['Date']) if not df_pur.empty else None
    date_range = st.sidebar.date_input("Purchase Date Range", [date_min, date_max]) if date_min and date_max else None

    # Sidebar filters for model and color
    model_filter = st.sidebar.multiselect("Filter by Model", models, default=models)
    color_filter = st.sidebar.multiselect("Filter by Color", colors, default=colors)

    # Filter purchase data
    df_pur_f = df_pur[df_pur['Model'].isin(model_filter) & df_pur['Color'].isin(color_filter)]
    if date_range:
        df_pur_f = df_pur_f[
            (df_pur_f['Date'] >= date_range[0]) & (df_pur_f['Date'] <= date_range[1])
        ]

    # Stock calculation
    stock = df_pur_f.groupby(['Model', 'Color'])['Quantity'].sum().reset_index()
    if not df_sale.empty:
        df_sale_f = df_sale[df_sale['Model'].isin(model_filter) & df_sale['Color'].isin(color_filter)]
        sale_qty = df_sale_f.groupby(['Model', 'Color'])['Quantity Sold'].sum().reset_index()
        stock = pd.merge(stock, sale_qty, on=['Model', 'Color'], how='left').fillna(0)
        stock['Current Qty'] = stock['Quantity'] - stock['Quantity Sold']
    else:
        stock['Current Qty'] = stock['Quantity']
    stock = stock[['Model', 'Color', 'Current Qty']]
    st.subheader("Stock Table")
    st.dataframe(stock)

    # Total investment
    total_investment = df_pur_f['Total Value'].astype(float).sum() if not df_pur_f.empty else 0
    st.metric("Total Investment", f"₹{total_investment:,.0f}")

    # Interactive graph: allow user to select graph type and date range
    st.markdown("### Trends")
    graph_type = st.selectbox("Select Trend Graph", ["Profit Trend", "Stock Trend", "Investment Trend"])
    graph_date_range = st.date_input("Graph Date Range", [df_pur['Date'].min(), df_pur['Date'].max()]) if not df_pur.empty else None

    if graph_type == "Profit Trend" and not df_sale.empty:
        df_sale['Date'] = pd.to_datetime(df_sale['Date']).dt.date
        df_sale_f = df_sale[(df_sale['Date'] >= graph_date_range[0]) & (df_sale['Date'] <= graph_date_range[1])]
        df_sale_f['Profit'] = df_sale_f['Selling Price'].astype(float) * df_sale_f['Quantity Sold']
        profit_by_date = df_sale_f.groupby('Date')['Profit'].sum().reset_index()
        fig = px.bar(profit_by_date, x='Date', y='Profit', title='Profit Trend',
            color_discrete_sequence=['#2563eb'],
            template='simple_white')
        fig.update_layout(
            plot_bgcolor='#f8fafc',
            paper_bgcolor='#f8fafc',
            font_color='#1e293b',
            xaxis=dict(showgrid=False),
            yaxis=dict(showgrid=True, gridcolor='#e5e7eb')
        )
        st.plotly_chart(fig, use_container_width=True)
    elif graph_type == "Stock Trend" and not df_pur.empty:
        df_pur['Date'] = pd.to_datetime(df_pur['Date']).dt.date
        df_pur_f = df_pur[(df_pur['Date'] >= graph_date_range[0]) & (df_pur['Date'] <= graph_date_range[1])]
        stock_by_date = df_pur_f.groupby('Date')['Quantity'].sum().reset_index()
        fig = px.bar(stock_by_date, x='Date', y='Quantity', title='Stock Trend',
            color_discrete_sequence=['#2563eb'],
            template='simple_white')
        fig.update_layout(
            plot_bgcolor='#f8fafc',
            paper_bgcolor='#f8fafc',
            font_color='#1e293b',
            xaxis=dict(showgrid=False),
            yaxis=dict(showgrid=True, gridcolor='#e5e7eb')
        )
        st.plotly_chart(fig, use_container_width=True)
    elif graph_type == "Investment Trend" and not df_pur.empty:
        df_pur['Date'] = pd.to_datetime(df_pur['Date']).dt.date
        df_pur_f = df_pur[(df_pur['Date'] >= graph_date_range[0]) & (df_pur['Date'] <= graph_date_range[1])]
        invest_by_date = df_pur_f.groupby('Date')['Total Value'].sum().reset_index()
        fig = px.bar(invest_by_date, x='Date', y='Total Value', title='Investment Trend',
            color_discrete_sequence=['#2563eb'],
            template='simple_white')
        fig.update_layout(
            plot_bgcolor='#f8fafc',
            paper_bgcolor='#f8fafc',
            font_color='#1e293b',
            xaxis=dict(showgrid=False),
            yaxis=dict(showgrid=True, gridcolor='#e5e7eb')
        )
        st.plotly_chart(fig, use_container_width=True)

elif page == "Add Purchase":
    st.title("📦 Add Purchase Entry")
    with st.form("purchase_form"):
        model = st.text_input("Model", max_chars=50)
        color = st.text_input("Color", max_chars=30)
        quantity = st.number_input("Quantity", min_value=1, step=1)
        price = st.number_input("Purchase Price per Unit", min_value=0.0, step=0.5)
        date = st.date_input("Purchase Date", value=datetime.date.today())
        
        submit = st.form_submit_button("➕ Add Entry")

    if submit:
        total_value = quantity * price

        # Insert data in Google Sheet
        purchase_log.append_row([
            model,
            color,
            quantity,
            price,
            total_value,
            str(date)
        ])

        st.success(f"✔️ Entry added: {model} | {color} | Qty: {quantity} | ₹{total_value}")

elif page == "Add Sale":
    st.title("💸 Add Sale Entry")

    # Fetch unique models and colors from purchase log
    purchase_data = purchase_log.get_all_records()
    df_pur = pd.DataFrame(purchase_data)
    models = sorted(df_pur['Model'].unique()) if 'Model' in df_pur.columns else []

    # Sale Entry Form
    st.markdown('<div class="content-card">', unsafe_allow_html=True)
    with st.form("sales_form", clear_on_submit=True):
        col1, col2 = st.columns(2)

        with col1:
            model_input_type = st.radio("Model Input Type", ["Choose from List", "Enter Manually"], horizontal=True)
            if model_input_type == "Choose from List":
                model = st.selectbox("Model Name", models)
            else:
                model = st.text_input("Model Name")

            color = st.text_input("Color")

        with col2:
            quantity_sold = st.number_input("Quantity Sold", min_value=1, step=1)
            selling_price = st.number_input("Selling Price per Unit (₹)", min_value=0.0, step=0.5)

        col3, col4 = st.columns(2)
        with col3:
            date_of_sale = st.date_input("Date of Sale", value=datetime.date.today())
            customer_name = st.text_input("Customer Name")

        with col4:
            payment_method = st.selectbox("Payment Method", ["Cash", "UPI", "Card", "Bank Transfer"])
            customer_phone = st.text_input("Customer Phone")

        total_sale = quantity_sold * selling_price
        st.markdown(f'<div class="total-amount">Total Amount: ₹{total_sale:,.2f}</div>', unsafe_allow_html=True)

        submit_sale = st.form_submit_button("Submit Sale")

    st.markdown('</div>', unsafe_allow_html=True)

    if submit_sale:
        if not model or not color or quantity_sold <= 0 or selling_price <= 0:
            st.error("Please fill all required fields.")
        else:
            sales_log.append_row([
                str(date_of_sale),
                model,
                color,
                quantity_sold,
                selling_price,
                customer_name,
                payment_method,
                customer_phone,
                total_sale
            ])
            st.success("Sale entry added successfully!")
            st.balloons()
