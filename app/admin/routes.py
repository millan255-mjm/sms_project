from datetime import datetime
from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user

from app import db
from app.models import (User, Student, Lecturer, Course, Department, ClassGroup,
                         Enrollment, TimetableSlot, Announcement, Mark, Attendance,
                         ROLE_ADMIN, ROLE_LECTURER, ROLE_STUDENT)
from app.utils import role_required, log_action

admin_bp = Blueprint("admin", __name__, template_folder="../templates/admin")

WEEKDAYS = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"]


@admin_bp.route("/dashboard")
@login_required
@role_required(ROLE_ADMIN)
def dashboard():
    stats = {
        "students": Student.query.count(),
        "lecturers": Lecturer.query.count(),
        "courses": Course.query.count(),
        "classes": ClassGroup.query.count(),
        "departments": Department.query.count(),
        "enrollments": Enrollment.query.count(),
    }
    recent_announcements = Announcement.query.order_by(Announcement.created_at.desc()).limit(5).all()
    return render_template("admin/dashboard.html", stats=stats, recent_announcements=recent_announcements)


# ==================== DEPARTMENTS ====================
@admin_bp.route("/departments")
@login_required
@role_required(ROLE_ADMIN)
def departments():
    depts = Department.query.order_by(Department.name).all()
    rows = [{"name": d.name, "code": d.code, "classes": len(d.classes), "courses": len(d.courses),
             "edit_url": url_for("admin.department_edit", dept_id=d.id),
             "delete_url": url_for("admin.department_delete", dept_id=d.id)} for d in depts]
    return render_template("generic_list.html", title="Departments / Programs",
                            subtitle="Manage academic departments",
                            add_url=url_for("admin.department_add"), add_label="Add Department",
                            columns=[("name", "Name"), ("code", "Code"), ("classes", "Classes"), ("courses", "Courses")],
                            rows=rows)


@admin_bp.route("/departments/add", methods=["GET", "POST"])
@login_required
@role_required(ROLE_ADMIN)
def department_add():
    if request.method == "POST":
        d = Department(name=request.form["name"], code=request.form["code"].upper())
        db.session.add(d)
        db.session.commit()
        log_action("create_department", f"Created department '{d.name}'")
        flash("Department created.", "success")
        return redirect(url_for("admin.departments"))
    fields = [{"name": "name", "label": "Department Name", "type": "text", "required": True},
              {"name": "code", "label": "Code", "type": "text", "required": True, "placeholder": "e.g. CS"}]
    return render_template("generic_form.html", title="Add Department", fields=fields,
                            cancel_url=url_for("admin.departments"))


@admin_bp.route("/departments/<int:dept_id>/edit", methods=["GET", "POST"])
@login_required
@role_required(ROLE_ADMIN)
def department_edit(dept_id):
    d = Department.query.get_or_404(dept_id)
    if request.method == "POST":
        d.name = request.form["name"]
        d.code = request.form["code"].upper()
        db.session.commit()
        log_action("edit_department", f"Edited department '{d.name}'")
        flash("Department updated.", "success")
        return redirect(url_for("admin.departments"))
    fields = [{"name": "name", "label": "Department Name", "type": "text", "required": True, "value": d.name},
              {"name": "code", "label": "Code", "type": "text", "required": True, "value": d.code}]
    return render_template("generic_form.html", title="Edit Department", fields=fields,
                            cancel_url=url_for("admin.departments"))


@admin_bp.route("/departments/<int:dept_id>/delete", methods=["POST"])
@login_required
@role_required(ROLE_ADMIN)
def department_delete(dept_id):
    d = Department.query.get_or_404(dept_id)
    db.session.delete(d)
    db.session.commit()
    log_action("delete_department", f"Deleted department '{d.name}'")
    flash("Department deleted.", "info")
    return redirect(url_for("admin.departments"))


# ==================== CLASSES ====================
@admin_bp.route("/classes")
@login_required
@role_required(ROLE_ADMIN)
def classes():
    class_list = ClassGroup.query.order_by(ClassGroup.name).all()
    rows = [{"name": c.name, "level": c.level or "—", "department": c.department.name if c.department else "—",
             "students": len(c.students),
             "edit_url": url_for("admin.class_edit", class_id=c.id),
             "delete_url": url_for("admin.class_delete", class_id=c.id)} for c in class_list]
    return render_template("generic_list.html", title="Manage Classes",
                            subtitle="Group students into classes / cohorts",
                            add_url=url_for("admin.class_add"), add_label="Add Class",
                            columns=[("name", "Class Name"), ("level", "Level"), ("department", "Department"), ("students", "Students")],
                            rows=rows)


def _class_fields(c=None):
    depts = [(d.id, d.name) for d in Department.query.order_by(Department.name).all()]
    return [
        {"name": "name", "label": "Class Name", "type": "text", "required": True, "value": c.name if c else "", "placeholder": "e.g. ND1 Networking A"},
        {"name": "level", "label": "Level / Year", "type": "text", "value": c.level if c else "", "placeholder": "e.g. Year 1"},
        {"name": "department_id", "label": "Department", "type": "select", "required": True, "options": depts, "value": c.department_id if c else ""},
    ]


@admin_bp.route("/classes/add", methods=["GET", "POST"])
@login_required
@role_required(ROLE_ADMIN)
def class_add():
    if request.method == "POST":
        c = ClassGroup(name=request.form["name"], level=request.form.get("level"),
                        department_id=request.form["department_id"])
        db.session.add(c)
        db.session.commit()
        log_action("create_class", f"Created class '{c.name}'")
        flash("Class created.", "success")
        return redirect(url_for("admin.classes"))
    return render_template("generic_form.html", title="Add Class", fields=_class_fields(),
                            cancel_url=url_for("admin.classes"))


@admin_bp.route("/classes/<int:class_id>/edit", methods=["GET", "POST"])
@login_required
@role_required(ROLE_ADMIN)
def class_edit(class_id):
    c = ClassGroup.query.get_or_404(class_id)
    if request.method == "POST":
        c.name = request.form["name"]
        c.level = request.form.get("level")
        c.department_id = request.form["department_id"]
        db.session.commit()
        log_action("edit_class", f"Edited class '{c.name}'")
        flash("Class updated.", "success")
        return redirect(url_for("admin.classes"))
    return render_template("generic_form.html", title="Edit Class", fields=_class_fields(c),
                            cancel_url=url_for("admin.classes"))


@admin_bp.route("/classes/<int:class_id>/delete", methods=["POST"])
@login_required
@role_required(ROLE_ADMIN)
def class_delete(class_id):
    c = ClassGroup.query.get_or_404(class_id)
    db.session.delete(c)
    db.session.commit()
    log_action("delete_class", f"Deleted class '{c.name}'")
    flash("Class deleted.", "info")
    return redirect(url_for("admin.classes"))


# ==================== COURSES ====================
@admin_bp.route("/courses")
@login_required
@role_required(ROLE_ADMIN)
def courses():
    course_list = Course.query.order_by(Course.code).all()
    rows = [{"code": c.code, "name": c.name, "units": c.credit_units,
             "department": c.department.name if c.department else "—",
             "lecturer": c.lecturer.user.full_name if c.lecturer else "Unassigned",
             "edit_url": url_for("admin.course_edit", course_id=c.id),
             "delete_url": url_for("admin.course_delete", course_id=c.id)} for c in course_list]
    return render_template("generic_list.html", title="Manage Courses",
                            subtitle="Create courses and assign lecturers",
                            add_url=url_for("admin.course_add"), add_label="Add Course",
                            columns=[("code", "Code"), ("name", "Course Name"), ("units", "Units"),
                                     ("department", "Department"), ("lecturer", "Lecturer")],
                            rows=rows)


def _course_fields(c=None):
    depts = [(d.id, d.name) for d in Department.query.order_by(Department.name).all()]
    lecturers = [(l.id, l.user.full_name) for l in Lecturer.query.all()]
    return [
        {"name": "code", "label": "Course Code", "type": "text", "required": True, "value": c.code if c else "", "placeholder": "e.g. NET201"},
        {"name": "name", "label": "Course Name", "type": "text", "required": True, "value": c.name if c else ""},
        {"name": "credit_units", "label": "Credit Units", "type": "number", "value": c.credit_units if c else 2},
        {"name": "department_id", "label": "Department", "type": "select", "required": True, "options": depts, "value": c.department_id if c else ""},
        {"name": "lecturer_id", "label": "Assigned Lecturer", "type": "select", "options": lecturers, "value": c.lecturer_id if c else ""},
    ]


@admin_bp.route("/courses/add", methods=["GET", "POST"])
@login_required
@role_required(ROLE_ADMIN)
def course_add():
    if request.method == "POST":
        c = Course(code=request.form["code"].upper(), name=request.form["name"],
                   credit_units=request.form.get("credit_units", 2),
                   department_id=request.form["department_id"],
                   lecturer_id=request.form.get("lecturer_id") or None)
        db.session.add(c)
        db.session.commit()
        log_action("create_course", f"Created course '{c.code}'")
        flash("Course created.", "success")
        return redirect(url_for("admin.courses"))
    return render_template("generic_form.html", title="Add Course", fields=_course_fields(),
                            cancel_url=url_for("admin.courses"))


@admin_bp.route("/courses/<int:course_id>/edit", methods=["GET", "POST"])
@login_required
@role_required(ROLE_ADMIN)
def course_edit(course_id):
    c = Course.query.get_or_404(course_id)
    if request.method == "POST":
        c.code = request.form["code"].upper()
        c.name = request.form["name"]
        c.credit_units = request.form.get("credit_units", 2)
        c.department_id = request.form["department_id"]
        c.lecturer_id = request.form.get("lecturer_id") or None
        db.session.commit()
        log_action("edit_course", f"Edited course '{c.code}'")
        flash("Course updated.", "success")
        return redirect(url_for("admin.courses"))
    return render_template("generic_form.html", title="Edit Course", fields=_course_fields(c),
                            cancel_url=url_for("admin.courses"))


@admin_bp.route("/courses/<int:course_id>/delete", methods=["POST"])
@login_required
@role_required(ROLE_ADMIN)
def course_delete(course_id):
    c = Course.query.get_or_404(course_id)
    db.session.delete(c)
    db.session.commit()
    log_action("delete_course", f"Deleted course '{c.code}'")
    flash("Course deleted.", "info")
    return redirect(url_for("admin.courses"))


# ==================== LECTURERS ====================
@admin_bp.route("/lecturers")
@login_required
@role_required(ROLE_ADMIN)
def lecturers():
    lect_list = Lecturer.query.all()
    rows = [{"full_name": l.user.full_name, "staff_id": l.staff_id, "username": l.user.username,
             "department": l.department.name if l.department else "—",
             "courses": len(l.courses),
             "edit_url": url_for("admin.lecturer_edit", lecturer_id=l.id),
             "delete_url": url_for("admin.lecturer_delete", lecturer_id=l.id)} for l in lect_list]
    return render_template("generic_list.html", title="Manage Lecturers",
                            subtitle="Create lecturer accounts and profiles",
                            add_url=url_for("admin.lecturer_add"), add_label="Add Lecturer",
                            columns=[("full_name", "Full Name"), ("staff_id", "Staff ID"), ("username", "Username"),
                                     ("department", "Department"), ("courses", "Courses")],
                            rows=rows)


@admin_bp.route("/lecturers/add", methods=["GET", "POST"])
@login_required
@role_required(ROLE_ADMIN)
def lecturer_add():
    depts = [(d.id, d.name) for d in Department.query.order_by(Department.name).all()]
    if request.method == "POST":
        username = request.form["username"].strip()
        if User.query.filter_by(username=username).first():
            flash("Username already exists.", "danger")
            return redirect(url_for("admin.lecturer_add"))
        u = User(full_name=request.form["full_name"], username=username,
                  email=request.form.get("email"), role=ROLE_LECTURER)
        u.set_password(request.form["password"])
        db.session.add(u)
        db.session.flush()
        l = Lecturer(user_id=u.id, staff_id=request.form["staff_id"],
                     department_id=request.form.get("department_id") or None,
                     phone=request.form.get("phone"), specialization=request.form.get("specialization"))
        db.session.add(l)
        db.session.commit()
        log_action("create_lecturer", f"Created lecturer '{username}'")
        flash("Lecturer account created.", "success")
        return redirect(url_for("admin.lecturers"))

    fields = [
        {"name": "full_name", "label": "Full Name", "type": "text", "required": True},
        {"name": "username", "label": "Username", "type": "text", "required": True},
        {"name": "password", "label": "Password", "type": "password", "required": True},
        {"name": "email", "label": "Email", "type": "email"},
        {"name": "staff_id", "label": "Staff ID", "type": "text", "required": True},
        {"name": "department_id", "label": "Department", "type": "select", "options": depts},
        {"name": "phone", "label": "Phone", "type": "text"},
        {"name": "specialization", "label": "Specialization", "type": "text"},
    ]
    return render_template("generic_form.html", title="Add Lecturer", fields=fields,
                            cancel_url=url_for("admin.lecturers"))


@admin_bp.route("/lecturers/<int:lecturer_id>/edit", methods=["GET", "POST"])
@login_required
@role_required(ROLE_ADMIN)
def lecturer_edit(lecturer_id):
    l = Lecturer.query.get_or_404(lecturer_id)
    depts = [(d.id, d.name) for d in Department.query.order_by(Department.name).all()]
    if request.method == "POST":
        l.user.full_name = request.form["full_name"]
        l.user.email = request.form.get("email")
        if request.form.get("password"):
            l.user.set_password(request.form["password"])
        l.staff_id = request.form["staff_id"]
        l.department_id = request.form.get("department_id") or None
        l.phone = request.form.get("phone")
        l.specialization = request.form.get("specialization")
        db.session.commit()
        log_action("edit_lecturer", f"Edited lecturer '{l.user.username}'")
        flash("Lecturer updated.", "success")
        return redirect(url_for("admin.lecturers"))

    fields = [
        {"name": "full_name", "label": "Full Name", "type": "text", "required": True, "value": l.user.full_name},
        {"name": "password", "label": "New Password", "type": "password", "help": "Leave blank to keep current password"},
        {"name": "email", "label": "Email", "type": "email", "value": l.user.email},
        {"name": "staff_id", "label": "Staff ID", "type": "text", "required": True, "value": l.staff_id},
        {"name": "department_id", "label": "Department", "type": "select", "options": depts, "value": l.department_id},
        {"name": "phone", "label": "Phone", "type": "text", "value": l.phone},
        {"name": "specialization", "label": "Specialization", "type": "text", "value": l.specialization},
    ]
    return render_template("generic_form.html", title=f"Edit Lecturer - {l.user.full_name}", fields=fields,
                            cancel_url=url_for("admin.lecturers"))


@admin_bp.route("/lecturers/<int:lecturer_id>/delete", methods=["POST"])
@login_required
@role_required(ROLE_ADMIN)
def lecturer_delete(lecturer_id):
    l = Lecturer.query.get_or_404(lecturer_id)
    username = l.user.username
    db.session.delete(l.user)
    db.session.commit()
    log_action("delete_lecturer", f"Deleted lecturer '{username}'")
    flash("Lecturer removed.", "info")
    return redirect(url_for("admin.lecturers"))


# ==================== STUDENTS ====================
@admin_bp.route("/students")
@login_required
@role_required(ROLE_ADMIN)
def students():
    student_list = Student.query.all()
    rows = [{"full_name": s.user.full_name, "reg_no": s.reg_no, "username": s.user.username,
             "class_name": s.class_group.name if s.class_group else "—",
             "phone": s.phone or "—",
             "edit_url": url_for("admin.student_edit", student_id=s.id),
             "delete_url": url_for("admin.student_delete", student_id=s.id)} for s in student_list]
    return render_template("generic_list.html", title="Manage Students",
                            subtitle="Create student accounts and profiles",
                            add_url=url_for("admin.student_add"), add_label="Add Student",
                            columns=[("full_name", "Full Name"), ("reg_no", "Reg No"), ("username", "Username"),
                                     ("class_name", "Class"), ("phone", "Phone")],
                            rows=rows)


@admin_bp.route("/students/add", methods=["GET", "POST"])
@login_required
@role_required(ROLE_ADMIN)
def student_add():
    class_list = [(c.id, c.name) for c in ClassGroup.query.order_by(ClassGroup.name).all()]
    if request.method == "POST":
        username = request.form["username"].strip()
        if User.query.filter_by(username=username).first():
            flash("Username already exists.", "danger")
            return redirect(url_for("admin.student_add"))
        if Student.query.filter_by(reg_no=request.form["reg_no"]).first():
            flash("Registration number already exists.", "danger")
            return redirect(url_for("admin.student_add"))
        u = User(full_name=request.form["full_name"], username=username,
                  email=request.form.get("email"), role=ROLE_STUDENT)
        u.set_password(request.form["password"])
        db.session.add(u)
        db.session.flush()
        s = Student(user_id=u.id, reg_no=request.form["reg_no"],
                    class_id=request.form.get("class_id") or None,
                    phone=request.form.get("phone"), address=request.form.get("address"))
        dob = request.form.get("dob")
        if dob:
            s.dob = datetime.strptime(dob, "%Y-%m-%d").date()
        db.session.add(s)
        db.session.commit()
        log_action("create_student", f"Created student '{username}'")
        flash("Student account created.", "success")
        return redirect(url_for("admin.students"))

    fields = [
        {"name": "full_name", "label": "Full Name", "type": "text", "required": True},
        {"name": "username", "label": "Username", "type": "text", "required": True},
        {"name": "password", "label": "Password", "type": "password", "required": True},
        {"name": "email", "label": "Email", "type": "email"},
        {"name": "reg_no", "label": "Registration Number", "type": "text", "required": True},
        {"name": "class_id", "label": "Class", "type": "select", "options": class_list},
        {"name": "phone", "label": "Phone", "type": "text"},
        {"name": "address", "label": "Address", "type": "text"},
        {"name": "dob", "label": "Date of Birth", "type": "date"},
    ]
    return render_template("generic_form.html", title="Add Student", fields=fields,
                            cancel_url=url_for("admin.students"))


@admin_bp.route("/students/<int:student_id>/edit", methods=["GET", "POST"])
@login_required
@role_required(ROLE_ADMIN)
def student_edit(student_id):
    s = Student.query.get_or_404(student_id)
    class_list = [(c.id, c.name) for c in ClassGroup.query.order_by(ClassGroup.name).all()]
    if request.method == "POST":
        s.user.full_name = request.form["full_name"]
        s.user.email = request.form.get("email")
        if request.form.get("password"):
            s.user.set_password(request.form["password"])
        s.reg_no = request.form["reg_no"]
        s.class_id = request.form.get("class_id") or None
        s.phone = request.form.get("phone")
        s.address = request.form.get("address")
        dob = request.form.get("dob")
        if dob:
            s.dob = datetime.strptime(dob, "%Y-%m-%d").date()
        db.session.commit()
        log_action("edit_student", f"Edited student '{s.user.username}'")
        flash("Student updated.", "success")
        return redirect(url_for("admin.students"))

    fields = [
        {"name": "full_name", "label": "Full Name", "type": "text", "required": True, "value": s.user.full_name},
        {"name": "password", "label": "New Password", "type": "password", "help": "Leave blank to keep current password"},
        {"name": "email", "label": "Email", "type": "email", "value": s.user.email},
        {"name": "reg_no", "label": "Registration Number", "type": "text", "required": True, "value": s.reg_no},
        {"name": "class_id", "label": "Class", "type": "select", "options": class_list, "value": s.class_id},
        {"name": "phone", "label": "Phone", "type": "text", "value": s.phone},
        {"name": "address", "label": "Address", "type": "text", "value": s.address},
        {"name": "dob", "label": "Date of Birth", "type": "date", "value": s.dob.isoformat() if s.dob else ""},
    ]
    return render_template("generic_form.html", title=f"Edit Student - {s.user.full_name}", fields=fields,
                            cancel_url=url_for("admin.students"))


@admin_bp.route("/students/<int:student_id>/delete", methods=["POST"])
@login_required
@role_required(ROLE_ADMIN)
def student_delete(student_id):
    s = Student.query.get_or_404(student_id)
    username = s.user.username
    db.session.delete(s.user)
    db.session.commit()
    log_action("delete_student", f"Deleted student '{username}'")
    flash("Student removed.", "info")
    return redirect(url_for("admin.students"))


# ==================== ENROLLMENT ====================
@admin_bp.route("/enrollment", methods=["GET", "POST"])
@login_required
@role_required(ROLE_ADMIN)
def enrollment():
    if request.method == "POST":
        student_id = request.form["student_id"]
        course_id = request.form["course_id"]
        existing = Enrollment.query.filter_by(student_id=student_id, course_id=course_id).first()
        if existing:
            flash("Student is already enrolled in this course.", "warning")
        else:
            e = Enrollment(student_id=student_id, course_id=course_id)
            db.session.add(e)
            db.session.commit()
            log_action("enroll_student", f"Enrolled student #{student_id} in course #{course_id}")
            flash("Student enrolled successfully.", "success")
        return redirect(url_for("admin.enrollment"))

    students_list = [(s.id, f"{s.user.full_name} ({s.reg_no})") for s in Student.query.all()]
    courses_list = [(c.id, f"{c.code} - {c.name}") for c in Course.query.all()]
    enrollments = Enrollment.query.order_by(Enrollment.date_enrolled.desc()).limit(100).all()
    rows = [{"student": e.student.user.full_name, "reg_no": e.student.reg_no,
             "course": f"{e.course.code} - {e.course.name}", "semester": e.semester,
             "delete_url": url_for("admin.enrollment_delete", enrollment_id=e.id)} for e in enrollments]
    return render_template("admin/enrollment.html", students=students_list, courses=courses_list, rows=rows)


@admin_bp.route("/enrollment/<int:enrollment_id>/delete", methods=["POST"])
@login_required
@role_required(ROLE_ADMIN)
def enrollment_delete(enrollment_id):
    e = Enrollment.query.get_or_404(enrollment_id)
    db.session.delete(e)
    db.session.commit()
    log_action("unenroll_student", f"Removed enrollment #{enrollment_id}")
    flash("Enrollment removed.", "info")
    return redirect(url_for("admin.enrollment"))


# ==================== TIMETABLE ====================
@admin_bp.route("/timetable")
@login_required
@role_required(ROLE_ADMIN)
def timetable():
    slots = TimetableSlot.query.all()
    rows = [{"course": f"{t.course.code} - {t.course.name}", "class_name": t.class_group.name if t.class_group else "All",
             "day": t.day, "time": f"{t.start_time} - {t.end_time}", "venue": t.venue or "—",
             "edit_url": url_for("admin.timetable_edit", slot_id=t.id),
             "delete_url": url_for("admin.timetable_delete", slot_id=t.id)} for t in slots]
    return render_template("generic_list.html", title="Timetable",
                            subtitle="Weekly class schedule",
                            add_url=url_for("admin.timetable_add"), add_label="Add Slot",
                            columns=[("course", "Course"), ("class_name", "Class"), ("day", "Day"),
                                     ("time", "Time"), ("venue", "Venue")],
                            rows=rows)


def _timetable_fields(t=None):
    courses_list = [(c.id, f"{c.code} - {c.name}") for c in Course.query.all()]
    class_list = [(c.id, c.name) for c in ClassGroup.query.all()]
    days = [(d, d) for d in WEEKDAYS]
    return [
        {"name": "course_id", "label": "Course", "type": "select", "required": True, "options": courses_list, "value": t.course_id if t else ""},
        {"name": "class_id", "label": "Class", "type": "select", "options": class_list, "value": t.class_id if t else ""},
        {"name": "day", "label": "Day", "type": "select", "required": True, "options": days, "value": t.day if t else ""},
        {"name": "start_time", "label": "Start Time", "type": "time", "required": True, "value": t.start_time if t else ""},
        {"name": "end_time", "label": "End Time", "type": "time", "required": True, "value": t.end_time if t else ""},
        {"name": "venue", "label": "Venue", "type": "text", "value": t.venue if t else ""},
    ]


@admin_bp.route("/timetable/add", methods=["GET", "POST"])
@login_required
@role_required(ROLE_ADMIN)
def timetable_add():
    if request.method == "POST":
        t = TimetableSlot(course_id=request.form["course_id"], class_id=request.form.get("class_id") or None,
                          day=request.form["day"], start_time=request.form["start_time"],
                          end_time=request.form["end_time"], venue=request.form.get("venue"))
        db.session.add(t)
        db.session.commit()
        log_action("create_timetable_slot", f"Added timetable slot for course #{t.course_id}")
        flash("Timetable slot added.", "success")
        return redirect(url_for("admin.timetable"))
    return render_template("generic_form.html", title="Add Timetable Slot", fields=_timetable_fields(),
                            cancel_url=url_for("admin.timetable"))


@admin_bp.route("/timetable/<int:slot_id>/edit", methods=["GET", "POST"])
@login_required
@role_required(ROLE_ADMIN)
def timetable_edit(slot_id):
    t = TimetableSlot.query.get_or_404(slot_id)
    if request.method == "POST":
        t.course_id = request.form["course_id"]
        t.class_id = request.form.get("class_id") or None
        t.day = request.form["day"]
        t.start_time = request.form["start_time"]
        t.end_time = request.form["end_time"]
        t.venue = request.form.get("venue")
        db.session.commit()
        log_action("edit_timetable_slot", f"Edited timetable slot #{slot_id}")
        flash("Timetable slot updated.", "success")
        return redirect(url_for("admin.timetable"))
    return render_template("generic_form.html", title="Edit Timetable Slot", fields=_timetable_fields(t),
                            cancel_url=url_for("admin.timetable"))


@admin_bp.route("/timetable/<int:slot_id>/delete", methods=["POST"])
@login_required
@role_required(ROLE_ADMIN)
def timetable_delete(slot_id):
    t = TimetableSlot.query.get_or_404(slot_id)
    db.session.delete(t)
    db.session.commit()
    log_action("delete_timetable_slot", f"Deleted timetable slot #{slot_id}")
    flash("Timetable slot removed.", "info")
    return redirect(url_for("admin.timetable"))


# ==================== ANNOUNCEMENTS ====================
@admin_bp.route("/announcements")
@login_required
@role_required(ROLE_ADMIN)
def announcements():
    ann_list = Announcement.query.order_by(Announcement.created_at.desc()).all()
    rows = [{"title": a.title, "target": a.target_role, "posted_by": a.posted_by.full_name if a.posted_by else "—",
             "date": a.created_at.strftime("%Y-%m-%d"),
             "delete_url": url_for("admin.announcement_delete", ann_id=a.id)} for a in ann_list]
    return render_template("generic_list.html", title="Announcements",
                            subtitle="Post updates visible to selected roles",
                            add_url=url_for("admin.announcement_add"), add_label="New Announcement",
                            columns=[("title", "Title"), ("target", "Audience"), ("posted_by", "Posted By"), ("date", "Date")],
                            rows=rows)


@admin_bp.route("/announcements/add", methods=["GET", "POST"])
@login_required
@role_required(ROLE_ADMIN)
def announcement_add():
    if request.method == "POST":
        a = Announcement(title=request.form["title"], body=request.form["body"],
                         target_role=request.form.get("target_role", "all"), posted_by_id=current_user.id)
        db.session.add(a)
        db.session.commit()
        log_action("create_announcement", f"Posted announcement '{a.title}'")
        flash("Announcement posted.", "success")
        return redirect(url_for("admin.announcements"))
    fields = [
        {"name": "title", "label": "Title", "type": "text", "required": True},
        {"name": "body", "label": "Message", "type": "textarea", "required": True},
        {"name": "target_role", "label": "Audience", "type": "select", "required": True,
         "options": [("all", "Everyone"), ("admin", "Admins"), ("lecturer", "Lecturers"), ("student", "Students")]},
    ]
    return render_template("generic_form.html", title="New Announcement", fields=fields,
                            cancel_url=url_for("admin.announcements"))


@admin_bp.route("/announcements/<int:ann_id>/delete", methods=["POST"])
@login_required
@role_required(ROLE_ADMIN)
def announcement_delete(ann_id):
    a = Announcement.query.get_or_404(ann_id)
    db.session.delete(a)
    db.session.commit()
    log_action("delete_announcement", f"Deleted announcement '{a.title}'")
    flash("Announcement removed.", "info")
    return redirect(url_for("admin.announcements"))


# ==================== REPORTS ====================
@admin_bp.route("/reports")
@login_required
@role_required(ROLE_ADMIN)
def reports():
    class_stats = [{"name": c.name, "count": len(c.students)} for c in ClassGroup.query.all()]
    course_stats = [{"code": c.code, "name": c.name, "enrolled": len(c.enrollments)} for c in Course.query.all()]
    return render_template("admin/reports.html", class_stats=class_stats, course_stats=course_stats)
