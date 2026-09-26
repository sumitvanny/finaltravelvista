"""
utils.py
Shared helper functions: file uploads, id generation, notifications,
and the mock AI trip-planning engine (structured so a real LLM/API
call can be dropped in later without changing callers).
"""

import os
import re
import json
import uuid
import secrets
from datetime import datetime, timedelta

from flask import current_app
from werkzeug.utils import secure_filename

from extensions import db
from models import Notification


# --------------------------------------------------------------------------
# FILE UPLOADS
# --------------------------------------------------------------------------
def allowed_file(filename):
    ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
    return ext in current_app.config["ALLOWED_IMAGE_EXTENSIONS"]


def save_image(file_storage, folder):
    """
    Saves an uploaded FileStorage object into `folder` with a unique,
    collision-proof filename. Returns the filename (not full path) so it
    can be stored in the database and rendered with url_for('static', ...).
    Silently returns None for anything that isn't an actual uploaded file
    (e.g. an empty string submitted by a non-multipart form post).
    """
    if not file_storage or not hasattr(file_storage, "filename") or not file_storage.filename:
        return None
    if not allowed_file(file_storage.filename):
        raise ValueError("Unsupported file type.")

    os.makedirs(folder, exist_ok=True)
    ext = file_storage.filename.rsplit(".", 1)[-1].lower()
    unique_name = f"{uuid.uuid4().hex}.{ext}"
    safe_name = secure_filename(unique_name)
    file_storage.save(os.path.join(folder, safe_name))
    return safe_name


def delete_image(filename, folder):
    if not filename:
        return
    path = os.path.join(folder, filename)
    if os.path.exists(path):
        try:
            os.remove(path)
        except OSError:
            pass


# --------------------------------------------------------------------------
# ID / TOKEN GENERATORS
# --------------------------------------------------------------------------
def generate_booking_reference():
    return "TV-" + uuid.uuid4().hex[:10].upper()


def generate_transaction_id():
    return "TXN-" + uuid.uuid4().hex[:14].upper()


def generate_reset_token():
    return secrets.token_urlsafe(32)


# --------------------------------------------------------------------------
# NOTIFICATIONS
# --------------------------------------------------------------------------
def create_notification(user_id, title, body, category="general"):
    note = Notification(user_id=user_id, title=title, body=body, category=category)
    db.session.add(note)
    db.session.commit()
    return note


# --------------------------------------------------------------------------
# MOCK AI TRIP PLANNER
# --------------------------------------------------------------------------
# This module intentionally isolates all "AI" decision logic behind the
# generate_trip_plan() function. Today it is rule-based / mock logic.
# To integrate a real model later (e.g. the Anthropic API), replace the
# body of generate_trip_plan() with a call out to the model, keeping the
# same return shape: (itinerary, packing_list, tips, estimated_budget).

_STYLE_ACTIVITIES = {
    "adventure": ["Hiking excursion", "Zip-lining", "White-water rafting", "Mountain biking", "Rock climbing session"],
    "luxury": ["Private spa morning", "Fine-dining experience", "Chauffeured city tour", "Rooftop lounge evening", "Personal shopping tour"],
    "nature": ["Nature reserve walk", "Botanical garden visit", "Wildlife safari", "Sunrise viewpoint hike", "Lakeside picnic"],
    "beach": ["Beach relaxation", "Snorkeling trip", "Sunset sailing cruise", "Beachside cafe crawl", "Water sports session"],
    "business": ["Co-working cafe session", "Networking lunch", "City business district tour", "Evening client dinner", "Conference center visit"],
    "family": ["Theme park visit", "Interactive science museum", "Family-friendly city tour", "Zoo or aquarium visit", "Game night at hotel"],
    "solo": ["Self-guided walking tour", "Local café hopping", "Museum exploration", "Journaling at a scenic viewpoint", "Street food tasting"],
    "couple": ["Sunset dinner cruise", "Couples spa session", "Romantic old-town walk", "Wine tasting evening", "Private photo tour"],
}

_STYLE_PACKING = {
    "adventure": ["Hiking boots", "Quick-dry clothing", "Reusable water bottle", "First-aid kit", "Headlamp"],
    "luxury": ["Formal evening wear", "Dress shoes", "Jewelry case", "Travel garment bag", "Premium sunglasses"],
    "nature": ["Insect repellent", "Binoculars", "Comfortable walking shoes", "Sun hat", "Reusable water bottle"],
    "beach": ["Swimwear", "Sunscreen SPF 50+", "Beach towel", "Flip-flops", "Waterproof phone pouch"],
    "business": ["Formal attire", "Laptop & charger", "Business cards", "Portable power bank", "Travel iron"],
    "family": ["Kids' entertainment kit", "Snacks", "First-aid kit", "Extra clothing sets", "Portable charger"],
    "solo": ["Universal power adapter", "Journal & pen", "Portable charger", "Comfortable daypack", "Offline maps download"],
    "couple": ["Matching outfits (optional)", "Camera", "Comfortable walking shoes", "Light jacket for evenings", "Portable charger"],
}

_GENERAL_TIPS = [
    "Book accommodations at least 3-4 weeks in advance for the best rates.",
    "Keep both digital and physical copies of important travel documents.",
    "Notify your bank of travel dates to avoid card blocks.",
    "Check visa and entry requirements well ahead of departure.",
    "Purchase travel insurance for medical and trip-cancellation coverage.",
]

_STYLE_TIPS = {
    "adventure": "Check weather and trail conditions daily; hire local guides for high-risk activities.",
    "luxury": "Reserve premium experiences (fine dining, spas) ahead of time — they fill up quickly.",
    "nature": "Pack eco-friendly gear and respect wildlife viewing distances.",
    "beach": "Reapply sunscreen every 2 hours and stay hydrated in the heat.",
    "business": "Confirm meeting locations and time zones the day before each appointment.",
    "family": "Build in downtime between activities to avoid overtiring younger travelers.",
    "solo": "Share your itinerary with someone back home and check in periodically.",
    "couple": "Balance planned activities with unstructured time to simply enjoy each other's company.",
}


def _budget_split(total_budget, days):
    """Rule-based allocation of an overall budget across categories."""
    accommodation = round(total_budget * 0.40, 2)
    food = round(total_budget * 0.25, 2)
    activities = round(total_budget * 0.20, 2)
    transport = round(total_budget * 0.10, 2)
    misc = round(total_budget - (accommodation + food + activities + transport), 2)
    return {
        "accommodation": accommodation,
        "food": food,
        "activities": activities,
        "local_transport": transport,
        "miscellaneous": misc,
        "per_day_average": round(total_budget / max(days, 1), 2),
    }


def generate_trip_plan(destination, budget, days, travelers, travel_style, interests=None):
    """
    Rule-based mock "AI" trip planner. Produces a day-wise itinerary,
    packing list, travel tips, and an estimated budget breakdown.

    Returns a dict — this shape is the contract a real AI integration
    should preserve:
        {
            "destination": str,
            "days": [{ "day": int, "title": str, "schedule": [...] }],
            "packing_list": [str, ...],
            "tips": [str, ...],
            "estimated_budget": {...}
        }
    """
    activities = _STYLE_ACTIVITIES.get(travel_style, _STYLE_ACTIVITIES["solo"])
    packing = list(_STYLE_PACKING.get(travel_style, _STYLE_PACKING["solo"]))

    interest_list = []
    if interests:
        interest_list = [i.strip() for i in re.split(r"[,/]", interests) if i.strip()]

    itinerary = []
    for day_num in range(1, days + 1):
        activity = activities[(day_num - 1) % len(activities)]
        interest_note = f" Focused around your interest in {interest_list[(day_num - 1) % len(interest_list)]}." \
            if interest_list else ""
        schedule = [
            {"time": "08:00 AM", "activity": "Breakfast at local cafe"},
            {"time": "10:00 AM", "activity": f"{activity} in {destination}.{interest_note}"},
            {"time": "01:00 PM", "activity": "Lunch break & rest"},
            {"time": "03:00 PM", "activity": f"Explore {destination} neighborhoods / free time"},
            {"time": "07:00 PM", "activity": "Dinner & evening leisure"},
        ]
        itinerary.append({
            "day": day_num,
            "title": f"Day {day_num}: {activity}",
            "schedule": schedule,
        })

    tips = [_STYLE_TIPS.get(travel_style, _STYLE_TIPS["solo"])] + _GENERAL_TIPS
    estimated_budget = _budget_split(budget, days)
    estimated_budget["travelers"] = travelers
    estimated_budget["per_person_total"] = round(budget / max(travelers, 1), 2)

    return {
        "destination": destination,
        "days": itinerary,
        "packing_list": packing,
        "tips": tips,
        "estimated_budget": estimated_budget,
    }


def serialize_trip_plan(plan):
    """Splits a plan dict into the JSON strings stored on the Trip model."""
    return (
        json.dumps(plan["days"]),
        json.dumps(plan["packing_list"]),
        json.dumps(plan["tips"]),
        json.dumps(plan["estimated_budget"]),
    )


def deserialize_trip(trip):
    """Rehydrates a Trip DB row back into displayable Python structures."""
    return {
        "destination": trip.destination_name,
        "days": json.loads(trip.itinerary_json or "[]"),
        "packing_list": json.loads(trip.packing_list_json or "[]"),
        "tips": json.loads(trip.tips_json or "[]"),
        "estimated_budget": json.loads(trip.estimated_budget_json or "{}"),
    }
