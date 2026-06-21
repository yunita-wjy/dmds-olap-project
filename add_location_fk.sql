USE dmds_olap_project;

-- Add foreign key constraint to orders table
ALTER TABLE orders ADD CONSTRAINT fk_orders_location 
FOREIGN KEY (location_id) REFERENCES location(location_id);