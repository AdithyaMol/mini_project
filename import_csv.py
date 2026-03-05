import sqlite3
import pandas as pd

csv_path = "data/amazon_products.csv"  # ✅ method 2

df = pd.read_csv(csv_path)

conn = sqlite3.connect("products.db")

df.to_sql(
    "amazon_products",
    conn,
    if_exists="append",
    index=False
)

conn.commit()
conn.close()

print("✅ Data inserted successfully")
