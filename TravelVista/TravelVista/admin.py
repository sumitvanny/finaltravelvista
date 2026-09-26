"""
admin.py
Admin blueprint: separate authentication from regular users, dashboard
with analytics, and full CRUD for users, bookings, destinations, and
contact messages. All mutating actions are written to the AuditLog.
"""

from datetime import datetime, timedelta
from functools import wraps

from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify, current_app
from flask_login import login_user, logout_user, login_required, current_user
from sqlalchemy import func, or_

from extensions import db
from models import (
    Admin, User, Destination, Booking, Message, Review, Payment, Image, AuditLog, Notification
)
from forms import AdminLoginForm, DestinationForm, GalleryUploadForm
from utils import save_image, delete_image, create_notification

admin_bp = Blueprint("admin", __name__, url_prefix="/admin")


def admin_required(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        if not current_user.is_authenticated or not isinstance(current_user._get_current_object(), Admin):
            flash("Admin access required.", "danger")
            return redirect(url_for("admin.admin_login"))
        return f(*args, **kwargs)
    return wrapper


def log_action(action, target_type=None, target_id=None, details=None):
    entry = AuditLog(
        admin_id=current_user.id if isinstance(current_user._get_current_object(), Admin) else None,
        action=action, target_type=target_type, target_id=target_id, details=details,
    )
    db.session.add(entry)
    db.session.commit()


# --------------------------------------------------------------------------
# ADMIN AUTH
# --------------------------------------------------------------------------
@admin_bp.route("/login", methods=["GET", "POST"])
def admin_login():
    if current_user.is_authenticated and isinstance(current_user._get_current_object(), Admin):
        return redirect(url_for("admin.dashboard"))

    form = AdminLoginForm()
    if form.validate_on_submit():
        admin = Admin.query.filter_by(username=form.username.data.strip()).first()
        if admin and admin.check_password(form.password.data):
            login_user(admin)
            log_action(f"Admin '{admin.username}' logged in")
            return redirect(url_for("admin.dashboard"))
        flash("Invalid admin credentials.", "danger")

    return render_template("admin/admin_login.html", form=form)


@admin_bp.route("/logout")
@login_required
def admin_logout():
    log_action(f"Admin '{current_user.username}' logged out")
    logout_user()
    flash("Admin logged out.", "info")
    return redirect(url_for("admin.admin_login"))


# --------------------------------------------------------------------------
# DASHBOARD / ANALYTICS
# --------------------------------------------------------------------------
@admin_bp.route("/")
@admin_bp.route("/dashboard")
@admin_required
def dashboard():
    total_users = User.query.count()
    total_bookings = Booking.query.count()
    total_revenue = db.session.query(func.coalesce(func.sum(Payment.amount), 0)).filter(
        Payment.payment_status == "paid"
    ).scalar()
    total_destinations = Destination.query.count()
    unread_messages = Message.query.filter_by(is_read=False).count()

    recent_bookings = Booking.query.order_by(Booking.created_at.desc()).limit(8).all()
    recent_users = User.query.order_by(User.created_at.desc()).limit(8).all()
    recent_activity = AuditLog.query.order_by(AuditLog.created_at.desc()).limit(10).all()

    # Bookings over the last 6 months for a simple chart
    six_months_ago = datetime.utcnow() - timedelta(days=180)
    monthly_counts = (
        db.session.query(func.strftime("%Y-%m", Booking.created_at), func.count(Booking.id))
        .filter(Booking.created_at >= six_months_ago)
        .group_by(func.strftime("%Y-%m", Booking.created_at))
        .order_by(func.strftime("%Y-%m", Booking.created_at))
        .all()
    )

    top_destinations = (
        db.session.query(Destination.name, func.count(Booking.id).label("cnt"))
        .join(Booking, Booking.destination_id == Destination.id)
        .group_by(Destination.id)
        .order_by(func.count(Booking.id).desc())
        .limit(5)
        .all()
    )

    return render_template(
        "admin/admin_dashboard.html",
        total_users=total_users, total_bookings=total_bookings, total_revenue=total_revenue,
        total_destinations=total_destinations, unread_messages=unread_messages,
        recent_bookings=recent_bookings, recent_users=recent_users, recent_activity=recent_activity,
        monthly_counts=monthly_counts, top_destinations=top_destinations,
    )


# --------------------------------------------------------------------------
# USER MANAGEMENT
# --------------------------------------------------------------------------
@admin_bp.route("/users")
@admin_required
def users():
    query = request.args.get("q", "").strip()
    page = request.args.get("page", 1, type=int)
    q = User.query
    if query:
        like = f"%{query}%"
        q = q.filter(or_(User.username.ilike(like), User.email.ilike(like), User.full_name.ilike(like)))
    pagination = q.order_by(User.created_at.desc()).paginate(
        page=page, per_page=current_app.config["ADMIN_ITEMS_PER_PAGE"], error_out=False
    )
    return render_template("admin/users.html", pagination=pagination, users=pagination.items, query=query)


@admin_bp.route("/users/<int:user_id>/toggle-active", methods=["POST"])
@admin_required
def toggle_user_active(user_id):
    user = User.query.get_or_404(user_id)
    user.is_active_account = not user.is_active_account
    db.session.commit()
    log_action(f"{'Activated' if user.is_active_account else 'Deactivated'} user {user.username}", "User", user.id)
    flash(f"User {user.username} {'activated' if user.is_active_account else 'deactivated'}.", "success")
    return redirect(url_for("admin.users"))


@admin_bp.route("/users/<int:user_id>/delete", methods=["POST"])
@admin_required
def delete_user(user_id):
    user = User.query.get_or_404(user_id)
    username = user.username
    db.session.delete(user)
    db.session.commit()
    log_action(f"Deleted user {username}", "User", user_id)
    flash(f"User {username} deleted.", "info")
    return redirect(url_for("admin.users"))


# --------------------------------------------------------------------------
# BOOKING MANAGEMENT
# --------------------------------------------------------------------------
@admin_bp.route("/bookings")
@admin_required
def bookings():
    status = request.args.get("status", "").strip()
    page = request.args.get("page", 1, type=int)
    q = Booking.query
    if status:
        q = q.filter_by(status=status)
    pagination = q.order_by(Booking.created_at.desc()).paginate(
        page=page, per_page=current_app.config["ADMIN_ITEMS_PER_PAGE"], error_out=False
    )
    return render_template("admin/bookings.html", pagination=pagination, bookings=pagination.items, status=status)


@admin_bp.route("/bookings/<int:booking_id>/status", methods=["POST"])
@admin_required
def update_booking_status(booking_id):
    bk = Booking.query.get_or_404(booking_id)
    new_status = request.form.get("status")
    if new_status in {"confirmed", "cancelled", "completed", "pending"}:
        bk.status = new_status
        db.session.commit()
        log_action(f"Updated booking {bk.booking_reference} to {new_status}", "Booking", bk.id)
        create_notification(
            bk.user_id, "Booking Status Updated",
            f"Your booking {bk.booking_reference} status changed to {new_status}.", category="general"
        )
        flash("Booking status updated.", "success")
    return redirect(url_for("admin.bookings"))


# --------------------------------------------------------------------------
# DESTINATION MANAGEMENT (CRUD)
# --------------------------------------------------------------------------
@admin_bp.route("/destinations")
@admin_required
def destinations():
    query = request.args.get("q", "").strip()
    page = request.args.get("page", 1, type=int)
    q = Destination.query
    if query:
        like = f"%{query}%"
        q = q.filter(or_(Destination.name.ilike(like), Destination.country.ilike(like)))
    pagination = q.order_by(Destination.created_at.desc()).paginate(
        page=page, per_page=current_app.config["ADMIN_ITEMS_PER_PAGE"], error_out=False
    )
    return render_template("admin/destinations.html", pagination=pagination, destinations=pagination.items, query=query)


@admin_bp.route("/destinations/new", methods=["GET", "POST"])
@admin_required
def new_destination():
    form = DestinationForm()
    if form.validate_on_submit():
        dest = Destination()
        _apply_destination_form(dest, form)
        db.session.add(dest)
        db.session.commit()
        log_action(f"Created destination {dest.name}", "Destination", dest.id)
        flash("Destination created.", "success")
        return redirect(url_for("admin.destinations"))
    return render_template("admin/destination_form.html", form=form, mode="create")


@admin_bp.route("/destinations/<int:destination_id>/edit", methods=["GET", "POST"])
@admin_required
def edit_destination(destination_id):
    dest = Destination.query.get_or_404(destination_id)
    form = DestinationForm(obj=dest)
    gallery_form = GalleryUploadForm()

    if form.validate_on_submit():
        _apply_destination_form(dest, form)
        db.session.commit()
        log_action(f"Updated destination {dest.name}", "Destination", dest.id)
        flash("Destination updated.", "success")
        return redirect(url_for("admin.destinations"))

    return render_template("admin/destination_form.html", form=form, mode="edit", dest=dest, gallery_form=gallery_form)


@admin_bp.route("/destinations/<int:destination_id>/delete", methods=["POST"])
@admin_required
def delete_destination(destination_id):
    dest = Destination.query.get_or_404(destination_id)
    name = dest.name
    for img in dest.images.all():
        delete_image(img.filename, current_app.config["DESTINATION_UPLOAD_FOLDER"])
    delete_image(dest.cover_image, current_app.config["DESTINATION_UPLOAD_FOLDER"])
    db.session.delete(dest)
    db.session.commit()
    log_action(f"Deleted destination {name}", "Destination", destination_id)
    flash(f"Destination '{name}' deleted.", "info")
    return redirect(url_for("admin.destinations"))


@admin_bp.route("/destinations/<int:destination_id>/gallery/upload", methods=["POST"])
@admin_required
def upload_gallery_image(destination_id):
    dest = Destination.query.get_or_404(destination_id)
    form = GalleryUploadForm()
    if form.images.data:
        try:
            filename = save_image(form.images.data, current_app.config["DESTINATION_UPLOAD_FOLDER"])
            if filename:
                db.session.add(Image(destination_id=dest.id, filename=filename, original_name=form.images.data.filename))
                db.session.commit()
                flash("Image uploaded to gallery.", "success")
        except ValueError as e:
            flash(str(e), "danger")
    return redirect(url_for("admin.edit_destination", destination_id=destination_id))


@admin_bp.route("/destinations/gallery/<int:image_id>/delete", methods=["POST"])
@admin_required
def delete_gallery_image(image_id):
    img = Image.query.get_or_404(image_id)
    destination_id = img.destination_id
    delete_image(img.filename, current_app.config["DESTINATION_UPLOAD_FOLDER"])
    db.session.delete(img)
    db.session.commit()
    flash("Gallery image removed.", "info")
    return redirect(url_for("admin.edit_destination", destination_id=destination_id))


def _apply_destination_form(dest, form):
    dest.name = form.name.data.strip()
    dest.city = form.city.data
    dest.country = form.country.data.strip()
    dest.description = form.description.data.strip()
    dest.overview = form.overview.data
    dest.travel_type = form.travel_type.data
    dest.price_per_person = form.price_per_person.data
    dest.duration_days = form.duration_days.data
    dest.best_time_to_visit = form.best_time_to_visit.data
    dest.safety_tips = form.safety_tips.data
    dest.things_to_do = form.things_to_do.data
    dest.hotels = form.hotels.data
    dest.restaurants = form.restaurants.data
    dest.transportation = form.transportation.data
    dest.map_lat = form.map_lat.data
    dest.map_lng = form.map_lng.data
    dest.is_featured = form.is_featured.data
    dest.is_popular = form.is_popular.data

    if form.cover_image.data:
        try:
            filename = save_image(form.cover_image.data, current_app.config["DESTINATION_UPLOAD_FOLDER"])
            if filename:
                dest.cover_image = filename
        except ValueError:
            pass


# --------------------------------------------------------------------------
# MESSAGES
# --------------------------------------------------------------------------
@admin_bp.route("/messages")
@admin_required
def messages():
    page = request.args.get("page", 1, type=int)
    pagination = Message.query.order_by(Message.created_at.desc()).paginate(
        page=page, per_page=current_app.config["ADMIN_ITEMS_PER_PAGE"], error_out=False
    )
    return render_template("admin/messages.html", pagination=pagination, messages=pagination.items)


@admin_bp.route("/messages/<int:message_id>/read", methods=["POST"])
@admin_required
def mark_message_read(message_id):
    msg = Message.query.get_or_404(message_id)
    msg.is_read = True
    db.session.commit()
    return jsonify({"success": True})


@admin_bp.route("/messages/<int:message_id>/reply", methods=["POST"])
@admin_required
def reply_message(message_id):
    msg = Message.query.get_or_404(message_id)
    reply_text = request.form.get("reply", "").strip()
    if reply_text:
        msg.admin_reply = reply_text
        msg.is_read = True
        db.session.commit()
        if msg.user_id:
            create_notification(msg.user_id, "Reply from TravelVista Support", reply_text, category="admin_message")
        log_action(f"Replied to message #{msg.id}", "Message", msg.id)
        flash("Reply sent.", "success")
    return redirect(url_for("admin.messages"))


@admin_bp.route("/messages/<int:message_id>/delete", methods=["POST"])
@admin_required
def delete_message(message_id):
    msg = Message.query.get_or_404(message_id)
    db.session.delete(msg)
    db.session.commit()
    flash("Message deleted.", "info")
    return redirect(url_for("admin.messages"))


# --------------------------------------------------------------------------
# REPORTS
# --------------------------------------------------------------------------
@admin_bp.route("/reports")
@admin_required
def reports():
    total_revenue = db.session.query(func.coalesce(func.sum(Payment.amount), 0)).filter(
        Payment.payment_status == "paid"
    ).scalar()
    bookings_by_status = dict(
        db.session.query(Booking.status, func.count(Booking.id)).group_by(Booking.status).all()
    )
    destinations_by_type = dict(
        db.session.query(Destination.travel_type, func.count(Destination.id)).group_by(Destination.travel_type).all()
    )
    top_rated = Destination.query.order_by(Destination.rating.desc()).limit(5).all()
    monthly_revenue = (
        db.session.query(func.strftime("%Y-%m", Payment.paid_at), func.sum(Payment.amount))
        .filter(Payment.payment_status == "paid")
        .group_by(func.strftime("%Y-%m", Payment.paid_at))
        .order_by(func.strftime("%Y-%m", Payment.paid_at))
        .all()
    )
    max_monthly_revenue = max([amt for _, amt in monthly_revenue], default=0) or 1
    return render_template(
        "admin/reports.html", total_revenue=total_revenue, bookings_by_status=bookings_by_status,
        destinations_by_type=destinations_by_type, top_rated=top_rated, monthly_revenue=monthly_revenue,
        max_monthly_revenue=max_monthly_revenue,
    )


# --------------------------------------------------------------------------
# SETTINGS
# --------------------------------------------------------------------------
@admin_bp.route("/settings", methods=["GET", "POST"])
@admin_required
def settings():
    if request.method == "POST":
        new_password = request.form.get("new_password", "").strip()
        if new_password and len(new_password) >= 8:
            current_user.set_password(new_password)
            db.session.commit()
            log_action("Admin changed their password")
            flash("Admin password updated.", "success")
        else:
            flash("Password must be at least 8 characters.", "danger")
        return redirect(url_for("admin.settings"))

    admins = Admin.query.all()
    return render_template("admin/settings.html", admins=admins)
