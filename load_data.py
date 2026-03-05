from app import app, db
from sqlalchemy import text


def clean_price(value):
    try:
        value = str(value).replace("₹", "").replace(",", "").strip()
        return float(value)
    except:
        return 0.0


def process_file(file_name, vendor_name):

    print(f"\n📂 Processing {file_name}")

    inserted = 0

    with open(file_name, "r", encoding="utf-8-sig") as f:
        lines = f.readlines()

    header = lines[0].strip().split(",")

    with app.app_context():

        for line in lines[1:]:

            parts = line.strip().split(",")

            # If more than 11 fields, merge extra commas into name
            if len(parts) > 11:
                # asin = parts[0]
                # name may contain extra commas
                extra = len(parts) - 11
                name = ",".join(parts[1:2 + extra])
                remaining = parts[2 + extra:]
                parts = [parts[0], name] + remaining

            if len(parts) != 11:
                print("⚠️ Skipping malformed row")
                continue

            try:
                query = text("""
                    INSERT INTO products 
                    (product_id, name, brand, category, price, rating, 
                     review_count, image_url, product_url, availability, vendor)
                    VALUES 
                    (:product_id, :name, :brand, :category, :price, :rating,
                     :review_count, :image_url, :product_url, :availability, :vendor)
                """)

                db.session.execute(query, {
                    "product_id": parts[0],
                    "name": parts[1],
                    "brand": parts[2],
                    "category": parts[3],
                    "price": clean_price(parts[4]),
                    "rating": float(parts[5]) if parts[5] else 0,
                    "review_count": int(parts[6]) if parts[6] else 0,
                    "image_url": parts[7],
                    "product_url": parts[8],
                    "availability": parts[9],
                    "vendor": vendor_name
                })

                inserted += 1

            except Exception as e:
                print("⚠️ Insert error:", e)

        db.session.commit()

    print(f"✅ {vendor_name} inserted rows:", inserted)


if __name__ == "__main__":

    with app.app_context():
        print("🧹 Clearing table...")
        db.session.execute(text("TRUNCATE TABLE products"))
        db.session.commit()

    process_file("amazon_products.csv", "Amazon")
    process_file("flipkart_products.csv", "Flipkart")
    process_file("products.csv", "OtherVendor")

    print("\n🎉 All datasets inserted successfully!")