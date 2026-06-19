import pandas as pd
from dbconfig.mongo_config import db
from dbconfig.mysql_config import mydb

product_coll = db["product_catalog"]
orders_coll = db["order_recap"]

customer_df = pd.read_sql("SELECT * FROM customer", mydb)
orders_fact = pd.read_sql("SELECT * FROM orders", mydb)
product_df = pd.read_sql("SELECT * FROM product", mydb)
location_df = pd.read_sql("SELECT * FROM location", mydb)

def load_hidden_value():
    query_fact = ("SELECT product_id, COUNT(DISTINCT order_id) AS frequency, SUM(profit) AS total_profit, SUM(sales) AS total_sales "
                  "FROM orders GROUP BY product_id;")
    df_fact = pd.read_sql(query_fact, mydb)

    # merge with table product to get category, sub_category, etc
    df_final = df_fact.merge(product_df[["product_id", "product_name"]], on="product_id", how="left")

    # merge with product collection to get variant and type
    df_mongo = pd.DataFrame(list(product_coll.find()))
    df_mongo = df_mongo.drop(columns=["_id"])

    df_final = df_final.merge(df_mongo, on="product_id", how="left")

    return df_final

def load_trap_product():
    ...

def load_discount():
    ...