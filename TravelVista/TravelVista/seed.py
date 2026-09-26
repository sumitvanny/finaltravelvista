"""
seed.py
Populates the database with a default admin account and a set of sample
destinations so the app is immediately explorable after setup.

Run with:  python seed.py
"""

from app import create_app
from extensions import db
from models import Admin, Destination, Image

app = create_app()

SAMPLE_DESTINATIONS = [
    dict(
        name="Santorini Sunset Escape", city="Oia", country="Greece", travel_type="couple",
        description="Whitewashed cliffside villages overlooking the deep blue Aegean Sea.",
        overview="Santorini is famed for its dramatic caldera views, blue-domed churches, and some of "
                 "the most spectacular sunsets on Earth. Perfect for couples seeking romance and beauty.",
        price_per_person=1450, duration_days=5, rating=4.8, review_count=0,
        best_time_to_visit="April to June, September to October",
        safety_tips="Wear sturdy shoes on cobblestone paths; sun protection is essential in summer.",
        things_to_do="Watch the sunset in Oia\nVisit Akrotiri archaeological site\nWine tasting tour\nCatamaran cruise around the caldera",
        hotels="Grace Hotel Santorini\nCanaves Oia Epitome\nKatikies Hotel",
        restaurants="Ambrosia Restaurant\nMetaxy Mas\nSelene",
        transportation="Local buses, rental ATVs, taxis, and organized tours",
        map_lat=36.3932, map_lng=25.4615, is_featured=True, is_popular=True,
    ),
    dict(
        name="Kyoto Cultural Journey", city="Kyoto", country="Japan", travel_type="family",
        description="Ancient temples, serene gardens, and traditional geisha districts.",
        overview="Kyoto, Japan's former imperial capital, is home to thousands of temples, shrines, and "
                 "traditional wooden houses. A perfect blend of history and natural beauty for all ages.",
        price_per_person=1800, duration_days=7, rating=4.9, review_count=0,
        best_time_to_visit="March-April (cherry blossoms), October-November (autumn colors)",
        safety_tips="Japan is very safe; carry cash as some smaller shops don't accept cards.",
        things_to_do="Visit Fushimi Inari Shrine\nExplore Arashiyama Bamboo Grove\nGion district walk\nKinkaku-ji Golden Pavilion",
        hotels="The Ritz-Carlton Kyoto\nHyatt Regency Kyoto\nGion Hatanaka",
        restaurants="Kikunoi\nOmen Kodaiji\nNishiki Market food stalls",
        transportation="JR trains, city buses, bicycle rentals",
        map_lat=35.0116, map_lng=135.7681, is_featured=True, is_popular=True,
    ),
    dict(
        name="Serengeti Safari Adventure", city="Serengeti", country="Tanzania", travel_type="adventure",
        description="Witness the Great Migration across endless golden plains.",
        overview="The Serengeti National Park offers unparalleled wildlife viewing, including the "
                 "legendary wildebeest migration, lions, elephants, and more across vast savannahs.",
        price_per_person=3200, duration_days=6, rating=4.9, review_count=0,
        best_time_to_visit="June to September, and January to February",
        safety_tips="Always stay inside vehicles during game drives; follow your guide's instructions.",
        things_to_do="Game drives\nHot air balloon safari\nVisit a Maasai village\nGreat Migration river crossing viewing",
        hotels="Four Seasons Safari Lodge\nSingita Serengeti House\nSerengeti Serena Safari Lodge",
        restaurants="Lodge dining (most stays are full-board)\nBush breakfast experiences",
        transportation="4x4 safari vehicles, chartered light aircraft",
        map_lat=-2.3333, map_lng=34.8333, is_featured=True, is_popular=True,
    ),
    dict(
        name="Bali Beach Retreat", city="Ubud", country="Indonesia", travel_type="beach",
        description="Tropical beaches, lush rice terraces, and a thriving wellness scene.",
        overview="Bali offers something for everyone: surf breaks, rice paddies, yoga retreats, "
                 "vibrant nightlife, and warm hospitality across its many distinct regions.",
        price_per_person=950, duration_days=6, rating=4.6, review_count=0,
        best_time_to_visit="April to October (dry season)",
        safety_tips="Respect temple dress codes; be cautious of strong currents at surf beaches.",
        things_to_do="Tegallalang Rice Terraces\nUluwatu Temple sunset\nSurfing at Canggu\nBalinese cooking class",
        hotels="Four Seasons Resort Bali at Sayan\nCOMO Uma Ubud\nThe Mulia",
        restaurants="Locavore\nMozaic\nWarung Babi Guling Ibu Oka",
        transportation="Private drivers, scooters, ride-hailing apps",
        map_lat=-8.5069, map_lng=115.2625, is_featured=False, is_popular=True,
    ),
    dict(
        name="Swiss Alps Adventure", city="Zermatt", country="Switzerland", travel_type="nature",
        description="Snow-capped peaks, alpine lakes, and world-class hiking trails.",
        overview="Zermatt sits in the shadow of the iconic Matterhorn, offering breathtaking hiking, "
                 "skiing, and mountain railways with some of the most scenic views in Europe.",
        price_per_person=2600, duration_days=5, rating=4.7, review_count=0,
        best_time_to_visit="July-September (hiking), December-March (skiing)",
        safety_tips="Check weather and trail conditions daily; carry layers for sudden temperature drops.",
        things_to_do="Gornergrat railway\nMatterhorn Glacier Paradise\nAlpine hiking trails\nSkiing and snowboarding",
        hotels="The Omnia\nMont Cervin Palace\nRiffelalp Resort",
        restaurants="Whymper-Stube\nChez Vrony\nFindlerhof",
        transportation="Cogwheel trains, cable cars, electric taxis (car-free village)",
        map_lat=46.0207, map_lng=7.7491, is_featured=False, is_popular=True,
    ),
    dict(
        name="New York City Business Trip", city="New York", country="United States", travel_type="business",
        description="The city that never sleeps — iconic skyline, world finance, and culture.",
        overview="New York City combines a global business hub with world-class museums, Broadway "
                 "shows, and dining, making it ideal for business travelers extending their stay.",
        price_per_person=1600, duration_days=4, rating=4.5, review_count=0,
        best_time_to_visit="April-June, September-November",
        safety_tips="Use official yellow cabs or ride-hailing apps late at night; stay aware in crowded areas.",
        things_to_do="Wall Street tour\nBroadway show\nCentral Park walk\nMuseum of Modern Art",
        hotels="The Peninsula New York\nThe Langham\nAce Hotel New York",
        restaurants="Eleven Madison Park\nKatz's Delicatessen\nLe Bernardin",
        transportation="Subway, yellow cabs, ride-hailing apps",
        map_lat=40.7128, map_lng=-74.0060, is_featured=False, is_popular=True,
    ),
    dict(
        name="Patagonia Solo Trek", city="El Chaltén", country="Argentina", travel_type="solo",
        description="Rugged trails beneath towering granite peaks, ideal for solo explorers.",
        overview="Patagonia's dramatic landscapes, from Fitz Roy to glacial lakes, attract solo hikers "
                 "seeking solitude, self-discovery, and unforgettable trekking routes.",
        price_per_person=2100, duration_days=8, rating=4.8, review_count=0,
        best_time_to_visit="November to March (Southern Hemisphere summer)",
        safety_tips="Register your hiking route with local rangers; weather can change rapidly.",
        things_to_do="Laguna de los Tres trek\nPerito Moreno Glacier visit\nFitz Roy viewpoint hike\nStargazing",
        hotels="Los Cerros El Chaltén\nAguas Arriba Lodge\nHostería El Puma",
        restaurants="La Tapera\nPatagonicus\nLa Vinería",
        transportation="Local shuttles, rental cars, trekking on foot",
        map_lat=-49.3325, map_lng=-72.8869, is_featured=False, is_popular=False,
    ),
    dict(
        name="Maldives Luxury Overwater Villas", city="Malé", country="Maldives", travel_type="luxury",
        description="Crystal-clear lagoons and private overwater villas for the ultimate indulgence.",
        overview="The Maldives is the definition of paradise — powder-white sand, turquoise waters, "
                 "and some of the world's most luxurious overwater resorts.",
        price_per_person=4200, duration_days=5, rating=5.0, review_count=0,
        best_time_to_visit="November to April (dry season)",
        safety_tips="Use reef-safe sunscreen; check with your resort about currents before swimming.",
        things_to_do="Snorkeling with manta rays\nSunset dolphin cruise\nPrivate sandbank picnic\nSpa treatments over the lagoon",
        hotels="Soneva Fushi\nOne&Only Reethi Rah\nGili Lankanfushi",
        restaurants="Overwater fine dining at resort\nUnderwater restaurant experiences",
        transportation="Seaplane or speedboat transfers from Malé",
        map_lat=4.1755, map_lng=73.5093, is_featured=True, is_popular=False,
    ),
]


def seed_admin():
    if not Admin.query.filter_by(username="admin").first():
        admin = Admin(username="admin", email="admin@travelvista.com", role="superadmin")
        admin.set_password("Admin@12345")
        db.session.add(admin)
        db.session.commit()
        print("Created default admin -> username: admin | password: Admin@12345")
    else:
        print("Admin already exists, skipping.")


def seed_destinations():
    if Destination.query.count() > 0:
        print("Destinations already seeded, skipping.")
        return
    for data in SAMPLE_DESTINATIONS:
        dest = Destination(**data)
        db.session.add(dest)
    db.session.commit()
    print(f"Seeded {len(SAMPLE_DESTINATIONS)} sample destinations.")


if __name__ == "__main__":
    with app.app_context():
        db.create_all()
        seed_admin()
        seed_destinations()
        print("Database seeding complete.")
