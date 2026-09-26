-- Sample data for TravelVista (SQLite dialect)
-- NOTE: The recommended way to seed the database is `python seed.py`,
-- which uses Werkzeug's password hashing correctly. This file is a
-- reference/manual-setup companion to schema.sql showing the shape of
-- the data; the password hash below corresponds to "Admin@12345" and
-- was generated with werkzeug.security.generate_password_hash.

INSERT INTO admins (username, email, password_hash, role)
VALUES (
    'admin',
    'admin@travelvista.com',
    'pbkdf2:sha256:600000$placeholderSaltValue$0000000000000000000000000000000000000000000000000000000000000000',
    'superadmin'
);
-- IMPORTANT: the password_hash placeholder above is NOT a valid hash.
-- Always create the admin account via `python seed.py` so the hash is
-- generated correctly, then update this file from your own DB if you
-- want a real static export for version control.

INSERT INTO destinations (
    name, city, country, description, overview, travel_type,
    price_per_person, duration_days, rating, review_count,
    best_time_to_visit, safety_tips, things_to_do, hotels, restaurants,
    transportation, map_lat, map_lng, cover_image, is_featured, is_popular
) VALUES (
    'Santorini Sunset Escape', 'Oia', 'Greece',
    'Whitewashed cliffside villages overlooking the deep blue Aegean Sea.',
    'Santorini is famed for its dramatic caldera views, blue-domed churches, and unforgettable sunsets.',
    'couple', 1450, 5, 4.8, 0,
    'April to June, September to October',
    'Wear sturdy shoes on cobblestone paths; sun protection is essential in summer.',
    'Watch the sunset in Oia
Visit Akrotiri archaeological site
Wine tasting tour
Catamaran cruise around the caldera',
    'Grace Hotel Santorini
Canaves Oia Epitome
Katikies Hotel',
    'Ambrosia Restaurant
Metaxy Mas
Selene',
    'Local buses, rental ATVs, taxis, and organized tours',
    36.3932, 25.4615, 'default_destination.jpg', 1, 1
);

INSERT INTO destinations (
    name, city, country, description, overview, travel_type,
    price_per_person, duration_days, rating, review_count,
    best_time_to_visit, safety_tips, things_to_do, hotels, restaurants,
    transportation, map_lat, map_lng, cover_image, is_featured, is_popular
) VALUES (
    'Kyoto Cultural Journey', 'Kyoto', 'Japan',
    'Ancient temples, serene gardens, and traditional geisha districts.',
    'Kyoto, Japan''s former imperial capital, blends centuries of history with natural beauty.',
    'family', 1800, 7, 4.9, 0,
    'March-April (cherry blossoms), October-November (autumn colors)',
    'Japan is very safe; carry cash as some smaller shops don''t accept cards.',
    'Visit Fushimi Inari Shrine
Explore Arashiyama Bamboo Grove
Gion district walk
Kinkaku-ji Golden Pavilion',
    'The Ritz-Carlton Kyoto
Hyatt Regency Kyoto
Gion Hatanaka',
    'Kikunoi
Omen Kodaiji
Nishiki Market food stalls',
    'JR trains, city buses, bicycle rentals',
    35.0116, 135.7681, 'default_destination.jpg', 1, 1
);

-- For the full sample destination set (8 destinations), run `python seed.py`,
-- which populates identical data programmatically and is kept as the
-- single source of truth for demo content.
