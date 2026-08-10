import psycopg2

from .config import ADMIN_EMAILS, DATABASE_URL


def get_db_connection():
    return psycopg2.connect(DATABASE_URL)


def init_db():
    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    id SERIAL PRIMARY KEY,
                    email TEXT UNIQUE NOT NULL,
                    password_hash TEXT NOT NULL,
                    role TEXT NOT NULL DEFAULT 'customer',
                    full_name TEXT,
                    phone TEXT,
                    address TEXT,
                    session_version INTEGER NOT NULL DEFAULT 1,
                    created_at TIMESTAMPTZ DEFAULT now()
                )
            """)
            cur.execute("ALTER TABLE users ADD COLUMN IF NOT EXISTS role TEXT NOT NULL DEFAULT 'customer'")
            cur.execute("ALTER TABLE users ADD COLUMN IF NOT EXISTS full_name TEXT")
            cur.execute("ALTER TABLE users ADD COLUMN IF NOT EXISTS phone TEXT")
            cur.execute("ALTER TABLE users ADD COLUMN IF NOT EXISTS address TEXT")
            cur.execute("ALTER TABLE users ADD COLUMN IF NOT EXISTS session_version INTEGER NOT NULL DEFAULT 1")
            cur.execute("""
                CREATE TABLE IF NOT EXISTS orders (
                    id SERIAL PRIMARY KEY,
                    user_id INTEGER NOT NULL REFERENCES users(id),
                    items JSONB NOT NULL,
                    total_aud NUMERIC(12, 2) NOT NULL,
                    status TEXT NOT NULL DEFAULT 'pending',
                    assigned_to INTEGER REFERENCES users(id),
                    created_at TIMESTAMPTZ DEFAULT now()
                )
            """)
            cur.execute("ALTER TABLE orders ADD COLUMN IF NOT EXISTS status TEXT NOT NULL DEFAULT 'pending'")
            cur.execute("ALTER TABLE orders ADD COLUMN IF NOT EXISTS assigned_to INTEGER REFERENCES users(id)")
            cur.execute("""
                CREATE TABLE IF NOT EXISTS reservations (
                    id SERIAL PRIMARY KEY,
                    user_id INTEGER NOT NULL REFERENCES users(id),
                    items JSONB NOT NULL,
                    total_aud NUMERIC(12, 2) NOT NULL,
                    pickup_date DATE NOT NULL,
                    status TEXT NOT NULL DEFAULT 'pending',
                    assigned_to INTEGER REFERENCES users(id),
                    notes TEXT,
                    created_at TIMESTAMPTZ DEFAULT now()
                )
            """)
            cur.execute("ALTER TABLE reservations ADD COLUMN IF NOT EXISTS assigned_to INTEGER REFERENCES users(id)")
            cur.execute("ALTER TABLE reservations ADD COLUMN IF NOT EXISTS notes TEXT")
            cur.execute("""
                CREATE TABLE IF NOT EXISTS password_resets (
                    id SERIAL PRIMARY KEY,
                    user_id INTEGER NOT NULL REFERENCES users(id),
                    token TEXT UNIQUE NOT NULL,
                    expires_at TIMESTAMPTZ NOT NULL,
                    used BOOLEAN NOT NULL DEFAULT FALSE,
                    created_at TIMESTAMPTZ DEFAULT now()
                )
            """)
            cur.execute("""
                CREATE TABLE IF NOT EXISTS aud_news (
                    id SERIAL PRIMARY KEY,
                    title TEXT NOT NULL,
                    summary TEXT,
                    source TEXT NOT NULL,
                    url TEXT UNIQUE NOT NULL,
                    published_at TIMESTAMPTZ,
                    fetched_at TIMESTAMPTZ DEFAULT now()
                )
            """)
            cur.execute("""
                CREATE TABLE IF NOT EXISTS admin_activity_log (
                    id SERIAL PRIMARY KEY,
                    entity_type TEXT NOT NULL,
                    entity_id INTEGER NOT NULL,
                    actor_user_id INTEGER REFERENCES users(id),
                    action TEXT NOT NULL,
                    detail TEXT,
                    created_at TIMESTAMPTZ DEFAULT now()
                )
            """)

            # Bootstrap: anyone listed in ADMIN_EMAILS starts out as 'admin'.
            # Only touches accounts still at the 'customer' default, so a
            # manual role change made later through the admin UI sticks.
            if ADMIN_EMAILS:
                cur.execute(
                    "UPDATE users SET role = 'admin' WHERE role = 'customer' AND email = ANY(%s)",
                    (list(ADMIN_EMAILS),)
                )
        conn.commit()
    finally:
        conn.close()
