import os

BASE_DIR = os.path.abspath(os.path.dirname(__file__))


class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY", "change-this-secret-key-in-production")

    db_url = os.environ.get("DATABASE_URL", "")
    if db_url.startswith("postgres://"):
        # Railway / Heroku style URLs use the old "postgres://" scheme;
        # SQLAlchemy 2.x requires "postgresql://"
        db_url = db_url.replace("postgres://", "postgresql://", 1)

    if not db_url:
        db_url = "sqlite:///" + os.path.join(BASE_DIR, "instance", "sms.db")

    SQLALCHEMY_DATABASE_URI = db_url
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Default super admin account created automatically on first run
    DEFAULT_SUPERADMIN_USERNAME = os.environ.get("DEFAULT_SUPERADMIN_USERNAME", "superadmin")
    DEFAULT_SUPERADMIN_PASSWORD = os.environ.get("DEFAULT_SUPERADMIN_PASSWORD", "Admin@123")
