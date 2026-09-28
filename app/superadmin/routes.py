import os
from flask import (Blueprint, render_template, request, redirect, url_for,
                    flash, send_file, current_app)
from flask_login import login_required, current_user

from app import db
from app.models import (User, Student, Lecturer, Course, Department, ClassGroup,
                         Enrollment, Attendance, Mark, AuditLog, SystemSetting,
                         ROLE_ADMIN, ROLE_SUPERADMIN, ROLE_LECTURER, ROLE_STUDENT)
from app.utils import role_required, log_action

superadmin_bp = Blueprint("superadmin", __name__, template_folder="../templates/superadmin")


@superadmin_bp.route("/dashboard")
@login_required
@role_required(ROLE_SUPERADMIN)
def dashboard():
    stats = {
        "admins": User.query.filter_by(role=ROLE_ADMIN).count(),
        "lecturers": User.query.filter_by(role=ROLE_LECTURER).count(),
        "students": User.query.filter_by(role=ROLE_STUDENT).count(),
        "courses": Course.query.count(),
        "departments": Department.query.count(),
    }
    recent_logs = AuditLog.query.order_by(AuditLog.timestamp.desc()).limit(8).all()
    return render_template("superadmin/dashboard.html", stats=stats, recent_logs=recent_logs)


# ---------------- Manage Admins ----------------
@superadmin_bp.route("/admins")
@login_required
@role_required(ROLE_SUPERADMIN)
def admins():
    admin_users = User.query.filter_by(role=ROLE_ADMIN).order_by(User.full_name).all()
    rows = [{
        "full_name": u.full_name, "username": u.username, "email": u.email or "—",
        "status": "Active" if u.is_active_account else "Disabled",
        "edit_url": url_for("superadmin.admin_edit", user_id=u.id),
        "delete_url": url_for("superadmin.admin_delete", user_id=u.id),
    } for u in admin_users]
    return render_template("generic_list.html", title="Manage Admins",
                            subtitle="Create and manage Admin accounts",
                            add_url=url_for("superadmin.admin_add"), add_label="Add Admin",
                            columns=[("full_name", "Full Name"), ("username", "Username"),
                                     ("email", "Email"), ("status", "Status")],
                            rows=rows)


@superadmin_bp.route("/admins/add", methods=["GET", "POST"])
@login_required
@role_required(ROLE_SUPERADMIN)
def admin_add():
    if request.method == "POST":
        username = request.form["username"].strip()
        if User.query.filter_by(username=username).first():
            flash("Username already exists.", "danger")
            return redirect(url_for("superadmin.admin_add"))
        u = User(full_name=request.form["full_name"], username=username,
                  email=request.form.get("email"), role=ROLE_ADMIN)
        u.set_password(request.form["password"])
        db.session.add(u)
        db.session.commit()
        log_action("create_admin", f"Created admin '{username}'")
        flash("Admin account created.", "success")
        return redirect(url_for("superadmin.admins"))

    fields = _user_fields()
    return render_template("generic_form.html", title="Add Admin", fields=fields,
                            cancel_url=url_for("superadmin.admins"))


@superadmin_bp.route("/admins/<int:user_id>/edit", methods=["GET", "POST"])
@login_required
@role_required(ROLE_SUPERADMIN)
def admin_edit(user_id):
    u = User.query.get_or_404(user_id)
    if request.method == "POST":
        u.full_name = request.form["full_name"]
        u.email = request.form.get("email")
        if request.form.get("password"):
            u.set_password(request.form["password"])
        db.session.commit()
        log_action("edit_admin", f"Edited admin '{u.username}'")
        flash("Admin updated.", "success")
        return redirect(url_for("superadmin.admins"))

    fields = _user_fields(u, editing=True)
    return render_template("generic_form.html", title=f"Edit Admin - {u.full_name}",
                            fields=fields, cancel_url=url_for("superadmin.admins"))


@superadmin_bp.route("/admins/<int:user_id>/delete", methods=["POST"])
@login_required
@role_required(ROLE_SUPERADMIN)
def admin_delete(user_id):
    u = User.query.get_or_404(user_id)
    db.session.delete(u)
    db.session.commit()
    log_action("delete_admin", f"Deleted admin '{u.username}'")
    flash("Admin removed.", "info")
    return redirect(url_for("superadmin.admins"))


def _user_fields(u=None, editing=False):
    fields = [
        {"name": "full_name", "label": "Full Name", "type": "text", "required": True, "value": u.full_name if u else ""},
        {"name": "email", "label": "Email", "type": "email", "value": u.email if u else ""},
    ]
    if not editing:
        fields.append({"name": "username", "label": "Username", "type": "text", "required": True})
        fields.append({"name": "password", "label": "Password", "type": "password", "required": True})
    else:
        fields.append({"name": "password", "label": "New Password", "type": "password",
                        "help": "Leave blank to keep the current password"})
    return fields


# ---------------- Manage All Users ----------------
@superadmin_bp.route("/users")
@login_required
@role_required(ROLE_SUPERADMIN)
def users():
    all_users = User.query.order_by(User.role, User.full_name).all()
    rows = [{
        "full_name": u.full_name, "username": u.username, "role": u.role_label(),
        "status": "Active" if u.is_active_account else "Disabled",
        "extra_url": url_for("superadmin.toggle_user", user_id=u.id),
        "extra_label": "Disable" if u.is_active_account else "Enable",
    } for u in all_users]
    return render_template("superadmin/users.html", rows=rows)


@superadmin_bp.route("/users/<int:user_id>/toggle", methods=["GET"])
@login_required
@role_required(ROLE_SUPERADMIN)
def toggle_user(user_id):
    u = User.query.get_or_404(user_id)
    if u.id == current_user.id:
        flash("You cannot disable your own account.", "warning")
        return redirect(url_for("superadmin.users"))
    u.is_active_account = not u.is_active_account
    db.session.commit()
    log_action("toggle_user", f"Set '{u.username}' active={u.is_active_account}")
    flash(f"Account '{u.username}' {'enabled' if u.is_active_account else 'disabled'}.", "success")
    return redirect(url_for("superadmin.users"))


# ---------------- System Settings ----------------
DEFAULT_SETTINGS = {
    "institution_name": "National Institute of Technology",
    "academic_year": "2025/2026",
    "current_semester": "1st Semester",
    "allow_self_registration": "off",
}


@superadmin_bp.route("/settings", methods=["GET", "POST"])
@login_required
@role_required(ROLE_SUPERADMIN)
def settings():
    for key, default in DEFAULT_SETTINGS.items():
        if not SystemSetting.query.filter_by(key=key).first():
            db.session.add(SystemSetting(key=key, value=default))
    db.session.commit()

    if request.method == "POST":
        for key in DEFAULT_SETTINGS.keys():
            setting = SystemSetting.query.filter_by(key=key).first()
            if key == "allow_self_registration":
                setting.value = "on" if request.form.get(key) else "off"
            else:
                setting.value = request.form.get(key, setting.value)
        db.session.commit()
        log_action("update_settings", "System settings updated")
        flash("System settings saved.", "success")
        return redirect(url_for("superadmin.settings"))

    current_settings = {s.key: s.value for s in SystemSetting.query.all()}
    return render_template("superadmin/settings.html", settings=current_settings)


# ---------------- Database Backup ----------------
@superadmin_bp.route("/backup")
@login_required
@role_required(ROLE_SUPERADMIN)
def backup():
    db_uri = current_app.config["SQLALCHEMY_DATABASE_URI"]
    is_sqlite = db_uri.startswith("sqlite")
    db_path = db_uri.replace("sqlite:///", "") if is_sqlite else None
    return render_template("superadmin/backup.html", is_sqlite=is_sqlite, db_path=db_path)


@superadmin_bp.route("/backup/download")
@login_required
@role_required(ROLE_SUPERADMIN)
def backup_download():
    db_uri = current_app.config["SQLALCHEMY_DATABASE_URI"]
    if not db_uri.startswith("sqlite"):
        flash("Direct file backup is only available for SQLite. Use your database provider's backup tools (e.g. Railway PostgreSQL backups) instead.", "warning")
        return redirect(url_for("superadmin.backup"))
    db_path = db_uri.replace("sqlite:///", "")
    if not os.path.exists(db_path):
        flash("Database file not found.", "danger")
        return redirect(url_for("superadmin.backup"))
    log_action("backup_download", "Downloaded database backup")
    return send_file(db_path, as_attachment=True, download_name="sms_backup.db")


# ---------------- Reports ----------------
@superadmin_bp.route("/reports")
@login_required
@role_required(ROLE_SUPERADMIN)
def reports():
    dept_stats = []
    for dept in Department.query.all():
        dept_stats.append({
            "name": dept.name,
            "students": ClassGroup.query.filter_by(department_id=dept.id).join(Student).count() if False else sum(len(c.students) for c in dept.classes),
            "courses": len(dept.courses),
        })
    totals = {
        "students": Student.query.count(),
        "lecturers": Lecturer.query.count(),
        "courses": Course.query.count(),
        "enrollments": Enrollment.query.count(),
        "attendance_records": Attendance.query.count(),
        "marks_recorded": Mark.query.count(),
    }
    return render_template("superadmin/reports.html", dept_stats=dept_stats, totals=totals)


# ---------------- Security & Permissions ----------------
ROLE_PERMISSIONS = [
    ("Super Admin", ["Full system access", "Manage Admins", "System Settings", "Database Backup", "Audit Logs", "Security & Permissions"]),
    ("Admin", ["Manage Students", "Manage Lecturers", "Manage Courses/Classes", "Enrollment", "Timetable", "Announcements", "Reports"]),
    ("Lecturer", ["View assigned Courses", "Record Attendance", "Enter Marks", "Manage Assignments", "View Student Performance"]),
    ("Student", ["View Profile", "View Courses", "View Results", "View Attendance", "Submit Assignments"]),
]


@superadmin_bp.route("/security")
@login_required
@role_required(ROLE_SUPERADMIN)
def security():
    return render_template("superadmin/security.html", role_permissions=ROLE_PERMISSIONS)


# ---------------- Audit Logs ----------------
@superadmin_bp.route("/audit-logs")
@login_required
@role_required(ROLE_SUPERADMIN)
def audit_logs():
    role_filter = request.args.get("role", "")
    query = AuditLog.query
    if role_filter:
        query = query.filter_by(role=role_filter)
    logs = query.order_by(AuditLog.timestamp.desc()).limit(300).all()
    return render_template("superadmin/audit_logs.html", logs=logs, role_filter=role_filter)
