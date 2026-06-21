import pandas as pd
import mysql.connector
import os

# MySQL connection
conn = mysql.connector.connect(
    host='localhost',
    user='root',
    password='',
    database='dmds_olap_project'
)
cursor = conn.cursor()

# Create tables
cursor.execute('''
CREATE TABLE IF NOT EXISTS product (
    product_id VARCHAR(50) PRIMARY KEY, -- Diubah jadi 50 karena beberapa ID superstore cukup panjang
    product_name TEXT,
    category VARCHAR(100),
    sub_category VARCHAR(100)
)
''')

cursor.execute('''
CREATE TABLE IF NOT EXISTS orders (
    order_id VARCHAR(50),
    customer_id VARCHAR(50),
    product_id VARCHAR(50),
    location_id VARCHAR(50),
    sales DECIMAL(10,2),
    quantity INT,
    discount DECIMAL(5,4),
    profit DECIMAL(10,2),
    shipping_cost DECIMAL(10,2),
    order_date DATE,
    ship_date DATE,
    ship_mode VARCHAR(50),
    order_priority VARCHAR(50)
)
''') 
# Catatan: Foreign Key sengaja dilepas dulu di sini saat migrasi awal agar data orders tidak mental 
# jika ada product_id di orders yang tidak sengaja terlewat di tabel product.

print("Mengimport data product...")
# Import product data
df_product = pd.read_csv('data/product.csv')
for _, row in df_product.iterrows():
    cursor.execute('''
        INSERT IGNORE INTO product (product_id, product_name, category, sub_category) 
        VALUES (%s, %s, %s, %s)
    ''', (row['product_id'], row['product_name'], row['category'], row['sub_category']))

print("Mengimport data orders (mohon tunggu, data cukup besar)...")
# Import orders data
df_orders = pd.read_csv('data/orders.csv')

# Ubah format tanggal agar sesuai dengan standar MySQL (YYYY-MM-DD)
df_orders['order_date'] = pd.to_datetime(df_orders['order_date']).dt.strftime('%Y-%m-%d')
df_orders['ship_date'] = pd.to_datetime(df_orders['ship_date']).dt.strftime('%Y-%m-%d')

for _, row in df_orders.iterrows():
    # Menyebutkan nama kolom secara spesifik agar tidak eror jika isi CSV kelebihan kolom
    cursor.execute('''
        INSERT IGNORE INTO orders (
            order_id, customer_id, product_id, location_id, sales, 
            quantity, discount, profit, shipping_cost, order_date, 
            ship_date, ship_mode, order_priority
        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
    ''', (
        row['order_id'], row['customer_id'], row['product_id'], row['location_id'], row['sales'],
        row['quantity'], row['discount'], row['profit'], row['shipping_cost'], row['order_date'],
        row['ship_date'], row['ship_mode'], row['order_priority']
    ))

conn.commit()
print("Data imported successfully into dmds_olap_project!")
conn.close()