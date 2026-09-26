"""
routes.py
Main (non-admin) blueprint: homepage, search, destinations, AI planner,
bookings, wishlist, dashboard, profile, contact, static pages.
"""

from datetime import date, datetime

from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify, abort, current_app
from flask_login import login_required, current_user
from sqlalchemy import or_

from extensions import db
from models import (
    Destination, Booking, Wishlist, Message, Review, Trip, Notification, Payment, Image, User
)
from forms import (
    ProfileForm, DeleteAccountForm, ChangePasswordForm, ContactForm,
    BookingForm, ReviewForm, PlannerForm
)
from utils import (
    save_image, delete_image, generate_booking_reference, generate_transaction_id,
    create_notification, generate_trip_plan, serialize_trip_plan, deserialize_trip
)

main_bp = Blueprint("main", __name__)


# --------------------------------------------------------------------------
# HOMEPAGE / STATIC PAGES
# --------------------------------------------------------------------------
@main_bp.route("/")
def index():
    featured = Destination.query.filter_by(is_featured=True).order_by(Destination.rating.desc()).limit(6).all()
    popular = Destination.query.filter_by(is_popular=True).order_by(Destination.review_count.desc()).limit(8).all()
    stats = {
        "destinations": Destination.query.count(),
        "travelers": User.query.count(),
        "bookings": Booking.query.count(),
        "countries": db.session.query(Destination.country).distinct().count(),
    }
    return render_template("index.html", featured=featured, popular=popular, stats=stats)


@main_bp.route("/about")
def about():
    return render_template("about.html")


@main_bp.route("/contact", methods=["GET", "POST"])
def contact():
    form = ContactForm()
    if current_user.is_authenticated and request.method == "GET":
        form.name.data = current_user.full_name
        form.email.data = current_user.email

    if form.validate_on_submit():
        msg = Message(
            user_id=current_user.id if current_user.is_authenticated else None,
            name=form.name.data.strip(),
            email=form.email.data.strip().lower(),
            subject=form.subject.data.strip() if form.subject.data else None,
            body=form.message.data.strip(),
        )
        db.session.add(msg)
        db.session.commit()
        flash("Your message has been sent! Our team will get back to you soon.", "success")
        return redirect(url_for("main.contact"))

    return render_template("contact.html", form=form)


# --------------------------------------------------------------------------
# SEARCH
# --------------------------------------------------------------------------
@main_bp.route("/search")
def search():
    query = request.args.get("q", "").strip()
    country = request.args.get("country", "").strip()
    travel_type = request.args.get("travel_type", "").strip()
    min_budget = request.args.get("min_budget", type=float)
    max_budget = request.args.get("max_budget", type=float)
    min_duration = request.args.get("min_duration", type=int)
    min_rating = request.args.get("min_rating", type=float)
    page = request.args.get("page", 1, type=int)

    q = Destination.query
    if query:
        like = f"%{query}%"
        q = q.filter(or_(Destination.name.ilike(like), Destination.city.ilike(like), Destination.country.ilike(like)))
    if country:
        q = q.filter(Destination.country.ilike(f"%{country}%"))
    if travel_type:
        q = q.filter(Destination.travel_type == travel_type)
    if min_budget is not None:
        q = q.filter(Destination.price_per_person >= min_budget)
    if max_budget is not None:
        q = q.filter(Destination.price_per_person <= max_budget)
    if min_duration is not None:
        q = q.filter(Destination.duration_days >= min_duration)
    if min_rating is not None:
        q = q.filter(Destination.rating >= min_rating)

    pagination = q.order_by(Destination.rating.desc()).paginate(
        page=page, per_page=current_app.config["ITEMS_PER_PAGE"], error_out=False
    )

    travel_types = ["adventure", "luxury", "nature", "beach", "business", "family", "solo", "couple"]
    return render_template(
        "search.html", pagination=pagination, destinations=pagination.items,
        travel_types=travel_types, filters=request.args
    )


# --------------------------------------------------------------------------
# DESTINATION DETAIL
# --------------------------------------------------------------------------
@main_bp.route("/destination/<int:destination_id>")
def destination_detail(destination_id):
    dest = Destination.query.get_or_404(destination_id)
    reviews = dest.reviews.order_by(Review.created_at.desc()).all()
    gallery = dest.images.order_by(Image.uploaded_at.asc()).all()

    user_review = None
    in_wishlist = False
    if current_user.is_authenticated:
        user_review = Review.query.filter_by(user_id=current_user.id, destination_id=dest.id).first()
        in_wishlist = Wishlist.query.filter_by(user_id=current_user.id, destination_id=dest.id).first() is not None

    review_form = ReviewForm()
    related = Destination.query.filter(
        Destination.country == dest.country, Destination.id != dest.id
    ).limit(4).all()

    return render_template(
        "destination.html", dest=dest, reviews=reviews, gallery=gallery,
        user_review=user_review, in_wishlist=in_wishlist, review_form=review_form, related=related
    )


@main_bp.route("/destination/<int:destination_id>/review", methods=["POST"])
@login_required
def submit_review(destination_id):
    dest = Destination.query.get_or_404(destination_id)
    form = ReviewForm()
    if form.validate_on_submit():
        existing = Review.query.filter_by(user_id=current_user.id, destination_id=dest.id).first()
        if existing:
            existing.rating = form.rating.data
            existing.comment = form.comment.data
            existing.updated_at = datetime.utcnow()
            flash("Your review has been updated.", "success")
        else:
            review = Review(
                user_id=current_user.id, destination_id=dest.id,
                rating=form.rating.data, comment=form.comment.data
            )
            db.session.add(review)
            flash("Thanks for your review!", "success")
        db.session.commit()
        dest.recalculate_rating()
        db.session.commit()
    else:
        flash("Please provide a valid rating (1-5).", "danger")
    return redirect(url_for("main.destination_detail", destination_id=destination_id))


@main_bp.route("/destination/<int:destination_id>/review/delete", methods=["POST"])
@login_required
def delete_review(destination_id):
    review = Review.query.filter_by(user_id=current_user.id, destination_id=destination_id).first_or_404()
    dest = review.destination
    db.session.delete(review)
    db.session.commit()
    dest.recalculate_rating()
    db.session.commit()
    flash("Your review has been removed.", "info")
    return redirect(url_for("main.destination_detail", destination_id=destination_id))


# --------------------------------------------------------------------------
# WISHLIST
# --------------------------------------------------------------------------
@main_bp.route("/wishlist")
@login_required
def wishlist():
    items = Wishlist.query.filter_by(user_id=current_user.id).order_by(Wishlist.added_at.desc()).all()
    return render_template("wishlist.html", items=items)


@main_bp.route("/wishlist/toggle/<int:destination_id>", methods=["POST"])
@login_required
def toggle_wishlist(destination_id):
    dest = Destination.query.get_or_404(destination_id)
    existing = Wishlist.query.filter_by(user_id=current_user.id, destination_id=dest.id).first()
    if existing:
        db.session.delete(existing)
        db.session.commit()
        added = False
    else:
        db.session.add(Wishlist(user_id=current_user.id, destination_id=dest.id))
        db.session.commit()
        added = True

    if request.headers.get("X-Requested-With") == "XMLHttpRequest":
        return jsonify({"success": True, "added": added})

    flash("Added to wishlist." if added else "Removed from wishlist.", "success")
    return redirect(request.referrer or url_for("main.destination_detail", destination_id=destination_id))


# --------------------------------------------------------------------------
# AI TRIP PLANNER
# --------------------------------------------------------------------------
@main_bp.route("/planner", methods=["GET", "POST"])
@login_required
def planner():
    form = PlannerForm()
    plan = None
    if form.validate_on_submit():
        plan = generate_trip_plan(
            destination=form.destination.data.strip(),
            budget=form.budget.data,
            days=form.days.data,
            travelers=form.travelers.data,
            travel_style=form.travel_style.data,
            interests=form.interests.data,
        )
        itinerary_json, packing_json, tips_json, budget_json = serialize_trip_plan(plan)
        trip = Trip(
            user_id=current_user.id,
            destination_name=plan["destination"],
            budget=form.budget.data,
            days=form.days.data,
            travel_style=form.travel_style.data,
            travelers=form.travelers.data,
            interests=form.interests.data,
            itinerary_json=itinerary_json,
            packing_list_json=packing_json,
            tips_json=tips_json,
            estimated_budget_json=budget_json,
        )
        db.session.add(trip)
        db.session.commit()
        flash("Your itinerary has been generated and saved to My Trips!", "success")

    return render_template("planner.html", form=form, plan=plan)


@main_bp.route("/mytrips")
@login_required
def mytrips():
    trips = current_user.trips.order_by(Trip.created_at.desc()).all()
    parsed_trips = [(t, deserialize_trip(t)) for t in trips]
    return render_template("mytrips.html", parsed_trips=parsed_trips)


@main_bp.route("/mytrips/<int:trip_id>/delete", methods=["POST"])
@login_required
def delete_trip(trip_id):
    trip = Trip.query.filter_by(id=trip_id, user_id=current_user.id).first_or_404()
    db.session.delete(trip)
    db.session.commit()
    flash("Trip plan deleted.", "info")
    return redirect(url_for("main.mytrips"))


# --------------------------------------------------------------------------
# BOOKINGS
# --------------------------------------------------------------------------
@main_bp.route("/booking/<int:destination_id>", methods=["GET", "POST"])
@login_required
def booking(destination_id):
    dest = Destination.query.get_or_404(destination_id)
    form = BookingForm(destination_id=destination_id)

    if form.validate_on_submit():
        total = dest.price_per_person * form.passengers.data
        new_booking = Booking(
            booking_reference=generate_booking_reference(),
            user_id=current_user.id,
            destination_id=dest.id,
            hotel_name=form.hotel_name.data.strip(),
            travel_date=form.travel_date.data,
            return_date=form.return_date.data,
            passengers=form.passengers.data,
            price_per_person=dest.price_per_person,
            total_amount=total,
            status="confirmed",
        )
        db.session.add(new_booking)
        db.session.flush()  # get new_booking.id before commit

        payment = Payment(
            booking_id=new_booking.id,
            amount=total,
            payment_method=form.payment_method.data,
            payment_status="paid",
            transaction_id=generate_transaction_id(),
        )
        db.session.add(payment)
        db.session.commit()

        create_notification(
            current_user.id, "Booking Confirmed",
            f"Your trip to {dest.name} on {new_booking.travel_date.strftime('%b %d, %Y')} is confirmed. "
            f"Reference: {new_booking.booking_reference}",
            category="booking_confirmed",
        )

        return redirect(url_for("main.booking_confirmation", booking_id=new_booking.id))

    return render_template("booking.html", dest=dest, form=form)


@main_bp.route("/booking/confirmation/<int:booking_id>")
@login_required
def booking_confirmation(booking_id):
    bk = Booking.query.filter_by(id=booking_id, user_id=current_user.id).first_or_404()
    return render_template("booking_confirmation.html", booking=bk)


@main_bp.route("/booking/<int:booking_id>/cancel", methods=["POST"])
@login_required
def cancel_booking(booking_id):
    bk = Booking.query.filter_by(id=booking_id, user_id=current_user.id).first_or_404()
    if bk.status == "confirmed":
        bk.status = "cancelled"
        if bk.payment:
            bk.payment.payment_status = "refunded"
        db.session.commit()
        create_notification(
            current_user.id, "Booking Cancelled",
            f"Your booking {bk.booking_reference} has been cancelled.", category="general"
        )
        flash("Booking cancelled successfully.", "info")
    else:
        flash("This booking cannot be cancelled.", "warning")
    return redirect(url_for("main.mybookings"))


@main_bp.route("/mybookings")
@login_required
def mybookings():
    all_bookings = current_user.bookings.order_by(Booking.travel_date.desc()).all()
    upcoming = [b for b in all_bookings if b.is_upcoming()]
    past = [b for b in all_bookings if b.is_past() and b.status != "cancelled"]
    cancelled = [b for b in all_bookings if b.status == "cancelled"]
    return render_template("mybookings.html", upcoming=upcoming, past=past, cancelled=cancelled)


# --------------------------------------------------------------------------
# DASHBOARD
# --------------------------------------------------------------------------
@main_bp.route("/dashboard")
@login_required
def dashboard():
    bookings = current_user.bookings.order_by(Booking.created_at.desc()).all()
    upcoming = [b for b in bookings if b.is_upcoming()][:5]
    past = [b for b in bookings if b.is_past()][:5]
    wishlist_items = current_user.wishlist_items.order_by(Wishlist.added_at.desc()).limit(6).all()
    notifications = current_user.notifications.order_by(Notification.created_at.desc()).limit(8).all()
    recent_trips = current_user.trips.order_by(Trip.created_at.desc()).limit(3).all()

    stats = {
        "total_bookings": len(bookings),
        "upcoming_trips": len(upcoming),
        "wishlist_count": current_user.wishlist_items.count(),
        "reviews_written": current_user.reviews.count(),
        "profile_completion": current_user.profile_completion(),
    }
    return render_template(
        "dashboard.html", upcoming=upcoming, past=past, wishlist_items=wishlist_items,
        notifications=notifications, recent_trips=recent_trips, stats=stats
    )


@main_bp.route("/notifications/mark-read/<int:notification_id>", methods=["POST"])
@login_required
def mark_notification_read(notification_id):
    note = Notification.query.filter_by(id=notification_id, user_id=current_user.id).first_or_404()
    note.is_read = True
    db.session.commit()
    return jsonify({"success": True})


@main_bp.route("/notifications/mark-all-read", methods=["POST"])
@login_required
def mark_all_notifications_read():
    current_user.notifications.filter_by(is_read=False).update({"is_read": True})
    db.session.commit()
    return jsonify({"success": True})


# --------------------------------------------------------------------------
# PROFILE
# --------------------------------------------------------------------------
@main_bp.route("/profile", methods=["GET", "POST"])
@login_required
def profile():
    form = ProfileForm(obj=current_user)
    delete_form = DeleteAccountForm()
    password_form = ChangePasswordForm()

    if form.validate_on_submit():
        current_user.full_name = form.full_name.data.strip()
        current_user.phone = form.phone.data
        current_user.address = form.address.data
        current_user.country = form.country.data
        current_user.passport_number = form.passport_number.data
        current_user.emergency_contact = form.emergency_contact.data

        if form.profile_picture.data:
            try:
                filename = save_image(form.profile_picture.data, current_app.config["PROFILE_UPLOAD_FOLDER"])
                if filename:
                    current_user.profile_image = filename
            except ValueError as e:
                flash(str(e), "danger")
                return redirect(url_for("main.profile"))

        db.session.commit()
        create_notification(current_user.id, "Profile Updated", "Your profile details were updated.", category="profile_updated")
        flash("Profile updated successfully.", "success")
        return redirect(url_for("main.profile"))

    return render_template("profile.html", form=form, delete_form=delete_form, password_form=password_form)


@main_bp.route("/profile/change-password", methods=["POST"])
@login_required
def change_password():
    form = ChangePasswordForm()
    if form.validate_on_submit():
        if not current_user.check_password(form.current_password.data):
            flash("Current password is incorrect.", "danger")
        else:
            current_user.set_password(form.new_password.data)
            db.session.commit()
            create_notification(current_user.id, "Password Changed", "Your password was changed successfully.", category="password_changed")
            flash("Password changed successfully.", "success")
    else:
        flash("Please correct the errors and try again.", "danger")
    return redirect(url_for("main.profile"))


@main_bp.route("/profile/delete", methods=["POST"])
@login_required
def delete_account():
    form = DeleteAccountForm()
    if form.validate_on_submit() and current_user.check_password(form.password.data):
        from flask_login import logout_user
        user_id = current_user.id
        logout_user()
        User.query.filter_by(id=user_id).delete()
        db.session.commit()
        flash("Your account has been permanently deleted.", "info")
        return redirect(url_for("main.index"))

    flash("Incorrect password. Account not deleted.", "danger")
    return redirect(url_for("main.profile"))
