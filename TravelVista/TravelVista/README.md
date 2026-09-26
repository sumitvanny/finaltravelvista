# TravelVista

A full-stack, database-backed AI travel planning platform built with Flask.
Users can search destinations, generate AI-assisted trip itineraries, book
trips, leave reviews, manage a wishlist, and track everything from a
personal dashboard. Admins get a separate login and a full control panel
for users, bookings, destinations, messages, and analytics.

---

## Features

- **Auth**: registration, login, logout, remember-me, forgot/reset password, CSRF protection
- **Profile**: picture upload, edit details, change password, delete account
- **Search & Destinations**: filterable search, rich destination pages, galleries, reviews
- **AI Trip Planner**: rule-based itinerary generator (day-by-day plan, packing list, budget breakdown) — structured so a real LLM/API call can be dropped in later (see `utils.generate_trip_plan`)
- **Bookings**: hotel selection, travel dates, mock payment, confirmation, cancellation, history
- **Wishlist, Reviews, Notifications**
- **Admin Panel**: separate login, dashboard analytics, user/booking/destination CRUD, image uploads, contact message inbox, reports, audit log

---

## Tech Stack

Python 3 / Flask / SQLAlchemy / Flask-Login / Flask-WTF / Flask-Migrate /
SQLite (dev) — swappable to PostgreSQL or MySQL / Vanilla HTML, CSS, JS
(no frontend framework) / Gunicorn for production.

---

## 1. Installation

```bash
git clone <your-repo-url> travelvista
cd travelvista
```

### Create a virtual environment

```bash
python3 -m venv venv

# macOS / Linux
source venv/bin/activate

# Windows
venv\Scripts\activate
```

### Install dependencies

```bash
pip install -r requirements.txt
```

---

## 2. Environment Configuration

Copy the provided `.env` (already included with sensible dev defaults) and
adjust as needed:

```
FLASK_ENV=development
SECRET_KEY=change-this-to-a-long-random-string-in-production
DATABASE_URL=                     # blank = local SQLite at instance/database.db
SESSION_COOKIE_SECURE=false       # set true when serving over HTTPS
MAIL_BACKEND=console              # "console" logs password-reset links to the terminal
```

**Never commit a real `SECRET_KEY` or mail credentials to version control.**

---

## 3. Database Setup

The app uses Flask-SQLAlchemy models (`models.py`) as the source of truth.
`sql/schema.sql` and `sql/sample_data.sql` are provided for reference/manual
inspection, but the recommended path is:

```bash
python seed.py
```

This will:
1. Create all tables (`db.create_all()`)
2. Create a default admin account:
   - **Username:** `admin`
   - **Password:** `Admin@12345`
3. Seed 8 sample destinations across 8 travel styles

> Change the default admin password immediately after first login via
> **Admin Panel → Settings**.

### Using Flask-Migrate instead (optional, for schema evolution)

```bash
flask --app app db init
flask --app app db migrate -m "initial schema"
flask --app app db upgrade
```

---

## 4. Run the App

```bash
python app.py
```

Visit **http://127.0.0.1:5000**

- User signup: `/register`
- Admin login: `/admin/login`

---

## 5. Project Structure

```
TravelVista/
├── app.py                # Application factory + entry point
├── config.py             # Environment-based configuration
├── extensions.py         # Shared Flask extension instances
├── models.py              # SQLAlchemy models (12 tables)
├── forms.py               # Flask-WTF forms
├── auth.py                # User auth blueprint
├── routes.py               # Main user-facing blueprint
├── admin.py                # Admin blueprint (separate auth + CRUD)
├── utils.py                 # Helpers: uploads, tokens, AI planner logic
├── seed.py                   # DB seeding script
├── requirements.txt
├── .env / .gitignore
├── sql/
│   ├── schema.sql            # Reference schema (SQLite dialect)
│   └── sample_data.sql       # Reference seed data
├── static/
│   ├── css/                  # style.css (design system) + per-page CSS
│   ├── js/                   # main.js, dashboard.js, planner.js, booking.js, animations.js
│   └── images/uploads/       # destination & profile image uploads
├── templates/
│   ├── base.html, index.html, login.html, ...
│   ├── admin/                # admin panel templates
│   └── partials/             # reusable includes (cards, rows)
└── instance/
    └── database.db           # SQLite database (created on first run)
```

---

## 6. Deployment

### Gunicorn (Linux/production)

```bash
pip install gunicorn
gunicorn "app:create_app()" --bind 0.0.0.0:8000 --workers 4
```

### Checklist before going live

- [ ] Set a strong, random `SECRET_KEY`
- [ ] Point `DATABASE_URL` at PostgreSQL/MySQL, not SQLite
- [ ] Set `FLASK_ENV=production` and `SESSION_COOKIE_SECURE=true` (requires HTTPS)
- [ ] Configure a real `MAIL_BACKEND` (SMTP) so password-reset emails actually send
- [ ] Put the app behind a reverse proxy (nginx/Caddy) terminating TLS
- [ ] Change the default admin password
- [ ] Set up regular database backups

---

## 7. Extending the AI Planner

The itinerary generator lives entirely in `utils.generate_trip_plan()`. It
currently uses rule-based logic (no external API calls) so the app runs
fully offline. To connect a real model:

1. Keep the function signature and return shape identical:
   `{"destination", "days", "packing_list", "tips", "estimated_budget"}`
2. Replace the body with a call to your model/API of choice.
3. Everything downstream (routes, templates, Trip storage) needs no changes.

---

## 8. Troubleshooting

| Issue | Fix |
|---|---|
| `unable to open database file` | Make sure `instance/` exists and `DATABASE_URL` isn't a relative path pointed at the wrong working directory. Leave `DATABASE_URL` blank in `.env` to use the safe default. |
| Server keeps restarting mid-request in dev mode | This was caused by Flask's reloader watching SQLite writes in `instance/`. `app.py` already runs with `use_reloader=False` for this reason. |
| CSRF token errors on a form | Every POST form must include `{{ form.hidden_tag() }}` (WTForms) or a manual `<input type="hidden" name="csrf_token" value="{{ csrf_token() }}">` for raw HTML forms. |
| Uploaded images not showing | Confirm `static/images/uploads/destinations` and `.../profiles` are writable and under the 8 MB limit (`MAX_CONTENT_LENGTH`). |
| `pip install` conflicts with system Pillow/PyJWT | Use a virtual environment (see step 1) instead of installing system-wide. |

---

## License

Provided as a foundation for your own product — adapt freely.
