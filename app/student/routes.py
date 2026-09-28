from datetime import datetime
from flask import Blueprint, render_template, request, redirect, url_for, flash, abort
from flask_login import login_required, current_user

from app import db
from app.models import Mark, Attendance, Assignment, Submission, Announcement, ROLE_STUDENT
from app.utils import role_required, log_action

student_bp = Blueprint("student", __name__, template_folder="../templates/student")


def _current_student():
    return current_user.student_profile


@student_bp.route("/dashboard")
@login_required
@role_required(ROLE_STUDENT)
def dashboard():
    s = _current_student()
    course_count = len(s.enrollments) if s else 0
    marks = Mark.query.filter_by(student_id=s.id).all() if s else []
    avg_score = round(sum(m.total for m in marks) / len(marks), 1) if marks else 0
    attendance_records = Attendance.query.filter_by(student_id=s.id).all() if s else []
    present_count = sum(1 for a in attendance_records if a.status == "present")
    attendance_rate = round((present_count / len(attendance_records)) * 100, 1) if attendance_records else 100
    announcements = Announcement.query.filter(Announcement.target_role.in_(["all", "student"])).order_by(Announcement.created_at.desc()).limit(5).all()
    return render_template("student/dashboard.html", course_count=course_count, avg_score=avg_score,
                            attendance_rate=attendance_rate, announcements=announcements)


@student_bp.route("/profile", methods=["GET", "POST"])
@login_required
@role_required(ROLE_STUDENT)
def profile():
    s = _current_student()
    if request.method == "POST":
        s.phone = request.form.get("phone")
        s.address = request.form.get("address")
        if request.form.get("password"):
            current_user.set_password(request.form["password"])
        db.session.commit()
        log_action("update_profile", "Student updated their profile")
        flash("Profile updated.", "success")
        return redirect(url_for("student.profile"))
    return render_template("student/profile.html", student=s)


@student_bp.route("/courses")
@login_required
@role_required(ROLE_STUDENT)
def courses():
    s = _current_student()
    enrollments = s.enrollments if s else []
    return render_template("student/courses.html", enrollments=enrollments)


@student_bp.route("/results")
@login_required
@role_required(ROLE_STUDENT)
def results():
    s = _current_student()
    marks = Mark.query.filter_by(student_id=s.id).all() if s else []
    return render_template("student/results.html", marks=marks)


@student_bp.route("/attendance")
@login_required
@role_required(ROLE_STUDENT)
def attendance():
    s = _current_student()
    records = Attendance.query.filter_by(student_id=s.id).order_by(Attendance.date.desc()).all() if s else []
    total = len(records)
    present = sum(1 for r in records if r.status == "present")
    rate = round((present / total) * 100, 1) if total else 100
    return render_template("student/attendance.html", records=records, rate=rate, total=total)


@student_bp.route("/assignments", methods=["GET"])
@login_required
@role_required(ROLE_STUDENT)
def assignments():
    s = _current_student()
    course_ids = [e.course_id for e in s.enrollments] if s else []
    assignment_list = Assignment.query.filter(Assignment.course_id.in_(course_ids)).order_by(Assignment.due_date).all()
    my_submissions = {sub.assignment_id: sub for sub in Submission.query.filter_by(student_id=s.id).all()} if s else {}
    return render_template("student/assignments.html", assignments=assignment_list, submissions=my_submissions)


@student_bp.route("/assignments/<int:assignment_id>/submit", methods=["GET", "POST"])
@login_required
@role_required(ROLE_STUDENT)
def assignment_submit(assignment_id):
    s = _current_student()
    a = Assignment.query.get_or_404(assignment_id)
    enrolled_course_ids = [e.course_id for e in s.enrollments]
    if a.course_id not in enrolled_course_ids:
        abort(403)

    existing = Submission.query.filter_by(assignment_id=assignment_id, student_id=s.id).first()

    if request.method == "POST":
        if existing:
            existing.content = request.form["content"]
            existing.submitted_at = datetime.utcnow()
        else:
            db.session.add(Submission(assignment_id=assignment_id, student_id=s.id,
                                       content=request.form["content"]))
        db.session.commit()
        log_action("submit_assignment", f"Submitted assignment '{a.title}'")
        flash("Assignment submitted.", "success")
        return redirect(url_for("student.assignments"))

    fields = [{"name": "content", "label": "Your Answer / Link", "type": "textarea", "required": True,
               "value": existing.content if existing else "",
               "help": "Paste your text answer, or a link to your work (e.g. Google Drive, GitHub)."}]
    return render_template("generic_form.html", title=f"Submit: {a.title}", fields=fields,
                            cancel_url=url_for("student.assignments"))
