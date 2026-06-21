import streamlit as st
import pandas as pd
from dbconfig.mongo_config import *
from dbconfig.mysql_config import *

orders_coll = db["order_recap"]

@st.cache_data
def load_mongo_product():
    product_coll = get_collection("product_catalog")
    df = pd.DataFrame(list(product_coll.find()))
    return df.drop(columns=["_id"])

@st.cache_data
def load_mongo_orders():
    product_coll = get_collection("order_recap")
    df = pd.DataFrame(list(product_coll.find()))
    return df.drop(columns=["_id"])

def fetch_sql(query):
    mydb = get_connection()
    df = pd.read_sql(query, mydb)
    mydb.close()
    return df

@st.cache_data
def load_customer():
    return fetch_sql("SELECT * FROM customer")

@st.cache_data
def load_product():
    return fetch_sql("SELECT * FROM product")

@st.cache_data
def load_location():
    return fetch_sql("SELECT * FROM location")

@st.cache_data
def load_hidden_value():
    mydb = get_connection()
    query_fact = """
        SELECT product_id, 
            SUM(quantity) AS total_qty, 
            COUNT(DISTINCT order_id) AS frequency, 
            SUM(profit) AS total_profit, 
            SUM(sales) AS total_sales, 
            l.region 
        FROM orders o 
        JOIN location l ON o.location_id = l.location_id 
        GROUP BY o.product_id, l.region"""
    df_fact = pd.read_sql(query_fact, mydb)
    mydb.close()

    product_df = load_product()
    df_mongo = load_mongo_product()

    # merge with table product to get category, sub_category, etc
    df_final = df_fact.merge(product_df[["product_id", "product_name"]], on="product_id", how="left")

    # merge with product collection to get variant and type
    df_final = df_final.merge(df_mongo, on="product_id", how="left")

    return df_final

def load_trap_product():
    ...

def load_discount():
    ...