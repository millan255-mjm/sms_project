from datetime import date, datetime
from flask import Blueprint, render_template, request, redirect, url_for, flash, abort
from flask_login import login_required, current_user

from app import db
from app.models import (Course, Enrollment, Attendance, Mark, Assignment, Submission,
                         ROLE_LECTURER)
from app.utils import role_required, log_action

lecturer_bp = Blueprint("lecturer", __name__, template_folder="../templates/lecturer")


def _current_lecturer():
    return current_user.lecturer_profile


@lecturer_bp.route("/dashboard")
@login_required
@role_required(ROLE_LECTURER)
def dashboard():
    lect = _current_lecturer()
    courses = lect.courses if lect else []
    total_students = sum(len(c.enrollments) for c in courses)
    pending_grading = 0
    for c in courses:
        for a in c.assignments:
            pending_grading += sum(1 for s in a.submissions if s.score is None)
    return render_template("lecturer/dashboard.html", courses=courses,
                            total_students=total_students, pending_grading=pending_grading)


@lecturer_bp.route("/my-courses")
@login_required
@role_required(ROLE_LECTURER)
def my_courses():
    lect = _current_lecturer()
    courses = lect.courses if lect else []
    return render_template("lecturer/my_courses.html", courses=courses)


@lecturer_bp.route("/my-students")
@login_required
@role_required(ROLE_LECTURER)
def my_students():
    lect = _current_lecturer()
    course_id = request.args.get("course_id", type=int)
    courses = lect.courses if lect else []
    students = []
    if course_id:
        course = Course.query.get_or_404(course_id)
        if course.lecturer_id != lect.id:
            abort(403)
        students = [e.student for e in course.enrollments]
    return render_template("lecturer/my_students.html", courses=courses, students=students, selected_course=course_id)


# ==================== ATTENDANCE ====================
@lecturer_bp.route("/attendance", methods=["GET", "POST"])
@login_required
@role_required(ROLE_LECTURER)
def attendance():
    lect = _current_lecturer()
    courses = lect.courses if lect else []
    course_id = request.values.get("course_id", type=int)
    att_date_str = request.values.get("att_date") or date.today().isoformat()
    att_date = datetime.strptime(att_date_str, "%Y-%m-%d").date()

    course = None
    enrollments = []
    if course_id:
        course = Course.query.get_or_404(course_id)
        if course.lecturer_id != lect.id:
            abort(403)
        enrollments = course.enrollments

    if request.method == "POST" and course:
        for e in enrollments:
            status = request.form.get(f"status_{e.student_id}", "present")
            record = Attendance.query.filter_by(student_id=e.student_id, course_id=course.id, date=att_date).first()
            if record:
                record.status = status
            else:
                db.session.add(Attendance(student_id=e.student_id, course_id=course.id, date=att_date, status=status))
        db.session.commit()
        log_action("record_attendance", f"Recorded attendance for course '{course.code}' on {att_date}")
        flash("Attendance saved.", "success")
        return redirect(url_for("lecturer.attendance", course_id=course.id, att_date=att_date_str))

    existing = {}
    if course:
        for a in Attendance.query.filter_by(course_id=course.id, date=att_date).all():
            existing[a.student_id] = a.status

    return render_template("lecturer/attendance.html", courses=courses, course=course,
                            enrollments=enrollments, att_date=att_date_str, existing=existing)


# ==================== MARKS ====================
@lecturer_bp.route("/marks", methods=["GET", "POST"])
@login_required
@role_required(ROLE_LECTURER)
def marks():
    lect = _current_lecturer()
    courses = lect.courses if lect else []
    course_id = request.values.get("course_id", type=int)
    course = None
    enrollments = []
    if course_id:
        course = Course.query.get_or_404(course_id)
        if course.lecturer_id != lect.id:
            abort(403)
        enrollments = course.enrollments

    if request.method == "POST" and course:
        for e in enrollments:
            ca = request.form.get(f"ca_{e.student_id}", 0) or 0
            exam = request.form.get(f"exam_{e.student_id}", 0) or 0
            record = Mark.query.filter_by(student_id=e.student_id, course_id=course.id).first()
            if not record:
                record = Mark(student_id=e.student_id, course_id=course.id)
                db.session.add(record)
            record.ca_score = float(ca)
            record.exam_score = float(exam)
        db.session.commit()
        log_action("enter_marks", f"Entered marks for course '{course.code}'")
        flash("Marks saved.", "success")
        return redirect(url_for("lecturer.marks", course_id=course.id))

    existing = {}
    if course:
        for m in Mark.query.filter_by(course_id=course.id).all():
            existing[m.student_id] = m

    return render_template("lecturer/marks.html", courses=courses, course=course,
                            enrollments=enrollments, existing=existing)


# ==================== ASSIGNMENTS ====================
@lecturer_bp.route("/assignments")
@login_required
@role_required(ROLE_LECTURER)
def assignments():
    lect = _current_lecturer()
    course_ids = [c.id for c in lect.courses] if lect else []
    assignment_list = Assignment.query.filter(Assignment.course_id.in_(course_ids)).order_by(Assignment.due_date).all()
    rows = [{"title": a.title, "course": a.course.code, "due": a.due_date.strftime("%Y-%m-%d") if a.due_date else "—",
             "submissions": len(a.submissions),
             "extra_url": url_for("lecturer.assignment_submissions", assignment_id=a.id), "extra_label": "Submissions",
             "delete_url": url_for("lecturer.assignment_delete", assignment_id=a.id)} for a in assignment_list]
    return render_template("generic_list.html", title="Manage Assignments",
                            subtitle="Create assignments for your courses",
                            add_url=url_for("lecturer.assignment_add"), add_label="New Assignment",
                            columns=[("title", "Title"), ("course", "Course"), ("due", "Due Date"), ("submissions", "Submissions")],
                            rows=rows)


@lecturer_bp.route("/assignments/add", methods=["GET", "POST"])
@login_required
@role_required(ROLE_LECTURER)
def assignment_add():
    lect = _current_lecturer()
    course_opts = [(c.id, f"{c.code} - {c.name}") for c in lect.courses]
    if request.method == "POST":
        due = request.form.get("due_date")
        a = Assignment(course_id=request.form["course_id"], title=request.form["title"],
                       description=request.form.get("description"),
                       due_date=datetime.strptime(due, "%Y-%m-%d").date() if due else None,
                       max_score=request.form.get("max_score", 100))
        db.session.add(a)
        db.session.commit()
        log_action("create_assignment", f"Created assignment '{a.title}'")
        flash("Assignment created.", "success")
        return redirect(url_for("lecturer.assignments"))
    fields = [
        {"name": "course_id", "label": "Course", "type": "select", "required": True, "options": course_opts},
        {"name": "title", "label": "Title", "type": "text", "required": True},
        {"name": "description", "label": "Description", "type": "textarea"},
        {"name": "due_date", "label": "Due Date", "type": "date"},
        {"name": "max_score", "label": "Max Score", "type": "number", "value": 100},
    ]
    return render_template("generic_form.html", title="New Assignment", fields=fields,
                            cancel_url=url_for("lecturer.assignments"))


@lecturer_bp.route("/assignments/<int:assignment_id>/delete", methods=["POST"])
@login_required
@role_required(ROLE_LECTURER)
def assignment_delete(assignment_id):
    a = Assignment.query.get_or_404(assignment_id)
    db.session.delete(a)
    db.session.commit()
    log_action("delete_assignment", f"Deleted assignment '{a.title}'")
    flash("Assignment removed.", "info")
    return redirect(url_for("lecturer.assignments"))


@lecturer_bp.route("/assignments/<int:assignment_id>/submissions", methods=["GET", "POST"])
@login_required
@role_required(ROLE_LECTURER)
def assignment_submissions(assignment_id):
    a = Assignment.query.get_or_404(assignment_id)
    if a.course.lecturer_id != _current_lecturer().id:
        abort(403)

    if request.method == "POST":
        sub_id = request.form["submission_id"]
        sub = Submission.query.get_or_404(sub_id)
        sub.score = request.form.get("score") or None
        sub.feedback = request.form.get("feedback")
        db.session.commit()
        log_action("grade_submission", f"Graded submission #{sub_id} for '{a.title}'")
        flash("Grade saved.", "success")
        return redirect(url_for("lecturer.assignment_submissions", assignment_id=assignment_id))

    submissions = a.submissions
    return render_template("lecturer/submissions.html", assignment=a, submissions=submissions)


# ==================== PERFORMANCE ====================
@lecturer_bp.route("/performance")
@login_required
@role_required(ROLE_LECTURER)
def performance():
    lect = _current_lecturer()
    course_id = request.args.get("course_id", type=int)
    courses = lect.courses if lect else []
    course = None
    perf_rows = []
    if course_id:
        course = Course.query.get_or_404(course_id)
        if course.lecturer_id != lect.id:
            abort(403)
        for e in course.enrollments:
            mark = Mark.query.filter_by(student_id=e.student_id, course_id=course.id).first()
            perf_rows.append({
                "name": e.student.user.full_name,
                "reg_no": e.student.reg_no,
                "total": mark.total if mark else 0,
                "grade": mark.grade if mark else "—",
            })
    return render_template("lecturer/performance.html", courses=courses, course=course, perf_rows=perf_rows)
