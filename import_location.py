import pandas as pd
import mysql.connector

# MySQL connection
conn = mysql.connector.connect(
    host='localhost',
    user='root',
    password='',
    database='dmds_olap_project'
)
cursor = conn.cursor()

# Import location data
df_location = pd.read_csv('data/location.csv')

# Clean location data - remove empty rows
df_location = df_location.dropna(subset=['location_id'])
df_location = df_location[df_location['location_id'].str.strip() != '']

print(f"Importing {len(df_location)} location records...")

for _, row in df_location.iterrows():
    try:
        cursor.execute('''
            INSERT IGNORE INTO location VALUES (%s, %s, %s, %s, %s, %s, %s)
        ''', (
            row['location_id'], 
            row['city'], 
            row['state'], 
            row['country'], 
            row['region'], 
            row['market'], 
            str(row['postal_code']) if pd.notna(row['postal_code']) else None
        ))
    except Exception as e:
        print(f"Error inserting row {row['location_id']}: {e}")

conn.commit()
print("Location data imported successfully!")

# Test query
cursor.execute("SELECT COUNT(*) FROM location")
count = cursor.fetchone()[0]
print(f"Total location records: {count}")

cursor.execute("SELECT DISTINCT region FROM location ORDER BY region")
regions = [r[0] for r in cursor.fetchall()]
print(f"Regions: {regions}")

conn.close()