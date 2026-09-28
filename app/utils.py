from functools import wraps
from flask import abort, request
from flask_login import current_user

from app import db
from app.models import AuditLog


def role_required(*roles):
    """Restrict a view to one or more roles, e.g. @role_required('admin', 'superadmin')"""
    def decorator(view_func):
        @wraps(view_func)
        def wrapped(*args, **kwargs):
            if not current_user.is_authenticated:
                abort(401)
            if current_user.role not in roles:
                abort(403)
            return view_func(*args, **kwargs)
        return wrapped
    return decorator


def log_action(action, details=""):
    """Write an entry to the audit log. Safe to call even for anonymous users."""
    try:
        user = current_user if current_user.is_authenticated else None
        entry = AuditLog(
            user_id=user.id if user else None,
            username=user.username if user else "anonymous",
            role=user.role if user else None,
            action=action,
            details=details,
            ip_address=request.remote_addr,
        )
        db.session.add(entry)
        db.session.commit()
    except Exception:
        db.session.rollback()


def grade_badge_class(grade):
    return {
        "A": "badge-success",
        "B": "badge-info",
        "C": "badge-warning",
        "D": "badge-warning",
        "F": "badge-danger",
    }.get(grade, "badge-muted")
