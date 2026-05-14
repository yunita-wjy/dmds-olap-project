import json
import pandas as pd

df = pd.read_csv("data/Global_Superstore.csv", encoding="utf-8", sep=";", decimal=",")
df = df.rename(columns={
    "Row ID": "row_id",
    "Order ID": "order_id",
    "Order Date": "order_date",
    "Ship Date": "ship_date",
    "Ship Mode": "ship_mode",
    "Customer ID": "customer_id",
    "Customer Name": "customer_name",
    "Segment": "segment",
    "City": "city",
    "State": "state",
    "Country": "country",
    "Postal Code": "postal_code",
    "Market": "market",
    "Region": "region",
    "Product ID": "product_id",
    "Category": "category",
    "Sub-Category": "sub_category",
    "Product Name": "product_name",
    "Sales": "sales",
    "Quantity": "quantity",
    "Discount": "discount",
    "Profit": "profit",
    "Shipping Cost": "shipping_cost",
    "Order Priority": "order_priority"
})

def split_product(name):
    parts = [p.strip() for p in str(name).split(',')]

    full_name = parts[0] if len(parts) > 0 else None
    type_ = parts[1] if len(parts) > 1 else None
    variant = parts[2] if len(parts) > 2 else None

    return pd.Series([full_name, type_, variant])


def build_attributes(row):
    attr = {}

    if pd.notna(row["type"]):
        attr["type"] = row["type"]

    if pd.notna(row["variant"]):
        attr["variant"] = row["variant"]

    return attr


def write_to_file(data, filename, format):
    if format == "csv":
        data.to_csv(filename, index=False)
    elif format == "json":
        # kalau DataFrame
        if isinstance(data, pd.DataFrame):
            data.to_json(filename, orient="records", indent=2)

        # kalau list/dict
        elif isinstance(data, (list, dict)):
            with open(filename, "w") as f:
                json.dump(data, f, indent=2)

        else:
            raise ValueError("Unsupported data type for JSON")

    print("File: ", filename, " has been written.")


# GENERAL CLEAN
df[['full_name', 'type', 'variant']] = df['product_name'].apply(split_product)
df["order_date"] = pd.to_datetime(df["order_date"], format="%d-%m-%Y")
df["ship_date"] = pd.to_datetime(df["ship_date"], format="%d-%m-%Y")

# -------------------------
#      Customer Table
# -------------------------
df_customer = df[['customer_id', 'customer_name', 'segment']].drop_duplicates().reset_index(drop=True)
write_to_file(df_customer, "data/customer.csv", "csv")

# -------------------------
#      Product Table
# -------------------------
df_product = df[['product_id', 'product_name', 'category', 'sub_category']].drop_duplicates().reset_index(drop=True)
write_to_file(df_product, "data/product.csv", "csv")

# -------------------------
#      Location Table
# -------------------------
df_location = df[['city', 'state', 'country', 'region', 'market', 'postal_code']].drop_duplicates().reset_index(
    drop=True)
df_location['location_id'] = df_location.index + 1
df_location['location_id'] = df_location['location_id'].astype(str).str.zfill(4)
write_to_file(df_location, "data/location.csv", "csv")

# -------------------------
#        Fact Table
# -------------------------
loc_cols = ['city', 'state', 'country', 'region', 'market', 'postal_code']

# merge df awal dengan dim_location untuk dapet Loc ID
df_fact = df.merge(
    df_location,
    on=loc_cols,
    how='left'
)

df_fact = df_fact[[
    'order_id',
    'customer_id',
    'product_id',
    'location_id',
    'sales',
    'quantity',
    'discount',
    'profit',
    'shipping_cost',
    'order_date',
    'ship_date',
    'ship_mode',
    'order_priority'
]]

write_to_file(df_fact, "data/orders.csv", "csv")

# -------------------------
#     product_catalog
# -------------------------
df_product_catalog = df[
    ['product_id', 'full_name', 'category', 'sub_category', 'type', 'variant']].drop_duplicates().reset_index(drop=True)
df_product_catalog["attributes"] = df_product_catalog.apply(build_attributes, axis=1)
df_product_catalog = df_product_catalog.drop(columns=["type", "variant"])
write_to_file(df_product_catalog, "data/product_catalog.json", "json")

# -------------------------
#       order_recap
# -------------------------
df_order_recap = df[[
    'order_id',
    'order_date',
    'customer_id',
    'ship_date',
    'ship_mode',
    'product_id',
    'sales',
    'quantity',
    'discount',
    'profit',
    'shipping_cost'
]]

df_order_recap["delay"] = (df_order_recap["ship_date"] - df_order_recap["order_date"]).dt.days

order_docs = []

for order_id, group in df_order_recap.groupby("order_id"):

    doc = {
        "order_id": order_id,
        "order_date": group["order_date"].iloc[0].strftime("%d-%m-%Y"),
        "customer_id": group["customer_id"].iloc[0],

        "products": [],

        "total_profit": round(group["profit"].sum(),3),
        "total_sales": round(group["sales"].sum(),3),

        "shipping": {
            "ship_mode": group["ship_mode"].iloc[0],
            "ship_date": group["ship_date"].iloc[0].strftime("%d-%m-%Y"),
            "delay": int(group["delay"].iloc[0]),
            "shipping_cost": round(group["shipping_cost"].sum(),3)
        }
    }

    # isi products array
    for _, row in group.iterrows():
        doc["products"].append({
            "product_id": row["product_id"],
            "quantity": row["quantity"],
            "sales": row["sales"],
            "profit": row["profit"],
            "discount": row["discount"]
        })

    order_docs.append(doc)

write_to_file(order_docs, "data/order_recap.json", "json")

# Testing
print(df.dtypes)
# print(df.columns)
# print(df_fact)
