-- TravelVista database schema (SQLite dialect)
-- Note: In normal operation, Flask-SQLAlchemy/Flask-Migrate create and
-- version these tables automatically from models.py. This file is
-- provided for manual inspection, documentation, or manual DB setup.

PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username VARCHAR(64) UNIQUE NOT NULL,
    email VARCHAR(120) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    full_name VARCHAR(120),
    phone VARCHAR(30),
    address VARCHAR(255),
    country VARCHAR(80),
    passport_number VARCHAR(50),
    emergency_contact VARCHAR(120),
    profile_image VARCHAR(255) DEFAULT 'default_profile.png',
    is_active_account BOOLEAN DEFAULT 1,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    reset_token VARCHAR(255),
    reset_token_expiry DATETIME
);

CREATE TABLE IF NOT EXISTS admins (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username VARCHAR(64) UNIQUE NOT NULL,
    email VARCHAR(120) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    role VARCHAR(30) DEFAULT 'admin',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS destinations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name VARCHAR(120) NOT NULL,
    city VARCHAR(80),
    country VARCHAR(80) NOT NULL,
    description TEXT,
    overview TEXT,
    travel_type VARCHAR(30),
    price_per_person FLOAT DEFAULT 0,
    duration_days INTEGER DEFAULT 1,
    rating FLOAT DEFAULT 0,
    review_count INTEGER DEFAULT 0,
    best_time_to_visit VARCHAR(120),
    safety_tips TEXT,
    things_to_do TEXT,
    hotels TEXT,
    restaurants TEXT,
    transportation TEXT,
    map_lat FLOAT,
    map_lng FLOAT,
    cover_image VARCHAR(255) DEFAULT 'default_destination.jpg',
    is_featured BOOLEAN DEFAULT 0,
    is_popular BOOLEAN DEFAULT 0,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS images (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    destination_id INTEGER NOT NULL REFERENCES destinations(id) ON DELETE CASCADE,
    filename VARCHAR(255) NOT NULL,
    original_name VARCHAR(255),
    is_cover BOOLEAN DEFAULT 0,
    uploaded_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS bookings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    booking_reference VARCHAR(20) UNIQUE NOT NULL,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    destination_id INTEGER NOT NULL REFERENCES destinations(id),
    hotel_name VARCHAR(120),
    travel_date DATE NOT NULL,
    return_date DATE,
    passengers INTEGER DEFAULT 1,
    price_per_person FLOAT DEFAULT 0,
    total_amount FLOAT DEFAULT 0,
    status VARCHAR(20) DEFAULT 'confirmed',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS payments (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    booking_id INTEGER NOT NULL REFERENCES bookings(id) ON DELETE CASCADE,
    amount FLOAT NOT NULL,
    payment_method VARCHAR(30) DEFAULT 'card',
    payment_status VARCHAR(20) DEFAULT 'paid',
    transaction_id VARCHAR(60) UNIQUE,
    paid_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS wishlist (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    destination_id INTEGER NOT NULL REFERENCES destinations(id) ON DELETE CASCADE,
    added_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(user_id, destination_id)
);

CREATE TABLE IF NOT EXISTS messages (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER REFERENCES users(id) ON DELETE SET NULL,
    name VARCHAR(120) NOT NULL,
    email VARCHAR(120) NOT NULL,
    subject VARCHAR(200),
    body TEXT NOT NULL,
    is_read BOOLEAN DEFAULT 0,
    admin_reply TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS reviews (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    destination_id INTEGER NOT NULL REFERENCES destinations(id) ON DELETE CASCADE,
    rating INTEGER NOT NULL,
    comment TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(user_id, destination_id)
);

CREATE TABLE IF NOT EXISTS trips (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    destination_name VARCHAR(120) NOT NULL,
    budget FLOAT,
    days INTEGER,
    travel_style VARCHAR(30),
    travelers INTEGER DEFAULT 1,
    interests VARCHAR(255),
    itinerary_json TEXT,
    packing_list_json TEXT,
    tips_json TEXT,
    estimated_budget_json TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS notifications (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    title VARCHAR(150) NOT NULL,
    body VARCHAR(500),
    category VARCHAR(30) DEFAULT 'general',
    is_read BOOLEAN DEFAULT 0,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS audit_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    admin_id INTEGER REFERENCES admins(id) ON DELETE SET NULL,
    action VARCHAR(200) NOT NULL,
    target_type VARCHAR(50),
    target_id INTEGER,
    details TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_destinations_country ON destinations(country);
CREATE INDEX IF NOT EXISTS idx_destinations_travel_type ON destinations(travel_type);
CREATE INDEX IF NOT EXISTS idx_bookings_user ON bookings(user_id);
CREATE INDEX IF NOT EXISTS idx_bookings_destination ON bookings(destination_id);
CREATE INDEX IF NOT EXISTS idx_reviews_destination ON reviews(destination_id);
