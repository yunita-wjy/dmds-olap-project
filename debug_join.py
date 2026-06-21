import pandas as pd

# Load data exactly like the app
orders_df = pd.read_csv('data/orders.csv')
products_df = pd.read_csv('data/product.csv') 
location_df = pd.read_csv('data/location.csv')

print("=== RAW DATA ===")
print(f"Orders: {len(orders_df)} rows")
print(f"Products: {len(products_df)} rows")
print(f"Locations: {len(location_df)} rows")

print("\n=== LOCATION REGIONS (before merge) ===")
print(location_df['region'].value_counts())

# INNER JOIN like the app
df = orders_df.merge(products_df, on='product_id', how='inner')
print(f"\nAfter product merge: {len(df)} rows")

df = df.merge(location_df, on='location_id', how='inner')
print(f"After location merge: {len(df)} rows")

print("\n=== FINAL REGIONS (after merge) ===")
if not df.empty:
    print(df['region'].value_counts())
    print(f"\nUnique regions: {df['region'].unique()}")
else:
    print("NO DATA AFTER MERGE!")

# Check what location_ids are in orders vs location
print("\n=== LOCATION ID ANALYSIS ===")
orders_locations = set(orders_df['location_id'].unique())
location_locations = set(location_df['location_id'].unique())

print(f"Unique location_ids in orders: {len(orders_locations)}")
print(f"Unique location_ids in location: {len(location_locations)}")
print(f"Matching location_ids: {len(orders_locations.intersection(location_locations))}")

# Missing location_ids
missing = orders_locations - location_locations
if missing:
    print(f"Missing location_ids in location.csv: {len(missing)}")
    print(f"First 5 missing: {list(missing)[:5]}")