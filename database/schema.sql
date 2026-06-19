-- ─────────────────────────────────────────────────────────────
-- schema.sql
-- Runs automatically on first postgres container start
-- via docker-entrypoint-initdb.d/
--
-- Order matters:
-- 1. Extensions
-- 2. Tables (dependencies first)
-- 3. Indexes
-- 4. Read-only role
-- 5. Views
-- ─────────────────────────────────────────────────────────────


-- ─────────────────────────────────────────────────────────────
-- 1. EXTENSIONS
-- ─────────────────────────────────────────────────────────────

-- uuid_generate_v4() for primary keys
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- pg_trgm for fuzzy text search (e.g. find customers by name)
CREATE EXTENSION IF NOT EXISTS pg_trgm;


-- ─────────────────────────────────────────────────────────────
-- 2. TABLES
-- Dependencies first:
-- customers, products → orders → order_items
-- ─────────────────────────────────────────────────────────────

CREATE TABLE IF NOT EXISTS customers (
    id                  UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name                VARCHAR(255) NOT NULL,
    email               VARCHAR(255) NOT NULL UNIQUE,
    phone               VARCHAR(50),
    country             VARCHAR(100) NOT NULL,
    city                VARCHAR(100),
    tier                VARCHAR(20) NOT NULL DEFAULT 'bronze'
                            CHECK (tier IN ('bronze', 'silver', 'gold', 'platinum')),
    is_active           BOOLEAN NOT NULL DEFAULT TRUE,
    created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at          TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

COMMENT ON TABLE customers IS 'End customers who place orders';
COMMENT ON COLUMN customers.tier IS 'Loyalty tier: bronze < silver < gold < platinum';
COMMENT ON COLUMN customers.created_at IS 'Timestamp with timezone — always stored in UTC';


CREATE TABLE IF NOT EXISTS categories (
    id                  UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name                VARCHAR(100) NOT NULL UNIQUE,
    description         TEXT,
    created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

COMMENT ON TABLE categories IS 'Product categories';


CREATE TABLE IF NOT EXISTS products (
    id                  UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name                VARCHAR(255) NOT NULL,
    sku                 VARCHAR(100) NOT NULL UNIQUE,
    category_id         UUID NOT NULL REFERENCES categories(id),
    description         TEXT,
    price               NUMERIC(10, 2) NOT NULL CHECK (price >= 0),
    cost                NUMERIC(10, 2) NOT NULL CHECK (cost >= 0),
    stock_qty           INTEGER NOT NULL DEFAULT 0 CHECK (stock_qty >= 0),
    is_active           BOOLEAN NOT NULL DEFAULT TRUE,
    created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at          TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

COMMENT ON TABLE products IS 'Product catalogue';
COMMENT ON COLUMN products.sku IS 'Stock Keeping Unit — unique product identifier';
COMMENT ON COLUMN products.cost IS 'Cost price — used for margin/profit calculations';
COMMENT ON COLUMN products.price IS 'Selling price';


CREATE TABLE IF NOT EXISTS orders (
    id                  UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    customer_id         UUID NOT NULL REFERENCES customers(id),
    status              VARCHAR(30) NOT NULL DEFAULT 'pending'
                            CHECK (status IN (
                                'pending',
                                'confirmed',
                                'processing',
                                'shipped',
                                'delivered',
                                'cancelled',
                                'refunded'
                            )),
    total_amount        NUMERIC(12, 2) NOT NULL DEFAULT 0 CHECK (total_amount >= 0),
    shipping_country    VARCHAR(100),
    shipping_city       VARCHAR(100),
    notes               TEXT,
    ordered_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at          TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

COMMENT ON TABLE orders IS 'Customer orders';
COMMENT ON COLUMN orders.total_amount IS 'Computed from order_items — kept denormalised for query performance';
COMMENT ON COLUMN orders.status IS 'Order lifecycle: pending → confirmed → processing → shipped → delivered';


CREATE TABLE IF NOT EXISTS order_items (
    id                  UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    order_id            UUID NOT NULL REFERENCES orders(id) ON DELETE CASCADE,
    product_id          UUID NOT NULL REFERENCES products(id),
    quantity            INTEGER NOT NULL CHECK (quantity > 0),
    unit_price          NUMERIC(10, 2) NOT NULL CHECK (unit_price >= 0),
    -- snapshot of cost at time of order for margin calculations
    unit_cost           NUMERIC(10, 2) NOT NULL CHECK (unit_cost >= 0),
    created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

COMMENT ON TABLE order_items IS 'Individual line items within an order';
COMMENT ON COLUMN order_items.unit_price IS 'Price at time of order — not affected by future price changes';
COMMENT ON COLUMN order_items.unit_cost IS 'Cost at time of order — used for margin reporting';


-- ─────────────────────────────────────────────────────────────
-- 3. INDEXES
-- Rule: index every foreign key, every column you filter or
-- sort by, and every column used in date range queries
-- ─────────────────────────────────────────────────────────────

-- customers
CREATE INDEX IF NOT EXISTS idx_customers_email      ON customers(email);
CREATE INDEX IF NOT EXISTS idx_customers_country    ON customers(country);
CREATE INDEX IF NOT EXISTS idx_customers_tier       ON customers(tier);
CREATE INDEX IF NOT EXISTS idx_customers_created_at ON customers(created_at);
CREATE INDEX IF NOT EXISTS idx_customers_is_active  ON customers(is_active);
-- fuzzy search on customer name (uses pg_trgm extension)
CREATE INDEX IF NOT EXISTS idx_customers_name_trgm  ON customers USING GIN (name gin_trgm_ops);

-- products
CREATE INDEX IF NOT EXISTS idx_products_category_id ON products(category_id);
CREATE INDEX IF NOT EXISTS idx_products_sku         ON products(sku);
CREATE INDEX IF NOT EXISTS idx_products_is_active   ON products(is_active);
CREATE INDEX IF NOT EXISTS idx_products_price       ON products(price);

-- orders
CREATE INDEX IF NOT EXISTS idx_orders_customer_id   ON orders(customer_id);
CREATE INDEX IF NOT EXISTS idx_orders_status        ON orders(status);
CREATE INDEX IF NOT EXISTS idx_orders_ordered_at    ON orders(ordered_at);
-- composite index — common pattern: filter by status AND date range
CREATE INDEX IF NOT EXISTS idx_orders_status_date   ON orders(status, ordered_at);

-- order_items
CREATE INDEX IF NOT EXISTS idx_order_items_order_id   ON order_items(order_id);
CREATE INDEX IF NOT EXISTS idx_order_items_product_id ON order_items(product_id);


-- ─────────────────────────────────────────────────────────────
-- 4. READ-ONLY ROLE
-- Created by 02_create_readonly_user.sh (runs after this file)
-- so it can read POSTGRES_READONLY_USER / POSTGRES_READONLY_PASSWORD
-- from the container environment.
-- ─────────────────────────────────────────────────────────────


-- ─────────────────────────────────────────────────────────────
-- 5. VIEWS
-- Pre-built joins that the AI agent can query directly.
-- Reduces complexity of AI-generated SQL — instead of
-- writing a 4-table join, the AI queries a single view.
-- ─────────────────────────────────────────────────────────────

-- Full order detail — orders with customer and item breakdown
CREATE OR REPLACE VIEW v_order_details AS
SELECT
    o.id                                        AS order_id,
    o.status                                    AS order_status,
    o.ordered_at,
    o.total_amount                              AS order_total,

    -- customer
    c.id                                        AS customer_id,
    c.name                                      AS customer_name,
    c.email                                     AS customer_email,
    c.country                                   AS customer_country,
    c.tier                                      AS customer_tier,

    -- item
    oi.id                                       AS item_id,
    oi.quantity,
    oi.unit_price,
    oi.unit_cost,
    (oi.quantity * oi.unit_price)               AS item_revenue,
    (oi.quantity * (oi.unit_price - oi.unit_cost)) AS item_profit,

    -- product
    p.id                                        AS product_id,
    p.name                                      AS product_name,
    p.sku                                       AS product_sku,

    -- category
    cat.name                                    AS category_name

FROM orders o
JOIN customers c       ON c.id = o.customer_id
JOIN order_items oi    ON oi.order_id = o.id
JOIN products p        ON p.id = oi.product_id
JOIN categories cat    ON cat.id = p.category_id;

COMMENT ON VIEW v_order_details IS
'Flattened order view joining orders, customers, items, products, categories.
Use this for order-level analysis instead of writing manual joins.';


-- Monthly revenue summary
CREATE OR REPLACE VIEW v_monthly_revenue AS
SELECT
    DATE_TRUNC('month', o.ordered_at)          AS month,
    COUNT(DISTINCT o.id)                        AS total_orders,
    COUNT(DISTINCT o.customer_id)               AS unique_customers,
    SUM(oi.quantity * oi.unit_price)            AS revenue,
    SUM(oi.quantity * oi.unit_cost)             AS cost,
    SUM(oi.quantity * (oi.unit_price - oi.unit_cost)) AS profit,
    ROUND(
        SUM(oi.quantity * (oi.unit_price - oi.unit_cost)) /
        NULLIF(SUM(oi.quantity * oi.unit_price), 0) * 100,
        2
    )                                           AS profit_margin_pct
FROM orders o
JOIN order_items oi ON oi.order_id = o.id
WHERE o.status NOT IN ('cancelled', 'refunded')
GROUP BY DATE_TRUNC('month', o.ordered_at)
ORDER BY month DESC;

COMMENT ON VIEW v_monthly_revenue IS
'Monthly revenue, cost, profit and margin. Excludes cancelled and refunded orders.';


-- Product performance summary
CREATE OR REPLACE VIEW v_product_performance AS
SELECT
    p.id                                        AS product_id,
    p.name                                      AS product_name,
    p.sku,
    cat.name                                    AS category,
    p.price                                     AS current_price,
    COUNT(DISTINCT oi.order_id)                 AS total_orders,
    SUM(oi.quantity)                            AS units_sold,
    SUM(oi.quantity * oi.unit_price)            AS total_revenue,
    SUM(oi.quantity * (oi.unit_price - oi.unit_cost)) AS total_profit,
    ROUND(
        SUM(oi.quantity * (oi.unit_price - oi.unit_cost)) /
        NULLIF(SUM(oi.quantity * oi.unit_price), 0) * 100,
        2
    )                                           AS profit_margin_pct
FROM products p
JOIN categories cat    ON cat.id = p.category_id
LEFT JOIN order_items oi ON oi.product_id = p.id
LEFT JOIN orders o     ON o.id = oi.order_id
    AND o.status NOT IN ('cancelled', 'refunded')
GROUP BY p.id, p.name, p.sku, cat.name, p.price;

COMMENT ON VIEW v_product_performance IS
'Per-product sales, revenue, and profit summary. Excludes cancelled/refunded orders.';


-- Customer summary
CREATE OR REPLACE VIEW v_customer_summary AS
SELECT
    c.id                                        AS customer_id,
    c.name,
    c.email,
    c.country,
    c.tier,
    c.is_active,
    c.created_at,
    COUNT(DISTINCT o.id)                        AS total_orders,
    COALESCE(SUM(o.total_amount), 0)            AS lifetime_value,
    MAX(o.ordered_at)                           AS last_order_at,
    MIN(o.ordered_at)                           AS first_order_at
FROM customers c
LEFT JOIN orders o ON o.customer_id = c.id
    AND o.status NOT IN ('cancelled', 'refunded')
GROUP BY c.id, c.name, c.email, c.country, c.tier, c.is_active, c.created_at;

COMMENT ON VIEW v_customer_summary IS
'Customer profile with order history summary and lifetime value.';