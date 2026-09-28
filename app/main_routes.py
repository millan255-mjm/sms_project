from flask import Blueprint, redirect, url_for
from flask_login import current_user

from app.models import ROLE_SUPERADMIN, ROLE_ADMIN, ROLE_LECTURER, ROLE_STUDENT

main_bp = Blueprint("main", __name__)


@main_bp.route("/")
def index():
    if current_user.is_authenticated:
        return redirect(dashboard_url_for(current_user.role))
    return redirect(url_for("auth.login"))


def dashboard_url_for(role):
    return {
        ROLE_SUPERADMIN: "superadmin.dashboard",
        ROLE_ADMIN: "admin.dashboard",
        ROLE_LECTURER: "lecturer.dashboard",
        ROLE_STUDENT: "student.dashboard",
    }.get(role)


def dashboard_redirect(role):
    from flask import redirect, url_for
    return redirect(url_for(dashboard_url_for(role)))
