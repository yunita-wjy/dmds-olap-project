import pandas as pd
import mysql.connector
import json
from dbconfig.mysql_config import mydb, mycursor
from dbconfig.mongo_config import db, product_coll, orders_coll

def create_mysql_tables():
    """Buat tabel MySQL untuk data relational"""
    
    # Table customers
    mycursor.execute("""
        CREATE TABLE IF NOT EXISTS customers (
            customer_id VARCHAR(20) PRIMARY KEY,
            customer_name VARCHAR(100),
            segment VARCHAR(50)
        )
    """)
    
    # Table products  
    mycursor.execute("""
        CREATE TABLE IF NOT EXISTS products (
            product_id VARCHAR(50) PRIMARY KEY,
            product_name TEXT,
            category VARCHAR(50),
            sub_category VARCHAR(50)
        )
    """)
    
    # Table locations
    mycursor.execute("""
        CREATE TABLE IF NOT EXISTS locations (
            location_id VARCHAR(10) PRIMARY KEY,
            city VARCHAR(100),
            state VARCHAR(100),
            country VARCHAR(100),
            region VARCHAR(50),
            market VARCHAR(50),
            postal_code VARCHAR(20)
        )
    """)
    
    # Table orders (fact table)
    mycursor.execute("""
        CREATE TABLE IF NOT EXISTS orders (
            id INT AUTO_INCREMENT PRIMARY KEY,
            order_id VARCHAR(50),
            customer_id VARCHAR(20),
            product_id VARCHAR(50),
            location_id VARCHAR(10),
            sales DECIMAL(10,2),
            quantity INT,
            discount DECIMAL(5,4),
            profit DECIMAL(10,2),
            shipping_cost DECIMAL(10,2),
            order_date DATE,
            ship_date DATE,
            ship_mode VARCHAR(50),
            order_priority VARCHAR(50),
            FOREIGN KEY (customer_id) REFERENCES customers(customer_id),
            FOREIGN KEY (product_id) REFERENCES products(product_id),
            FOREIGN KEY (location_id) REFERENCES locations(location_id)
        )
    """)
    
    mydb.commit()
    print("✅ Tabel MySQL berhasil dibuat!")

def export_csv_to_mysql():
    """Export data CSV ke MySQL"""
    
    # Import customers
    customers = pd.read_csv("data/customer.csv")
    for _, row in customers.iterrows():
        mycursor.execute("""
            INSERT IGNORE INTO customers (customer_id, customer_name, segment)
            VALUES (%s, %s, %s)
        """, tuple(row))
    
    # Import products
    products = pd.read_csv("data/product.csv") 
    for _, row in products.iterrows():
        mycursor.execute("""
            INSERT IGNORE INTO products (product_id, product_name, category, sub_category)
            VALUES (%s, %s, %s, %s)
        """, tuple(row))
    
    # Import locations
    locations = pd.read_csv("data/location.csv")
    for _, row in locations.iterrows():
        mycursor.execute("""
            INSERT IGNORE INTO locations VALUES (%s, %s, %s, %s, %s, %s, %s)
        """, tuple(row))
    
    # Import orders
    orders = pd.read_csv("data/orders.csv")
    orders['order_date'] = pd.to_datetime(orders['order_date'])
    orders['ship_date'] = pd.to_datetime(orders['ship_date'])
    
    for _, row in orders.iterrows():
        mycursor.execute("""
            INSERT INTO orders (order_id, customer_id, product_id, location_id, 
                              sales, quantity, discount, profit, shipping_cost,
                              order_date, ship_date, ship_mode, order_priority)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, tuple(row))
    
    mydb.commit()
    print("✅ Data CSV berhasil di-export ke MySQL!")

def export_json_to_mongo():
    """Export data JSON ke MongoDB"""
    
    # Clear existing collections
    product_coll.delete_many({})
    orders_coll.delete_many({})
    
    # Import product catalog
    with open("data/product_catalog.json", "r") as f:
        product_data = json.load(f)
        product_coll.insert_many(product_data)
    
    # Import order recap  
    with open("data/order_recap.json", "r") as f:
        order_data = json.load(f)
        orders_coll.insert_many(order_data)
    
    print("✅ Data JSON berhasil di-export ke MongoDB!")

if __name__ == "__main__":
    print("🚀 Memulai export data ke database...")
    
    # MySQL export
    create_mysql_tables()
    export_csv_to_mysql()
    
    # MongoDB export  
    export_json_to_mongo()
    
    print("🎉 Semua data berhasil di-export!")