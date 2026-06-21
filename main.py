import pandas as pd

customer = pd.read_csv("data/customer.csv")
product = pd.read_csv("data/product.csv")
location = pd.read_csv("data/location.csv")
orders = pd.read_csv("data/orders.csv")


pd.set_option('display.max_columns', None)  # kolom
pd.set_option('display.max_rows', None)     # baris
pd.set_option('display.width', 1000)        # ga patah ke bawah



print("CUSTOMER:", customer.shape)
print("PRODUCT:", product.shape)
print("LOCATION:", location.shape)
print("ORDERS:", orders.shape)

print("\nORDERS SAMPLE:")
print(orders.head())

print("\nNULL CHECK:")
print(orders.isnull().sum())

print("\nDUPLICATE CHECK:")
print("Orders duplicate:", orders.duplicated().sum())

missing_products = orders[~orders["product_id"].isin(product["product_id"])]
print("Missing product relations:", missing_products.shape)

print("Total Sales:", orders["sales"].sum())
print("Total Profit:", orders["profit"].sum())
print("Average Discount:", orders["discount"].mean())


bins = [0,0.1,0.2,0.3,0.4,0.5,0.6,0.7,1.0]
labels = ["0-10%","10-20%","20-30%","30-40%","40-50%","50-60%","60-70%","70%+"]

orders["discount_bucket"] = pd.cut(orders["discount"], bins=bins, labels=labels)

discount_analysis = orders.groupby("discount_bucket").agg({
    "profit":"mean",
    "sales":"mean"
})

print("\nDISCOUNT ANALYSIS:")
print(discount_analysis)

# ---

# =========================
# TRAP PRODUCT
# =========================

df = orders.merge(product, on="product_id")

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

df_region = df.merge(location, on="location_id")

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
