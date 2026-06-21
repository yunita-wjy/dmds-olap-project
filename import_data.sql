-- Create database and use it
CREATE DATABASE IF NOT EXISTS dmds_olap_project;
USE dmds_olap_project;

-- Create product table
CREATE TABLE IF NOT EXISTS product (
    product_id VARCHAR(10) PRIMARY KEY,
    product_name TEXT,
    category VARCHAR(100),
    sub_category VARCHAR(100)
);

-- Create orders table
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
    order_priority VARCHAR(50),
    FOREIGN KEY (product_id) REFERENCES product(product_id)
);

-- Load product data
LOAD DATA LOCAL INFILE 'C:/laragon/www/dmds-olap-project/data/product.csv'
INTO TABLE product
FIELDS TERMINATED BY ','
ENCLOSED BY '"'
LINES TERMINATED BY '\n'
IGNORE 1 ROWS
(product_name, category, sub_category, product_id);

-- Load orders data
LOAD DATA LOCAL INFILE 'C:/laragon/www/dmds-olap-project/data/orders.csv'
INTO TABLE orders
FIELDS TERMINATED BY ','
ENCLOSED BY '"'
LINES TERMINATED BY '\n'
IGNORE 1 ROWS;