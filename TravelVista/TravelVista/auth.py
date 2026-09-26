"""
auth.py
Authentication blueprint: registration, login, logout, forgot/reset
password, remember-me, and session management for regular Users.
Admin authentication lives in admin.py (separate login as required).
"""

from datetime import datetime, timedelta

from flask import Blueprint, render_template, redirect, url_for, flash, request, current_app
from flask_login import login_user, logout_user, login_required, current_user

from extensions import db
from models import User
from forms import RegisterForm, LoginForm, ForgotPasswordForm, ResetPasswordForm
from utils import generate_reset_token, create_notification

auth_bp = Blueprint("auth", __name__)


@auth_bp.route("/register", methods=["GET", "POST"])
def register():
    if current_user.is_authenticated:
        return redirect(url_for("main.dashboard"))

    form = RegisterForm()
    if form.validate_on_submit():
        user = User(
            username=form.username.data.strip(),
            email=form.email.data.strip().lower(),
            full_name=form.full_name.data.strip(),
        )
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()

        create_notification(
            user.id, "Welcome to TravelVista!",
            "Your account has been created. Start exploring destinations and plan your first trip.",
            category="general",
        )

        flash("Account created successfully! Please log in.", "success")
        return redirect(url_for("auth.login"))

    return render_template("register.html", form=form)


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("main.dashboard"))

    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data.strip().lower()).first()
        if user and user.check_password(form.password.data):
            if not user.is_active_account:
                flash("This account has been deactivated. Contact support.", "danger")
                return redirect(url_for("auth.login"))
            login_user(user, remember=form.remember.data)
            next_page = request.args.get("next")
            flash(f"Welcome back, {user.full_name or user.username}!", "success")
            return redirect(next_page or url_for("main.dashboard"))
        flash("Invalid email or password.", "danger")

    return render_template("login.html", form=form)


@auth_bp.route("/logout")
@login_required
def logout():
    logout_user()
    flash("You have been logged out.", "info")
    return redirect(url_for("main.index"))


@auth_bp.route("/forgot-password", methods=["GET", "POST"])
def forgot_password():
    form = ForgotPasswordForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data.strip().lower()).first()
        if user:
            token = generate_reset_token()
            user.reset_token = token
            user.reset_token_expiry = datetime.utcnow() + timedelta(hours=1)
            db.session.commit()

            reset_url = url_for("auth.reset_password", token=token, _external=True)
            if current_app.config["MAIL_BACKEND"] == "console":
                # Development stand-in for a real mail provider: log the link.
                current_app.logger.info(f"[PASSWORD RESET] {user.email} -> {reset_url}")

        # Always show the same message (don't leak which emails exist)
        flash("If that email is registered, a password reset link has been sent.", "info")
        return redirect(url_for("auth.login"))

    return render_template("forgot_password.html", form=form)


@auth_bp.route("/reset-password/<token>", methods=["GET", "POST"])
def reset_password(token):
    user = User.query.filter_by(reset_token=token).first()
    if not user or not user.reset_token_expiry or user.reset_token_expiry < datetime.utcnow():
        flash("This password reset link is invalid or has expired.", "danger")
        return redirect(url_for("auth.forgot_password"))

    form = ResetPasswordForm()
    if form.validate_on_submit():
        user.set_password(form.password.data)
        user.reset_token = None
        user.reset_token_expiry = None
        db.session.commit()
        create_notification(user.id, "Password Changed", "Your password was reset successfully.", category="password_changed")
        flash("Your password has been reset. Please log in.", "success")
        return redirect(url_for("auth.login"))

    return render_template("reset_password.html", form=form, token=token)
