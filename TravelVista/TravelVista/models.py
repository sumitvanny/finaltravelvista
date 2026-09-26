"""
models.py
All SQLAlchemy ORM models for TravelVista.

Tables: User, Admin, Destination, Booking, Wishlist, Message, Review,
Trip, Notification, Payment, Image, AuditLog
"""

from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin
from extensions import db


# --------------------------------------------------------------------------
# USER
# --------------------------------------------------------------------------
class User(UserMixin, db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False, index=True)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)

    full_name = db.Column(db.String(120))
    phone = db.Column(db.String(30))
    address = db.Column(db.String(255))
    country = db.Column(db.String(80))
    passport_number = db.Column(db.String(50))
    emergency_contact = db.Column(db.String(120))
    profile_image = db.Column(db.String(255), default="default_profile.png")

    is_active_account = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Password reset
    reset_token = db.Column(db.String(255))
    reset_token_expiry = db.Column(db.DateTime)

    # Relationships
    bookings = db.relationship("Booking", backref="user", lazy="dynamic", cascade="all, delete-orphan")
    wishlist_items = db.relationship("Wishlist", backref="user", lazy="dynamic", cascade="all, delete-orphan")
    reviews = db.relationship("Review", backref="user", lazy="dynamic", cascade="all, delete-orphan")
    trips = db.relationship("Trip", backref="user", lazy="dynamic", cascade="all, delete-orphan")
    notifications = db.relationship("Notification", backref="user", lazy="dynamic", cascade="all, delete-orphan")
    messages = db.relationship("Message", backref="user", lazy="dynamic")

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def profile_completion(self):
        fields = [self.full_name, self.phone, self.address, self.country,
                  self.emergency_contact, self.profile_image != "default_profile.png"]
        filled = sum(1 for f in fields if f)
        return int((filled / len(fields)) * 100)

    def unread_notification_count(self):
        return self.notifications.filter_by(is_read=False).count()

    def __repr__(self):
        return f"<User {self.username}>"


# --------------------------------------------------------------------------
# ADMIN
# --------------------------------------------------------------------------
class Admin(UserMixin, db.Model):
    __tablename__ = "admins"

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(30), default="admin")  # admin / superadmin
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def get_id(self):
        # Prefix so Flask-Login can distinguish Admin sessions from User sessions
        return f"admin-{self.id}"

    def __repr__(self):
        return f"<Admin {self.username}>"


# --------------------------------------------------------------------------
# DESTINATION
# --------------------------------------------------------------------------
class Destination(db.Model):
    __tablename__ = "destinations"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    city = db.Column(db.String(80))
    country = db.Column(db.String(80), nullable=False, index=True)
    description = db.Column(db.Text)
    overview = db.Column(db.Text)

    travel_type = db.Column(db.String(30), index=True)  # adventure/luxury/nature/beach/business/family/solo/couple
    price_per_person = db.Column(db.Float, default=0.0)
    duration_days = db.Column(db.Integer, default=1)
    rating = db.Column(db.Float, default=0.0)
    review_count = db.Column(db.Integer, default=0)

    best_time_to_visit = db.Column(db.String(120))
    safety_tips = db.Column(db.Text)
    things_to_do = db.Column(db.Text)      # newline separated
    hotels = db.Column(db.Text)            # newline separated
    restaurants = db.Column(db.Text)       # newline separated
    transportation = db.Column(db.Text)    # newline separated

    map_lat = db.Column(db.Float)   # used for the maps placeholder
    map_lng = db.Column(db.Float)

    cover_image = db.Column(db.String(255), default="default_destination.jpg")
    is_featured = db.Column(db.Boolean, default=False)
    is_popular = db.Column(db.Boolean, default=False)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    images = db.relationship("Image", backref="destination", lazy="dynamic", cascade="all, delete-orphan")
    bookings = db.relationship("Booking", backref="destination", lazy="dynamic")
    wishlist_items = db.relationship("Wishlist", backref="destination", lazy="dynamic", cascade="all, delete-orphan")
    reviews = db.relationship("Review", backref="destination", lazy="dynamic", cascade="all, delete-orphan")

    def things_to_do_list(self):
        return [x.strip() for x in (self.things_to_do or "").split("\n") if x.strip()]

    def hotels_list(self):
        return [x.strip() for x in (self.hotels or "").split("\n") if x.strip()]

    def restaurants_list(self):
        return [x.strip() for x in (self.restaurants or "").split("\n") if x.strip()]

    def transportation_list(self):
        return [x.strip() for x in (self.transportation or "").split("\n") if x.strip()]

    def recalculate_rating(self):
        reviews = self.reviews.all()
        if reviews:
            self.rating = round(sum(r.rating for r in reviews) / len(reviews), 1)
            self.review_count = len(reviews)
        else:
            self.rating = 0.0
            self.review_count = 0

    def __repr__(self):
        return f"<Destination {self.name}>"


# --------------------------------------------------------------------------
# IMAGE (destination gallery images)
# --------------------------------------------------------------------------
class Image(db.Model):
    __tablename__ = "images"

    id = db.Column(db.Integer, primary_key=True)
    destination_id = db.Column(db.Integer, db.ForeignKey("destinations.id"), nullable=False)
    filename = db.Column(db.String(255), nullable=False)
    original_name = db.Column(db.String(255))
    is_cover = db.Column(db.Boolean, default=False)
    uploaded_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"<Image {self.filename}>"


# --------------------------------------------------------------------------
# BOOKING
# --------------------------------------------------------------------------
class Booking(db.Model):
    __tablename__ = "bookings"

    id = db.Column(db.Integer, primary_key=True)
    booking_reference = db.Column(db.String(20), unique=True, nullable=False, index=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    destination_id = db.Column(db.Integer, db.ForeignKey("destinations.id"), nullable=False)

    hotel_name = db.Column(db.String(120))
    travel_date = db.Column(db.Date, nullable=False)
    return_date = db.Column(db.Date)
    passengers = db.Column(db.Integer, default=1)

    price_per_person = db.Column(db.Float, default=0.0)
    total_amount = db.Column(db.Float, default=0.0)

    status = db.Column(db.String(20), default="confirmed")  # confirmed/cancelled/completed/pending
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    payment = db.relationship("Payment", backref="booking", uselist=False, cascade="all, delete-orphan")

    def is_upcoming(self):
        from datetime import date
        return self.status == "confirmed" and self.travel_date >= date.today()

    def is_past(self):
        from datetime import date
        return self.travel_date < date.today() or self.status == "completed"

    def __repr__(self):
        return f"<Booking {self.booking_reference}>"


# --------------------------------------------------------------------------
# PAYMENT
# --------------------------------------------------------------------------
class Payment(db.Model):
    __tablename__ = "payments"

    id = db.Column(db.Integer, primary_key=True)
    booking_id = db.Column(db.Integer, db.ForeignKey("bookings.id"), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    payment_method = db.Column(db.String(30), default="card")  # card/upi/paypal/mock
    payment_status = db.Column(db.String(20), default="paid")  # paid/pending/refunded/failed
    transaction_id = db.Column(db.String(60), unique=True)
    paid_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"<Payment {self.transaction_id}>"


# --------------------------------------------------------------------------
# WISHLIST
# --------------------------------------------------------------------------
class Wishlist(db.Model):
    __tablename__ = "wishlist"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    destination_id = db.Column(db.Integer, db.ForeignKey("destinations.id"), nullable=False)
    added_at = db.Column(db.DateTime, default=datetime.utcnow)

    __table_args__ = (db.UniqueConstraint("user_id", "destination_id", name="uq_user_destination_wishlist"),)


# --------------------------------------------------------------------------
# MESSAGE (Contact form)
# --------------------------------------------------------------------------
class Message(db.Model):
    __tablename__ = "messages"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True)  # nullable: guests can contact too
    name = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(120), nullable=False)
    subject = db.Column(db.String(200))
    body = db.Column(db.Text, nullable=False)
    is_read = db.Column(db.Boolean, default=False)
    admin_reply = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"<Message from {self.email}>"


# --------------------------------------------------------------------------
# REVIEW
# --------------------------------------------------------------------------
class Review(db.Model):
    __tablename__ = "reviews"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    destination_id = db.Column(db.Integer, db.ForeignKey("destinations.id"), nullable=False)
    rating = db.Column(db.Integer, nullable=False)  # 1-5
    comment = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    __table_args__ = (db.UniqueConstraint("user_id", "destination_id", name="uq_user_destination_review"),)


# --------------------------------------------------------------------------
# TRIP (AI Planner output)
# --------------------------------------------------------------------------
class Trip(db.Model):
    __tablename__ = "trips"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    destination_name = db.Column(db.String(120), nullable=False)
    budget = db.Column(db.Float)
    days = db.Column(db.Integer)
    travel_style = db.Column(db.String(30))
    travelers = db.Column(db.Integer, default=1)
    interests = db.Column(db.String(255))

    itinerary_json = db.Column(db.Text)   # JSON-encoded day-wise itinerary
    packing_list_json = db.Column(db.Text)
    tips_json = db.Column(db.Text)
    estimated_budget_json = db.Column(db.Text)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"<Trip {self.destination_name}>"


# --------------------------------------------------------------------------
# NOTIFICATION
# --------------------------------------------------------------------------
class Notification(db.Model):
    __tablename__ = "notifications"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    title = db.Column(db.String(150), nullable=False)
    body = db.Column(db.String(500))
    category = db.Column(db.String(30), default="general")
    # booking_confirmed / trip_reminder / profile_updated / password_changed / admin_message / general
    is_read = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"<Notification {self.title}>"


# --------------------------------------------------------------------------
# AUDIT LOG (admin activity trail)
# --------------------------------------------------------------------------
class AuditLog(db.Model):
    __tablename__ = "audit_logs"

    id = db.Column(db.Integer, primary_key=True)
    admin_id = db.Column(db.Integer, db.ForeignKey("admins.id"), nullable=True)
    action = db.Column(db.String(200), nullable=False)
    target_type = db.Column(db.String(50))
    target_id = db.Column(db.Integer)
    details = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    admin = db.relationship("Admin")

    def __repr__(self):
        return f"<AuditLog {self.action}>"
