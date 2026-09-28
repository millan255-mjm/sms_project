from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager

db = SQLAlchemy()
login_manager = LoginManager()
login_manager.login_view = "auth.login"
login_manager.login_message = "Please log in to continue."
login_manager.login_message_category = "warning"


def create_app():
    app = Flask(__name__)
    app.config.from_object("config.Config")

    db.init_app(app)
    login_manager.init_app(app)

    from app.models import User

    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    # Blueprints
    from app.auth.routes import auth_bp
    from app.superadmin.routes import superadmin_bp
    from app.admin.routes import admin_bp
    from app.lecturer.routes import lecturer_bp
    from app.student.routes import student_bp
    from app.main_routes import main_bp

    app.register_blueprint(main_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(superadmin_bp, url_prefix="/superadmin")
    app.register_blueprint(admin_bp, url_prefix="/admin")
    app.register_blueprint(lecturer_bp, url_prefix="/lecturer")
    app.register_blueprint(student_bp, url_prefix="/student")

    with app.app_context():
        db.create_all()
        _auto_seed(app)

    @app.context_processor
    def inject_globals():
        from datetime import datetime
        return {"current_year": datetime.utcnow().year}

    return app


def _auto_seed(app):
    """Create a default Super Admin account on first boot so the system
    is usable immediately after deployment, without a manual shell step."""
    from app.models import User, ROLE_SUPERADMIN

    if User.query.filter_by(role=ROLE_SUPERADMIN).first():
        return

    username = app.config["DEFAULT_SUPERADMIN_USERNAME"]
    password = app.config["DEFAULT_SUPERADMIN_PASSWORD"]

    admin = User(
        full_name="System Super Administrator",
        username=username,
        email="superadmin@sms.local",
        role=ROLE_SUPERADMIN,
    )
    admin.set_password(password)
    db.session.add(admin)
    db.session.commit()
    app.logger.info(f"Seeded default super admin -> username: {username} / password: {password}")
