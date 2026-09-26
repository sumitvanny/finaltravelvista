"""
extensions.py
All Flask extensions are instantiated here (not bound to an app yet) so
that models.py, routes.py, and app.py can all import them without
creating circular-import problems. app.py calls .init_app(app) on each.
"""

from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_wtf import CSRFProtect
from flask_migrate import Migrate

db = SQLAlchemy()
login_manager = LoginManager()
csrf = CSRFProtect()
migrate = Migrate()

login_manager.login_view = "auth.login"
login_manager.login_message = "Please log in to access this page."
login_manager.login_message_category = "info"
