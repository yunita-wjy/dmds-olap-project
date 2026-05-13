import json
import pandas as pd

df = pd.read_csv("data/Global_Superstore.csv", encoding="utf-8", sep=";", decimal=",")


def split_product(name):
    parts = [p.strip() for p in str(name).split(',')]

    full_name = parts[0] if len(parts) > 0 else None
    type_ = parts[1] if len(parts) > 1 else None
    variant = parts[2] if len(parts) > 2 else None

    return pd.Series([full_name, type_, variant])


def build_attributes(row):
    attr = {}

    if pd.notna(row["Type"]):
        attr["Type"] = row["Type"]

    if pd.notna(row["Variant"]):
        attr["Variant"] = row["Variant"]

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
df[['Full Name', 'Type', 'Variant']] = df['Product Name'].apply(split_product)
df["Order Date"] = pd.to_datetime(df["Order Date"], format="%d-%m-%Y")
df["Ship Date"] = pd.to_datetime(df["Ship Date"], format="%d-%m-%Y")

# -------------------------
#      Customer Table
# -------------------------
df_customer = df[['Customer ID', 'Customer Name', 'Segment']].drop_duplicates().reset_index(drop=True)
write_to_file(df_customer, "data/customer.csv", "csv")

# -------------------------
#      Product Table
# -------------------------
df_product = df[['Product ID', 'Product Name', 'Category', 'Sub-Category']].drop_duplicates().reset_index(drop=True)
write_to_file(df_product, "data/product.csv", "csv")

# -------------------------
#      Location Table
# -------------------------
df_location = df[['City', 'State', 'Country', 'Region', 'Market', 'Postal Code']].drop_duplicates().reset_index(
    drop=True)
df_location['Location ID'] = df_location.index + 1
df_location['Location ID'] = df_location['Location ID'].astype(str).str.zfill(4)
write_to_file(df_location, "data/location.csv", "csv")

# -------------------------
#        Fact Table
# -------------------------
loc_cols = ['City', 'State', 'Country', 'Region', 'Market', 'Postal Code']

# merge df awal dengan dim_location untuk dapet Loc ID
df_fact = df.merge(
    df_location,
    on=loc_cols,
    how='left'
)

df_fact = df_fact[[
    'Order ID',
    'Customer ID',
    'Product ID',
    'Location ID',
    'Sales',
    'Quantity',
    'Discount',
    'Profit',
    'Shipping Cost',
    'Order Date',
    'Ship Date',
    'Ship Mode',
    'Order Priority'
]]

write_to_file(df_fact, "data/orders.csv", "csv")

# -------------------------
#     product_catalog
# -------------------------
df_product_catalog = df[
    ['Product ID', 'Full Name', 'Category', 'Sub-Category', 'Type', 'Variant']].drop_duplicates().reset_index(drop=True)
df_product_catalog["attributes"] = df_product_catalog.apply(build_attributes, axis=1)
df_product_catalog = df_product_catalog.rename(columns={
    "Product ID": "product_id",
    "Category": "category",
    "Sub-Category": "sub_category"
})
df_product_catalog = df_product_catalog.drop(columns=["Type", "Variant"])
write_to_file(df_product_catalog, "data/product_catalog.json", "json")

# -------------------------
#       order_recap
# -------------------------
df_order_recap = df[[
    'Order ID',
    'Order Date',
    'Customer ID',
    'Ship Date',
    'Ship Mode',
    'Product ID',
    'Sales',
    'Quantity',
    'Discount',
    'Profit',
    'Shipping Cost'
]]

df_order_recap["delay"] = (df_order_recap["Ship Date"] - df_order_recap["Order Date"]).dt.days

order_docs = []

for order_id, group in df_order_recap.groupby("Order ID"):

    doc = {
        "order_id": order_id,
        "order_date": group["Order Date"].iloc[0].strftime("%d-%m-%Y"),
        "customer_id": group["Customer ID"].iloc[0],

        "products": [],

        "total_profit": round(group["Profit"].sum(),3),
        "total_sales": round(group["Sales"].sum(),3),

        "shipping": {
            "ship_mode": group["Ship Mode"].iloc[0],
            "ship_date": group["Ship Date"].iloc[0].strftime("%d-%m-%Y"),
            "delay": int(group["delay"].iloc[0]),
            "shipping_cost": round(group["Shipping Cost"].sum(),3)
        }
    }

    # isi products array
    for _, row in group.iterrows():
        doc["products"].append({
            "product_id": row["Product ID"],
            "quantity": row["Quantity"],
            "sales": row["Sales"],
            "profit": row["Profit"],
            "discount": row["Discount"]
        })

    order_docs.append(doc)

write_to_file(order_docs, "data/order_recap.json", "json")

# Testing
print(df.dtypes)
# print(df.columns)
# print(df_fact)
