import streamlit as st
import datetime
import pandas as pd
import plotly.express as px
from sheet_config import connect_sheet

st.markdown('''
    <style>
    section[data-testid="stSidebar"] {
        background: #1e293b;
        color: #f1f5f9;
        border-right: 1px solid #334155;
    }
    .main, .block-container {
        background: #f8fafc !important;
        color: #1e293b !important;
    }
    div[data-testid="stMetric"] {
        background: #1e293b;
        color: #f1f5f9 !important;
        border-radius: 0.75rem;
        box-shadow: 0 2px 8px 0 #e5e7eb;
        padding: 1.2em 0.5em 1.2em 1em;
        margin-bottom: 1em;
    }
    div[data-testid="stMetric"] > div:first-child {
        color: #f1f5f9 !important;
    }
    div[data-testid="stMetric"] label {
        color: #f1f5f9 !important;
    }
    div[data-testid="stMetric"] div[data-testid="stMetricLabel"] {
        color: #f1f5f9 !important;
    }
    .stDataFrame, .stTable {
        background: #fff !important;
        border-radius: 0.5rem;
        box-shadow: 0 2px 8px 0 #e5e7eb;
        color: #1e293b !important;
    }
    h1, h2, h3, h4, h5, h6 {
        color: #1e293b !important;
        font-family: 'Inter', 'Segoe UI', Arial, sans-serif;
    }
    .stButton > button {
        background: #2563eb;
        color: #fff;
        border-radius: 0.5rem;
        border: none;
        padding: 0.5em 1.2em;
        font-weight: 600;
        transition: background 0.2s;
    }
    .stButton > button:hover {
        background: #1d4ed8;
    }
    .stTextInput > div > input, .stNumberInput > div > input, .stDateInput > div > input {
        background: #f1f5f9;
        border-radius: 0.5rem;
        border: 1px solid #e5e7eb;
        color: #1e293b;
    }
    .stAlert.info {
        background: #e0e7ff;
        color: #1e293b;
        border-radius: 0.5rem;
    }
    /* Form labels */
    label, .st-emotion-cache-1kyxreq, .st-emotion-cache-1c7y2kd, .st-emotion-cache-1wmy9hl {
        color: #1e293b !important;
        font-weight: 600;
    }
    /* Metrics labels */
    div[data-testid="stMarkdown"] p, div[data-testid="stMetricLabel"] > div, div[data-testid="stMetricValue"] > div {
        color: #f1f5f9 !important;
    }
    </style>
''', unsafe_allow_html=True)

# Connect to the sheet
sheet = connect_sheet("Inventory Tracker")
# Select the correct worksheet
purchase_log = sheet.worksheet("Purchases_Log")

# Add a sidebar for navigation
st.sidebar.title("Navigation")
page = st.sidebar.radio("Go to", ["Inventory Dashboard", "Add Purchase", "Add Sale", "Scan Paper Input"])

if page == "Inventory Dashboard":
    st.title("📊 Inventory Dashboard")
    # Load data
    purchase_data = purchase_log.get_all_records()
    sales_log = sheet.worksheet("Sales_Log")
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
    # Connect to the sales worksheet
    sales_log = sheet.worksheet("Sales_Log")
    st.title("💸 Add Sale Entry")
    with st.form("sales_form"):
        # Fetch unique models and colors from purchase log for dropdowns
        purchase_data = purchase_log.get_all_records()
        models = sorted(list(set([row["Model"] for row in purchase_data])))
        colors = sorted(list(set([row["Color"] for row in purchase_data])))

        Model = st.selectbox("Model", models)
        Color = st.selectbox("Color", colors)
        Quantity_sold = st.number_input("Quantity Sold", min_value=1, step=1)
        Selling_price = st.number_input("Selling Price per Unit", min_value=0.0, step=0.5)
        date_of_sale = st.date_input("Date of Sale", value=datetime.date.today())
        Customer_name = st.text_input("Customer Name (Optional)", max_chars=50)
        # Show total sale live
        Total_sale = Quantity_sold * Selling_price
        st.info(f"Total Sale: ₹{Total_sale}")
        submit_sale = st.form_submit_button("Submit Sale")

    if submit_sale:
        total_sale = Quantity_sold * Selling_price
        sales_log.append_row([
        str(date_of_sale),  # Date
        Model,              # Model
        Color,              # Color
        Quantity_sold,      # Quantity Sold
        Selling_price,      # Selling Price
        Customer_name,      # Customer Name
        Total_sale          # Total Sale Value
    ])
        st.success(f"✔️ Sale added: {Model} | {Color} | Qty: {Quantity_sold} | ₹{total_sale}")

elif page == "Scan Paper Input":
    st.title("📷 Scan Paper Input")
    st.info("Write like → Model: A15, Qty: 10, Price: 25")
    img_file = st.camera_input("Open Camera")
    model, qty, price = '', '', ''
    if img_file is not None:
        import pytesseract
        import cv2
        import numpy as np
        file_bytes = np.asarray(bytearray(img_file.read()), dtype=np.uint8)
        img = cv2.imdecode(file_bytes, 1)
        text = pytesseract.image_to_string(img)
        # Simple extraction logic
        import re
        model_match = re.search(r'Model[:\s]*([\w-]+)', text, re.IGNORECASE)
        qty_match = re.search(r'Qty[:\s]*(\d+)', text, re.IGNORECASE)
        price_match = re.search(r'Price[:\s]*(\d+\.?\d*)', text, re.IGNORECASE)
        model = model_match.group(1) if model_match else ''
        qty = qty_match.group(1) if qty_match else ''
        price = price_match.group(1) if price_match else ''
        st.image(img, caption="Preview Image")
        st.write(f"Extracted Text: {text}")
    with st.form("scan_purchase_form"):
        model_val = st.text_input("Model", value=model)
        qty_val = st.number_input("Quantity", min_value=1, value=int(qty) if qty else 1, step=1)
        price_val = st.number_input("Purchase Price", min_value=0.0, value=float(price) if price else 0.0, step=0.5)
        # Fetch unique colors from purchase log for dropdown
        purchase_data = purchase_log.get_all_records()
        colors = sorted(list(set([row["Color"] for row in purchase_data])))
        color_val = st.selectbox("Color", colors)
        date_val = st.date_input("Arrival Date", value=datetime.date.today())
        submit_scan = st.form_submit_button("Save Purchase")
    if submit_scan:
        total_value = qty_val * price_val
        purchase_log.append_row([
            model_val,
            color_val,
            qty_val,
            price_val,
            total_value,
            str(date_val)
        ])
        st.success(f"✔️ Entry added: {model_val} | {color_val} | Qty: {qty_val} | ₹{total_value}")
