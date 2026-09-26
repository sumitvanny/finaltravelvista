"""
app.py
Application factory. Run with `python app.py` for local development,
or `gunicorn "app:create_app()"` in production.
"""

import os
from flask import Flask, render_template
from dotenv import load_dotenv

load_dotenv()

from config import config_map
from extensions import db, login_manager, csrf, migrate
from models import User, Admin


def create_app(config_name=None):
    config_name = config_name or os.environ.get("FLASK_ENV", "development")
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_object(config_map.get(config_name, config_map["default"]))

    os.makedirs(app.instance_path, exist_ok=True)
    os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)
    os.makedirs(app.config["DESTINATION_UPLOAD_FOLDER"], exist_ok=True)
    os.makedirs(app.config["PROFILE_UPLOAD_FOLDER"], exist_ok=True)

    # --- Init extensions ---
    db.init_app(app)
    login_manager.init_app(app)
    csrf.init_app(app)
    migrate.init_app(app, db)

    # --- Blueprints ---
    from auth import auth_bp
    from routes import main_bp
    from admin import admin_bp

    app.register_blueprint(main_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(admin_bp)

    # --- Flask-Login user loader ---
    # Users and Admins share the login session but are distinguished by an
    # "admin-" prefix on the loaded id (see Admin.get_id()).
    @login_manager.user_loader
    def load_user(user_id):
        if isinstance(user_id, str) and user_id.startswith("admin-"):
            return Admin.query.get(int(user_id.split("-", 1)[1]))
        return User.query.get(int(user_id))

    # --- Template context ---
    @app.context_processor
    def inject_globals():
        from datetime import datetime, timezone
        return {"app_name": app.config["APP_NAME"], "current_year": datetime.now(timezone.utc).year}

    # --- Error handlers ---
    @app.errorhandler(404)
    def not_found(e):
        return render_template("errors/404.html"), 404

    @app.errorhandler(403)
    def forbidden(e):
        return render_template("errors/403.html"), 403

    @app.errorhandler(500)
    def server_error(e):
        db.session.rollback()
        return render_template("errors/500.html"), 500

    @app.errorhandler(413)
    def file_too_large(e):
        return render_template("errors/413.html"), 413

    return app


app = create_app()

if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    # use_reloader=False: the reloader's file-watcher would otherwise trigger
    # on every SQLite write inside instance/, restarting the server mid-request.
    app.run(debug=app.config.get("DEBUG", True), use_reloader=False,
            host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
