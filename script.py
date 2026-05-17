import pandas as pd
from dbconfig.mongo_config import db
from dbconfig.mysql_config import mydb

product_coll = db["product_catalog"]
orders_coll = db["order_recap"]

customer_df = pd.read_sql("SELECT * FROM customer", mydb)
orders_fact = pd.read_sql("SELECT * FROM orders", mydb)
product_df = pd.read_sql("SELECT * FROM product", mydb)
location_df = pd.read_sql("SELECT * FROM location", mydb)


print("CUSTOMER:", customer_df.shape)
print("PRODUCT:", product_df.shape)
print("LOCATION:", location_df.shape)
print("ORDERS:", orders_fact.shape)

print("\nORDERS SAMPLE:")
print(orders_fact.head())

print("\nNULL CHECK:")
print(orders_fact.isnull().sum())

print("\nDUPLICATE CHECK:")
print("Orders duplicate:", orders_fact.duplicated().sum())

missing_products = orders_fact[~orders_fact["product_id"].isin(product_df["product_id"])]
print("Missing product relations:", missing_products.shape)

print("Total Sales:", orders_fact["sales"].sum())
print("Total Profit:", orders_fact["profit"].sum())
print("Average Discount:", orders_fact["discount"].mean())


bins = [0,0.1,0.2,0.3,0.4,0.5,0.6,0.7,1.0]
labels = ["0-10%","10-20%","20-30%","30-40%","40-50%","50-60%","60-70%","70%+"]

orders_fact["discount_bucket"] = pd.cut(orders_fact["discount"], bins=bins, labels=labels)

discount_analysis = orders_fact.groupby("discount_bucket").agg({
    "profit":"mean",
    "sales":"mean"
})

print("\nDISCOUNT ANALYSIS:")
print(discount_analysis)

# ---

# =========================
# TRAP PRODUCT
# =========================

df = orders_fact.merge(product_df, on="product_id")

trap = df.groupby("product_name").agg({
    "quantity":"sum",
    "profit":"sum",
    "discount":"mean",
    "order_id":"count"
}).reset_index()

trap.columns = ["product_name","total_quantity","total_profit","avg_discount","order_count"]

trap_products = trap[
    (trap["total_quantity"] > trap["total_quantity"].quantile(0.75)) &
    (trap["total_profit"] < 0)
]

print("\n=== TRAP PRODUCTS ===")
print(trap_products.sort_values("total_profit"))

# =========================
# HIDDEN HIGH VALUE
# =========================

df_region = df.merge(location_df, on="location_id")

hidden = df_region.groupby(["region","sub_category"]).agg({
    "order_id":"count",
    "profit":"sum"
}).reset_index()

hidden.columns = ["region","sub_category","frequency","total_profit"]

hidden_products = hidden[
    (hidden["frequency"] < hidden["frequency"].median()) &
    (hidden["total_profit"] > hidden["total_profit"].median())
]

print("\n=== HIDDEN HIGH VALUE ===")
print(hidden_products.sort_values("total_profit", ascending=False))