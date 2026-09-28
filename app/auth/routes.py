from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_user, logout_user, login_required, current_user

from app.models import User
from app.utils import log_action
from app.main_routes import dashboard_url_for

auth_bp = Blueprint("auth", __name__)


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for(dashboard_url_for(current_user.role)))

    if request.method == "POST":
        role = request.form.get("role", "student")
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")

        user = User.query.filter_by(username=username, role=role).first()

        if not user or not user.check_password(password):
            flash("Invalid username or password for the selected role.", "danger")
            return render_template("login.html", active_role=role, username=username)

        if not user.is_active_account:
            flash("This account has been deactivated. Contact the administrator.", "danger")
            return render_template("login.html", active_role=role, username=username)

        login_user(user)
        log_action("login", f"{user.role} '{user.username}' logged in")
        flash(f"Welcome back, {user.full_name}!", "success")
        return redirect(url_for(dashboard_url_for(user.role)))

    return render_template("login.html", active_role="student", username="")


@auth_bp.route("/logout")
@login_required
def logout():
    log_action("logout", f"{current_user.role} '{current_user.username}' logged out")
    logout_user()
    flash("You have been logged out.", "info")
    return redirect(url_for("auth.login"))
