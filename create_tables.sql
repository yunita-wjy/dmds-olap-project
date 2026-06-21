-- Create database and tables
CREATE DATABASE IF NOT EXISTS dmds_olap_project;
USE dmds_olap_project;

CREATE TABLE IF NOT EXISTS product (
    product_id VARCHAR(10) PRIMARY KEY,
    product_name TEXT,
    category VARCHAR(100),
    sub_category VARCHAR(100)
);

CREATE TABLE IF NOT EXISTS orders (
    order_id VARCHAR(20) PRIMARY KEY,
    customer_id VARCHAR(20),
    product_id VARCHAR(10),
    location_id VARCHAR(10),
    sales DECIMAL(10,2),
    quantity INT,
    discount DECIMAL(5,4),
    profit DECIMAL(10,2),
    shipping_cost DECIMAL(10,2),
    order_date DATE,
    ship_date DATE,
    ship_mode VARCHAR(50),
    order_priority VARCHAR(50)
);