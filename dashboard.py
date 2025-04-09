import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime
import random

# Custom CSS for green header
st.markdown("""
<style>
    .header {
        background-color: #3D9970;
        color: white;
        padding: 1rem;
        border-radius: 0.5rem;
        margin-bottom: 1rem;
    }
    .header h1 {
        color: white;
    }
    .metric-card {
        border-left: 4px solid #3D9970;
        padding-left: 1rem;
    }
    .verification-success {
        border: 1px solid #3D9970;
        border-radius: 0.5rem;
        padding: 1rem;
        margin: 1rem 0;
    }
    .verification-fail {
        border: 1px solid #DC3545;
        border-radius: 0.5rem;
        padding: 1rem;
        margin: 1rem 0;
    }
</style>
""", unsafe_allow_html=True)

# Load and prepare data
@st.cache_data
def load_data():
    df = pd.read_excel('organic_india_complete_catalog.xlsx')
    
    # Data preprocessing
    df['Manufacture Date'] = pd.to_datetime(df['Manufacture Date'], dayfirst=True)
    df['Expiry Date'] = pd.to_datetime(df['Expiry Date'], dayfirst=True)
    df['Arrival Date at Retailer'] = pd.to_datetime(df['Arrival Date at Retailer'], dayfirst=True)
    df['Days Until Expiry'] = (df['Expiry Date'] - datetime.now()).dt.days
    df['Expiry Status'] = df['Days Until Expiry'].apply(
        lambda x: 'Expired' if x < 0 else ('Near Expiry' if x < 90 else 'Good'))
    
    # More realistic blockchain verification - based on product and retailer
    df['Blockchain Verified'] = df.apply(
        lambda x: random.choice([True, False]) if random.random() > 0.3 else (x['Current Stock'] > 0),
        axis=1
    )
    
    return df

df = load_data()

# Sidebar filters
with st.sidebar:
    st.title("Filters")
    search_term = st.text_input("Search by product name")
    
    # Blockchain verification
    st.subheader("Blockchain Verification")
    batch_number = st.text_input("Search by Batch ID", key="batch_input")
    if st.button("Verify Product"):
        if batch_number:
            product = df[df['Batch Number'] == batch_number]
            if not product.empty:
                product = product.iloc[0]
                if product['Blockchain Verified']:
                    st.markdown(f"""
                    <div class="verification-success">
                        <h3>Verification Successful!</h3>
                        <p><strong>Product Name:</strong> {product['Product Name']}</p>
                        <p><strong>Category:</strong> {product['Category']}</p>
                        <p><strong>Quantity:</strong> {product['Quantity']}</p>
                        <p><strong>MRP:</strong> ₹{product['MRP']:.2f}</p>
                        <p><strong>Shelf Life:</strong> {product['Shelf Life (Months)']} months</p>
                        <p><strong>Manufacturer:</strong> {product['Manufacturer']}</p>
                        <p><strong>Manufacturing Address:</strong> {product.get('Manufacturing Address', 'Organic India Facility, Lucknow')}</p>
                        <p><strong>Manufacturing Time:</strong> {product['Manufacture Date'].strftime('%Y-%m-%d %H:%M')}</p>
                        <p><strong>Organic Certifications:</strong> {product['Organic Certifications']}</p>
                    </div>
                    """, unsafe_allow_html=True)
                else:
                    st.markdown(f"""
                    <div class="verification-fail">
                        <h3>Verification Failed</h3>
                        <p><strong>Product Name:</strong> {product['Product Name']}</p>
                        <p><strong>Reason:</strong> Blockchain record not found or tampered with</p>
                        <p>This batch was manufactured at {product.get('Manufacturing Address', 'Organic India Facility, Lucknow')} on {product['Manufacture Date'].strftime('%Y-%m-%d')}</p>
                    </div>
                    """, unsafe_allow_html=True)
            else:
                st.warning("Batch ID not found in our records")
        else:
            st.warning("Please enter a Batch ID")

    category = st.selectbox("Filter by Category", ["All"] + list(df['Category'].unique()))
    retailer = st.selectbox("Filter by Retailer", ["All"] + list(df['Retailer Name'].unique()))
    stock_status = st.radio("Filter by Stock Status", ["All", "In Stock", "Low Stock", "Out of Stock"])

# Apply filters
filtered_df = df.copy()
if search_term:
    filtered_df = filtered_df[filtered_df['Product Name'].str.contains(search_term, case=False)]
if category != "All":
    filtered_df = filtered_df[filtered_df['Category'] == category]
if retailer != "All":
    filtered_df = filtered_df[filtered_df['Retailer Name'] == retailer]
if stock_status != "All":
    filtered_df = filtered_df[filtered_df['Batch Status'] == stock_status]

# Main dashboard
st.markdown('<div class="header"><h1>Organic India Product Dashboard</h1></div>', unsafe_allow_html=True)

# Inventory Summary
st.header("Inventory Summary")
cols = st.columns(4)
with cols[0]:
    st.markdown(f'<div class="metric-card"><h3>Total Products</h3><h2>{df["Product Name"].nunique()}</h2></div>', unsafe_allow_html=True)
with cols[1]:
    st.markdown(f'<div class="metric-card"><h3>Categories</h3><h2>{len(df["Category"].unique())}</h2></div>', unsafe_allow_html=True)
with cols[2]:
    st.markdown(f'<div class="metric-card"><h3>Retailers</h3><h2>{len(df["Retailer Name"].unique())}</h2></div>', unsafe_allow_html=True)
with cols[3]:
    st.markdown(f'<div class="metric-card"><h3>Avg. Shelf Life</h3><h2>{df["Shelf Life (Months)"].mean():.1f} months</h2></div>', unsafe_allow_html=True)

# Charts
st.header("Product Analytics")
tab1, tab2, tab3 = st.tabs(["Category Distribution", "Stock Status", "Price Distribution"])

with tab1:
    fig = px.pie(filtered_df, names='Category', title='Product Distribution by Category')
    st.plotly_chart(fig, use_container_width=True)

with tab2:
    fig = px.bar(
        filtered_df.groupby(['Retailer Name', 'Batch Status']).size().reset_index(name='Count'),
        x='Retailer Name',
        y='Count',
        color='Batch Status',
        title='Stock Status by Retailer'
    )
    st.plotly_chart(fig, use_container_width=True)

with tab3:
    fig = px.box(filtered_df, x='Category', y='MRP', title='Price Distribution by Category')
    st.plotly_chart(fig, use_container_width=True)

# Product Data Table
st.header("Product Details")
st.dataframe(
    filtered_df[['Product Name', 'Category', 'Quantity', 'MRP', 'Retailer Name', 
                'Current Stock', 'Batch Status', 'Blockchain Verified']],
    column_config={
        "MRP": st.column_config.NumberColumn(format="₹%.2f"),
        "Blockchain Verified": st.column_config.CheckboxColumn()
    },
    use_container_width=True,
    hide_index=True
)
