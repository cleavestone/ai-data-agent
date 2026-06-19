"""
database/seeds/seed.py

Generates realistic fake data and loads it into the database.
Run this once after the schema has been created.

Usage:
    cd ai-data-agent
    uv run python database/seeds/seed.py

What it creates:
    - 20 product categories
    - 200 products
    - 1,000 customers (from 20 countries)
    - 10,000 orders spread over 2 years
    - ~30,000 order items (avg 3 items per order)

Total rows: ~41,220
"""

import asyncio
import random
import sys
import os
from datetime import datetime, timedelta, timezone
from decimal import Decimal

import asyncpg
from dotenv import load_dotenv
from faker import Faker
from pathlib import Path

# Load .env from project root before importing core.config.
# pydantic-settings resolves env_file relative to cwd, which is
# backend/ when using `uv run`, not the project root where .env lives.
# Loading it here puts the values into os.environ so Settings() finds them.
_project_root = Path(__file__).resolve().parent.parent.parent
load_dotenv(_project_root / ".env")

# ─────────────────────────────────────────────────────────────
# Add backend/ to path so we can import core/config.py
# ─────────────────────────────────────────────────────────────
sys.path.append(os.path.join(os.path.dirname(__file__), "..", "..", "backend"))
from core.config import settings

fake = Faker()
Faker.seed(42)          # fixed seed = reproducible data every run
random.seed(42)

# ─────────────────────────────────────────────────────────────
# Reference data — realistic and consistent
# ─────────────────────────────────────────────────────────────

CATEGORIES = [
    ("Electronics",         "Phones, laptops, accessories and gadgets"),
    ("Clothing",            "Men and women fashion, casual and formal"),
    ("Home & Kitchen",      "Appliances, cookware, furniture and decor"),
    ("Sports & Outdoors",   "Equipment, apparel and accessories"),
    ("Books",               "Fiction, non-fiction, textbooks and more"),
    ("Beauty & Personal Care", "Skincare, haircare and grooming"),
    ("Toys & Games",        "Children toys, board games and puzzles"),
    ("Automotive",          "Car parts, accessories and tools"),
    ("Food & Grocery",      "Packaged foods, snacks and beverages"),
    ("Health & Wellness",   "Supplements, fitness and medical supplies"),
    ("Office Supplies",     "Stationery, furniture and equipment"),
    ("Jewellery & Watches", "Rings, necklaces, bracelets and watches"),
    ("Garden & Outdoors",   "Plants, tools and outdoor furniture"),
    ("Pet Supplies",        "Food, toys and accessories for pets"),
    ("Music & Instruments", "Guitars, keyboards and audio equipment"),
    ("Movies & TV",         "DVDs, blu-rays and streaming devices"),
    ("Software",            "Productivity, security and creative tools"),
    ("Baby & Kids",         "Clothing, feeding and nursery products"),
    ("Travel",              "Luggage, travel accessories and adapters"),
    ("Art & Crafts",        "Supplies for painting, drawing and crafting"),
]

# Products per category with realistic price ranges
# (category_name, product_name, base_price, base_cost)
PRODUCTS_TEMPLATE = {
    "Electronics": [
        ("Wireless Earbuds Pro",        149.99, 45.00),
        ("Smartphone Stand Deluxe",      29.99,  8.00),
        ("USB-C Hub 7-in-1",             49.99, 15.00),
        ("Mechanical Keyboard RGB",     119.99, 38.00),
        ("Webcam 4K Ultra",              89.99, 28.00),
        ("Portable Charger 20000mAh",    39.99, 12.00),
        ("Smart Watch Series X",        199.99, 65.00),
        ("Noise Cancelling Headphones", 249.99, 80.00),
        ("Tablet Stand Adjustable",      24.99,  7.00),
        ("Wireless Mouse Ergonomic",     44.99, 14.00),
    ],
    "Clothing": [
        ("Classic Cotton T-Shirt",       19.99,  5.00),
        ("Slim Fit Chinos",              49.99, 15.00),
        ("Running Shorts",               29.99,  9.00),
        ("Wool Blend Sweater",           69.99, 22.00),
        ("Waterproof Jacket",            99.99, 32.00),
        ("Casual Linen Shirt",           39.99, 12.00),
        ("Yoga Leggings",                44.99, 14.00),
        ("Formal Blazer",               129.99, 42.00),
        ("Winter Puffer Coat",          149.99, 48.00),
        ("Denim Jeans Classic",          59.99, 19.00),
    ],
    "Home & Kitchen": [
        ("Stainless Steel Cookware Set", 129.99, 40.00),
        ("Air Fryer 5.8L",               79.99, 25.00),
        ("Coffee Maker Programmable",    59.99, 19.00),
        ("Bamboo Cutting Board Set",     34.99, 10.00),
        ("Cast Iron Skillet 12in",       44.99, 14.00),
        ("Blender High Speed",           69.99, 22.00),
        ("Knife Set Professional",       89.99, 28.00),
        ("Instant Pot 6Qt",             119.99, 38.00),
        ("Toaster Oven Digital",         59.99, 19.00),
        ("Electric Kettle 1.7L",         34.99, 11.00),
    ],
    "Sports & Outdoors": [
        ("Yoga Mat Premium",             39.99, 12.00),
        ("Resistance Bands Set",         24.99,  7.00),
        ("Foam Roller Deep Tissue",      29.99,  9.00),
        ("Jump Rope Speed",              14.99,  4.00),
        ("Dumbbell Set Adjustable",     199.99, 65.00),
        ("Running Water Bottle",         24.99,  7.00),
        ("Cycling Gloves",               19.99,  6.00),
        ("Hiking Backpack 40L",          79.99, 25.00),
        ("Fitness Tracker Band",         49.99, 16.00),
        ("Pull Up Bar Doorway",          34.99, 11.00),
    ],
    "Books": [
        ("The Art of Clean Code",        34.99,  8.00),
        ("System Design Interview",      44.99, 10.00),
        ("Deep Work",                    19.99,  5.00),
        ("Atomic Habits",                17.99,  4.50),
        ("The Pragmatic Programmer",     49.99, 12.00),
        ("Designing Data Intensive Apps",54.99, 14.00),
        ("Clean Architecture",           44.99, 11.00),
        ("The Psychology of Money",      16.99,  4.00),
        ("Zero to One",                  18.99,  4.75),
        ("Thinking Fast and Slow",       17.99,  4.50),
    ],
}

# Fill remaining categories with generic products
GENERIC_PRODUCTS = [
    ("Premium Product A", 49.99, 15.00),
    ("Deluxe Product B",  79.99, 25.00),
    ("Essential Product C", 29.99, 9.00),
    ("Professional Product D", 99.99, 32.00),
    ("Starter Product E", 19.99, 6.00),
    ("Advanced Product F", 149.99, 48.00),
    ("Basic Product G",   14.99, 4.50),
    ("Elite Product H",  199.99, 65.00),
    ("Classic Product I", 39.99, 12.00),
    ("Value Product J",   24.99, 7.50),
]

COUNTRIES = [
    "Kenya", "Nigeria", "South Africa", "Ghana", "Egypt",
    "United States", "United Kingdom", "Canada", "Australia", "Germany",
    "France", "India", "Brazil", "Mexico", "UAE",
    "Singapore", "Japan", "Netherlands", "Sweden", "Italy",
]

COUNTRY_CITIES = {
    "Kenya":         ["Nairobi", "Mombasa", "Kisumu", "Nakuru"],
    "Nigeria":       ["Lagos", "Abuja", "Kano", "Ibadan"],
    "South Africa":  ["Johannesburg", "Cape Town", "Durban", "Pretoria"],
    "Ghana":         ["Accra", "Kumasi", "Tamale"],
    "Egypt":         ["Cairo", "Alexandria", "Giza"],
    "United States": ["New York", "Los Angeles", "Chicago", "Houston"],
    "United Kingdom":["London", "Manchester", "Birmingham", "Leeds"],
    "Canada":        ["Toronto", "Vancouver", "Montreal", "Calgary"],
    "Australia":     ["Sydney", "Melbourne", "Brisbane", "Perth"],
    "Germany":       ["Berlin", "Munich", "Hamburg", "Frankfurt"],
    "France":        ["Paris", "Lyon", "Marseille", "Toulouse"],
    "India":         ["Mumbai", "Delhi", "Bangalore", "Hyderabad"],
    "Brazil":        ["São Paulo", "Rio de Janeiro", "Brasília"],
    "Mexico":        ["Mexico City", "Guadalajara", "Monterrey"],
    "UAE":           ["Dubai", "Abu Dhabi", "Sharjah"],
    "Singapore":     ["Singapore"],
    "Japan":         ["Tokyo", "Osaka", "Kyoto", "Yokohama"],
    "Netherlands":   ["Amsterdam", "Rotterdam", "The Hague"],
    "Sweden":        ["Stockholm", "Gothenburg", "Malmö"],
    "Italy":         ["Rome", "Milan", "Naples", "Turin"],
}

TIERS = ["bronze", "silver", "gold", "platinum"]
TIER_WEIGHTS = [0.50, 0.30, 0.15, 0.05]   # 50% bronze, 30% silver etc

ORDER_STATUSES = ["pending", "confirmed", "processing", "shipped", "delivered", "cancelled", "refunded"]
STATUS_WEIGHTS = [0.05, 0.08, 0.10, 0.12, 0.55, 0.07, 0.03]  # most orders delivered


def random_date(start_days_ago: int, end_days_ago: int = 0) -> datetime:
    """Return a random UTC datetime between start_days_ago and end_days_ago."""
    start = datetime.now(timezone.utc) - timedelta(days=start_days_ago)
    end = datetime.now(timezone.utc) - timedelta(days=end_days_ago)
    delta = end - start
    return start + timedelta(seconds=random.randint(0, int(delta.total_seconds())))


# ─────────────────────────────────────────────────────────────
# Seeding functions
# Each function returns the inserted IDs so the next
# function can reference them as foreign keys
# ─────────────────────────────────────────────────────────────

async def seed_categories(conn) -> dict[str, str]:
    """Insert categories, return {name: id} map."""
    print("  Seeding categories...")
    category_map = {}

    for name, description in CATEGORIES:
        row = await conn.fetchrow(
            """
            INSERT INTO categories (name, description)
            VALUES ($1, $2)
            ON CONFLICT (name) DO UPDATE SET description = EXCLUDED.description
            RETURNING id, name
            """,
            name, description
        )
        category_map[row["name"]] = str(row["id"])

    print(f"    ✓ {len(category_map)} categories")
    return category_map


async def seed_products(conn, category_map: dict[str, str]) -> list[str]:
    """Insert products, return list of product IDs."""
    print("  Seeding products...")
    product_ids = []

    for category_name, cat_id in category_map.items():
        # Use template products if available, otherwise generic
        templates = PRODUCTS_TEMPLATE.get(category_name, [])

        if templates:
            for product_name, base_price, base_cost in templates:
                # Add slight price variation so data is not perfectly uniform
                price = round(base_price * random.uniform(0.9, 1.1), 2)
                cost = round(base_cost * random.uniform(0.9, 1.1), 2)
                sku = f"{category_name[:3].upper()}-{fake.bothify('???-####').upper()}"

                row = await conn.fetchrow(
                    """
                    INSERT INTO products (name, sku, category_id, description, price, cost, stock_qty)
                    VALUES ($1, $2, $3, $4, $5, $6, $7)
                    ON CONFLICT (sku) DO NOTHING
                    RETURNING id
                    """,
                    product_name,
                    sku,
                    cat_id,
                    fake.sentence(nb_words=12),
                    price,
                    cost,
                    random.randint(0, 500),
                )
                if row:
                    product_ids.append(str(row["id"]))
        else:
            for product_name, base_price, base_cost in GENERIC_PRODUCTS:
                full_name = f"{category_name} — {product_name}"
                price = round(base_price * random.uniform(0.85, 1.15), 2)
                cost = round(base_cost * random.uniform(0.85, 1.15), 2)
                sku = f"{category_name[:3].upper()}-{fake.bothify('???-####').upper()}"

                row = await conn.fetchrow(
                    """
                    INSERT INTO products (name, sku, category_id, description, price, cost, stock_qty)
                    VALUES ($1, $2, $3, $4, $5, $6, $7)
                    ON CONFLICT (sku) DO NOTHING
                    RETURNING id
                    """,
                    full_name,
                    sku,
                    cat_id,
                    fake.sentence(nb_words=12),
                    price,
                    cost,
                    random.randint(0, 500),
                )
                if row:
                    product_ids.append(str(row["id"]))

    print(f"    ✓ {len(product_ids)} products")
    return product_ids


async def seed_customers(conn, count: int = 1000) -> list[str]:
    """Insert customers, return list of customer IDs."""
    print(f"  Seeding {count} customers...")
    customer_ids = []

    for _ in range(count):
        country = random.choice(COUNTRIES)
        city = random.choice(COUNTRY_CITIES[country])
        tier = random.choices(TIERS, weights=TIER_WEIGHTS, k=1)[0]
        created_at = random_date(start_days_ago=730)   # up to 2 years ago

        row = await conn.fetchrow(
            """
            INSERT INTO customers (name, email, phone, country, city, tier, created_at, updated_at)
            VALUES ($1, $2, $3, $4, $5, $6, $7, $7)
            ON CONFLICT (email) DO NOTHING
            RETURNING id
            """,
            fake.name(),
            fake.unique.email(),
            fake.phone_number()[:50],
            country,
            city,
            tier,
            created_at,
        )
        if row:
            customer_ids.append(str(row["id"]))

    print(f"    ✓ {len(customer_ids)} customers")
    return customer_ids


async def seed_orders(
    conn,
    customer_ids: list[str],
    product_ids: list[str],
    order_count: int = 10000,
) -> None:
    """Insert orders and order items."""
    print(f"  Seeding {order_count} orders with items...")

    # Fetch product prices/costs once so we don't query per order
    products = await conn.fetch(
        "SELECT id, price, cost FROM products"
    )
    product_data = {
        str(p["id"]): {"price": float(p["price"]), "cost": float(p["cost"])}
        for p in products
    }
    product_id_list = list(product_data.keys())

    orders_inserted = 0
    items_inserted = 0

    # Process in batches for performance
    BATCH_SIZE = 500

    for batch_start in range(0, order_count, BATCH_SIZE):
        batch_end = min(batch_start + BATCH_SIZE, order_count)
        batch_size = batch_end - batch_start

        async with conn.transaction():
            for _ in range(batch_size):
                customer_id = random.choice(customer_ids)
                status = random.choices(ORDER_STATUSES, weights=STATUS_WEIGHTS, k=1)[0]
                ordered_at = random_date(start_days_ago=730)

                # Insert order with placeholder total
                order_row = await conn.fetchrow(
                    """
                    INSERT INTO orders
                        (customer_id, status, total_amount, shipping_country, shipping_city, ordered_at, updated_at)
                    VALUES ($1, $2, 0, $3, $4, $5, $5)
                    RETURNING id
                    """,
                    customer_id,
                    status,
                    fake.country(),
                    fake.city(),
                    ordered_at,
                )
                order_id = str(order_row["id"])

                # Each order has 1-6 items
                num_items = random.randint(1, 6)
                selected_products = random.sample(product_id_list, min(num_items, len(product_id_list)))

                order_total = Decimal("0")

                for product_id in selected_products:
                    qty = random.randint(1, 5)
                    unit_price = Decimal(str(round(
                        product_data[product_id]["price"] * random.uniform(0.95, 1.05), 2
                    )))
                    unit_cost = Decimal(str(round(
                        product_data[product_id]["cost"] * random.uniform(0.95, 1.05), 2
                    )))

                    await conn.execute(
                        """
                        INSERT INTO order_items (order_id, product_id, quantity, unit_price, unit_cost)
                        VALUES ($1, $2, $3, $4, $5)
                        """,
                        order_id, product_id, qty, unit_price, unit_cost,
                    )

                    order_total += unit_price * qty
                    items_inserted += 1

                # Update order with real total
                await conn.execute(
                    "UPDATE orders SET total_amount = $1 WHERE id = $2",
                    order_total, order_id,
                )
                orders_inserted += 1

        print(f"    {batch_end}/{order_count} orders...", end="\r")

    print(f"    ✓ {orders_inserted} orders, {items_inserted} order items          ")


# ─────────────────────────────────────────────────────────────
# Main
# ─────────────────────────────────────────────────────────────

async def main():
    print("\n🌱 Starting seed...\n")

    # Use admin connection for seeding (not readonly)
    # Strip +asyncpg from URL for asyncpg direct connection
    db_url = settings.postgres_url.replace("postgresql+asyncpg://", "postgresql://")

    conn = await asyncpg.connect(db_url)

    try:
        category_map = await seed_categories(conn)
        product_ids  = await seed_products(conn, category_map)
        customer_ids = await seed_customers(conn, count=1000)
        await seed_orders(conn, customer_ids, product_ids, order_count=10000)

        # ── Summary ──────────────────────────────────────────
        counts = await conn.fetch("""
            SELECT 'categories'  AS tbl, COUNT(*) FROM categories  UNION ALL
            SELECT 'products'    AS tbl, COUNT(*) FROM products     UNION ALL
            SELECT 'customers'   AS tbl, COUNT(*) FROM customers    UNION ALL
            SELECT 'orders'      AS tbl, COUNT(*) FROM orders       UNION ALL
            SELECT 'order_items' AS tbl, COUNT(*) FROM order_items
        """)

        print("\n✅ Seed complete!\n")
        print("  Table              Rows")
        print("  " + "─" * 30)
        for row in counts:
            print(f"  {row['tbl']:<18} {row['count']:>6,}")
        print()

    finally:
        await conn.close()


if __name__ == "__main__":
    asyncio.run(main())