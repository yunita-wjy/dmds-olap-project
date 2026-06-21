# FILTER GEOGRAFIS YANG BENAR - BERDASARKAN DATA ASLI

import pandas as pd
import streamlit as st

# Load data dengan JOIN location
@st.cache_data
def load_geographic_data():
    # JOIN orders, product, location
    query = """
    SELECT o.*, p.product_name, p.category, p.sub_category,
           l.city, l.state, l.country, l.region, l.market
    FROM orders o
    JOIN product p ON o.product_id = p.product_id  
    JOIN location l ON o.location_id = l.location_id
    """
    return pd.read_sql(query, connection)

df = load_geographic_data()

# REGION FILTER (Data Asli)
regions = [
    "Africa", "Canada", "Caribbean", "Central", "Central Asia", 
    "East", "EMEA", "North", "North Asia", "Oceania", 
    "South", "Southeast Asia", "West"
]

selected_region = st.selectbox(
    "Choose Region",
    ["All"] + regions
)

# COUNTRY FILTER (Cascade berdasarkan Region)
if selected_region != "All":
    filtered_countries = df[df["region"] == selected_region]["country"].unique()
else:
    filtered_countries = df["country"].unique()

selected_country = st.multiselect(
    "Filter Country",
    filtered_countries,
    default=filtered_countries
)

# MARKET FILTER  
markets = df["market"].unique()  # US, APAC, EU, Africa, LATAM, Canada
selected_market = st.selectbox(
    "Choose Market", 
    ["All"] + list(markets)
)

# APPLY FILTERS
filtered_df = df.copy()

if selected_region != "All":
    filtered_df = filtered_df[filtered_df["region"] == selected_region]
    
if selected_country:
    filtered_df = filtered_df[filtered_df["country"].isin(selected_country)]
    
if selected_market != "All":
    filtered_df = filtered_df[filtered_df["market"] == selected_market]

print("DATA GEOGRAFIS ASLI:")
print("Regions:", regions)
print("Total Countries:", len(df["country"].unique()))
print("Markets:", list(df["market"].unique()))