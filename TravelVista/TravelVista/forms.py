"""
forms.py
Flask-WTF form definitions with server-side validation.
"""

from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed
from wtforms import (
    StringField, PasswordField, BooleanField, TextAreaField, SelectField,
    IntegerField, FloatField, DateField, HiddenField
)
from wtforms.validators import (
    DataRequired, Email, Length, EqualTo, Optional, NumberRange, ValidationError
)
from models import User


# --------------------------------------------------------------------------
# AUTH
# --------------------------------------------------------------------------
class RegisterForm(FlaskForm):
    username = StringField("Username", validators=[DataRequired(), Length(min=3, max=64)])
    email = StringField("Email", validators=[DataRequired(), Email(), Length(max=120)])
    full_name = StringField("Full Name", validators=[DataRequired(), Length(max=120)])
    password = PasswordField("Password", validators=[DataRequired(), Length(min=8, max=128)])
    confirm_password = PasswordField(
        "Confirm Password", validators=[DataRequired(), EqualTo("password", message="Passwords must match.")]
    )

    def validate_username(self, field):
        if User.query.filter_by(username=field.data.strip()).first():
            raise ValidationError("That username is already taken.")

    def validate_email(self, field):
        if User.query.filter_by(email=field.data.strip().lower()).first():
            raise ValidationError("An account with that email already exists.")


class LoginForm(FlaskForm):
    email = StringField("Email", validators=[DataRequired(), Email()])
    password = PasswordField("Password", validators=[DataRequired()])
    remember = BooleanField("Remember Me")


class AdminLoginForm(FlaskForm):
    username = StringField("Username", validators=[DataRequired()])
    password = PasswordField("Password", validators=[DataRequired()])


class ForgotPasswordForm(FlaskForm):
    email = StringField("Email", validators=[DataRequired(), Email()])


class ResetPasswordForm(FlaskForm):
    password = PasswordField("New Password", validators=[DataRequired(), Length(min=8, max=128)])
    confirm_password = PasswordField(
        "Confirm New Password", validators=[DataRequired(), EqualTo("password", message="Passwords must match.")]
    )


class ChangePasswordForm(FlaskForm):
    current_password = PasswordField("Current Password", validators=[DataRequired()])
    new_password = PasswordField("New Password", validators=[DataRequired(), Length(min=8, max=128)])
    confirm_password = PasswordField(
        "Confirm New Password", validators=[DataRequired(), EqualTo("new_password", message="Passwords must match.")]
    )


# --------------------------------------------------------------------------
# PROFILE
# --------------------------------------------------------------------------
class ProfileForm(FlaskForm):
    full_name = StringField("Full Name", validators=[DataRequired(), Length(max=120)])
    phone = StringField("Phone", validators=[Optional(), Length(max=30)])
    address = StringField("Address", validators=[Optional(), Length(max=255)])
    country = StringField("Country", validators=[Optional(), Length(max=80)])
    passport_number = StringField("Passport Number", validators=[Optional(), Length(max=50)])
    emergency_contact = StringField("Emergency Contact", validators=[Optional(), Length(max=120)])
    profile_picture = FileField("Profile Picture", validators=[
        Optional(), FileAllowed(["jpg", "jpeg", "png", "gif", "webp"], "Images only!")
    ])


class DeleteAccountForm(FlaskForm):
    password = PasswordField("Confirm Password", validators=[DataRequired()])


# --------------------------------------------------------------------------
# CONTACT
# --------------------------------------------------------------------------
class ContactForm(FlaskForm):
    name = StringField("Name", validators=[DataRequired(), Length(max=120)])
    email = StringField("Email", validators=[DataRequired(), Email()])
    subject = StringField("Subject", validators=[Optional(), Length(max=200)])
    message = TextAreaField("Message", validators=[DataRequired(), Length(max=3000)])


# --------------------------------------------------------------------------
# BOOKING
# --------------------------------------------------------------------------
class BookingForm(FlaskForm):
    destination_id = HiddenField(validators=[DataRequired()])
    hotel_name = StringField("Hotel", validators=[DataRequired(), Length(max=120)])
    travel_date = DateField("Travel Date", validators=[DataRequired()], format="%Y-%m-%d")
    return_date = DateField("Return Date", validators=[Optional()], format="%Y-%m-%d")
    passengers = IntegerField("Passengers", validators=[DataRequired(), NumberRange(min=1, max=20)])
    payment_method = SelectField(
        "Payment Method",
        choices=[("card", "Credit / Debit Card"), ("upi", "UPI"), ("paypal", "PayPal")],
        validators=[DataRequired()],
    )


# --------------------------------------------------------------------------
# REVIEW
# --------------------------------------------------------------------------
class ReviewForm(FlaskForm):
    rating = IntegerField("Rating", validators=[DataRequired(), NumberRange(min=1, max=5)])
    comment = TextAreaField("Comment", validators=[Optional(), Length(max=1500)])


# --------------------------------------------------------------------------
# AI TRIP PLANNER
# --------------------------------------------------------------------------
class PlannerForm(FlaskForm):
    destination = StringField("Destination", validators=[DataRequired(), Length(max=120)])
    budget = FloatField("Budget", validators=[DataRequired(), NumberRange(min=1)])
    days = IntegerField("Number of Days", validators=[DataRequired(), NumberRange(min=1, max=60)])
    travelers = IntegerField("Number of Travelers", validators=[DataRequired(), NumberRange(min=1, max=20)])
    travel_style = SelectField(
        "Travel Style",
        choices=[
            ("adventure", "Adventure"), ("luxury", "Luxury"), ("nature", "Nature"),
            ("beach", "Beach"), ("business", "Business"), ("family", "Family"),
            ("solo", "Solo"), ("couple", "Couple"),
        ],
        validators=[DataRequired()],
    )
    interests = StringField("Interests (comma separated)", validators=[Optional(), Length(max=255)])


# --------------------------------------------------------------------------
# ADMIN: DESTINATION CRUD
# --------------------------------------------------------------------------
class DestinationForm(FlaskForm):
    name = StringField("Name", validators=[DataRequired(), Length(max=120)])
    city = StringField("City", validators=[Optional(), Length(max=80)])
    country = StringField("Country", validators=[DataRequired(), Length(max=80)])
    description = TextAreaField("Short Description", validators=[DataRequired(), Length(max=500)])
    overview = TextAreaField("Overview", validators=[Optional(), Length(max=3000)])
    travel_type = SelectField(
        "Travel Type",
        choices=[
            ("adventure", "Adventure"), ("luxury", "Luxury"), ("nature", "Nature"),
            ("beach", "Beach"), ("business", "Business"), ("family", "Family"),
            ("solo", "Solo"), ("couple", "Couple"),
        ],
        validators=[DataRequired()],
    )
    price_per_person = FloatField("Price Per Person", validators=[DataRequired(), NumberRange(min=0)])
    duration_days = IntegerField("Typical Duration (days)", validators=[DataRequired(), NumberRange(min=1)])
    best_time_to_visit = StringField("Best Time To Visit", validators=[Optional(), Length(max=120)])
    safety_tips = TextAreaField("Safety Tips", validators=[Optional(), Length(max=1500)])
    things_to_do = TextAreaField("Things To Do (one per line)", validators=[Optional()])
    hotels = TextAreaField("Hotels (one per line)", validators=[Optional()])
    restaurants = TextAreaField("Restaurants (one per line)", validators=[Optional()])
    transportation = TextAreaField("Transportation (one per line)", validators=[Optional()])
    map_lat = FloatField("Map Latitude", validators=[Optional()])
    map_lng = FloatField("Map Longitude", validators=[Optional()])
    is_featured = BooleanField("Featured")
    is_popular = BooleanField("Popular")
    cover_image = FileField("Cover Image", validators=[
        Optional(), FileAllowed(["jpg", "jpeg", "png", "gif", "webp"], "Images only!")
    ])


class GalleryUploadForm(FlaskForm):
    images = FileField("Gallery Images", validators=[
        Optional(), FileAllowed(["jpg", "jpeg", "png", "gif", "webp"], "Images only!")
    ])
