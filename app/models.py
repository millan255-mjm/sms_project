from datetime import datetime, date
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

from app import db

ROLE_SUPERADMIN = "superadmin"
ROLE_ADMIN = "admin"
ROLE_LECTURER = "lecturer"
ROLE_STUDENT = "student"


class User(db.Model, UserMixin):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    full_name = db.Column(db.String(150), nullable=False)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(150), unique=True, nullable=True)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(20), nullable=False)  # superadmin/admin/lecturer/student
    is_active_account = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    student_profile = db.relationship("Student", backref="user", uselist=False, cascade="all, delete-orphan")
    lecturer_profile = db.relationship("Lecturer", backref="user", uselist=False, cascade="all, delete-orphan")

    def set_password(self, raw_password):
        self.password_hash = generate_password_hash(raw_password)

    def check_password(self, raw_password):
        return check_password_hash(self.password_hash, raw_password)

    @property
    def is_active(self):
        return self.is_active_account

    def role_label(self):
        return {
            ROLE_SUPERADMIN: "Super Admin",
            ROLE_ADMIN: "Admin",
            ROLE_LECTURER: "Lecturer",
            ROLE_STUDENT: "Student",
        }.get(self.role, self.role)


class Department(db.Model):
    __tablename__ = "departments"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150), nullable=False, unique=True)
    code = db.Column(db.String(20), nullable=False, unique=True)

    classes = db.relationship("ClassGroup", backref="department", cascade="all, delete-orphan")
    courses = db.relationship("Course", backref="department", cascade="all, delete-orphan")


class ClassGroup(db.Model):
    __tablename__ = "classes"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)  # e.g. "ND1 Networking A"
    level = db.Column(db.String(50), nullable=True)   # e.g. "Year 1"
    department_id = db.Column(db.Integer, db.ForeignKey("departments.id"), nullable=False)

    students = db.relationship("Student", backref="class_group")


class Lecturer(db.Model):
    __tablename__ = "lecturers"
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    staff_id = db.Column(db.String(50), unique=True, nullable=False)
    department_id = db.Column(db.Integer, db.ForeignKey("departments.id"), nullable=True)
    phone = db.Column(db.String(30), nullable=True)
    specialization = db.Column(db.String(150), nullable=True)

    department = db.relationship("Department")
    courses = db.relationship("Course", backref="lecturer")


class Student(db.Model):
    __tablename__ = "students"
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    reg_no = db.Column(db.String(50), unique=True, nullable=False)
    class_id = db.Column(db.Integer, db.ForeignKey("classes.id"), nullable=True)
    phone = db.Column(db.String(30), nullable=True)
    address = db.Column(db.String(255), nullable=True)
    dob = db.Column(db.Date, nullable=True)
    enrollment_date = db.Column(db.Date, default=date.today)

    enrollments = db.relationship("Enrollment", backref="student", cascade="all, delete-orphan")
    attendances = db.relationship("Attendance", backref="student", cascade="all, delete-orphan")
    marks = db.relationship("Mark", backref="student", cascade="all, delete-orphan")
    submissions = db.relationship("Submission", backref="student", cascade="all, delete-orphan")


class Course(db.Model):
    __tablename__ = "courses"
    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(20), unique=True, nullable=False)
    name = db.Column(db.String(150), nullable=False)
    credit_units = db.Column(db.Integer, default=2)
    department_id = db.Column(db.Integer, db.ForeignKey("departments.id"), nullable=False)
    lecturer_id = db.Column(db.Integer, db.ForeignKey("lecturers.id"), nullable=True)

    enrollments = db.relationship("Enrollment", backref="course", cascade="all, delete-orphan")
    attendances = db.relationship("Attendance", backref="course", cascade="all, delete-orphan")
    marks = db.relationship("Mark", backref="course", cascade="all, delete-orphan")
    assignments = db.relationship("Assignment", backref="course", cascade="all, delete-orphan")
    timetable_slots = db.relationship("TimetableSlot", backref="course", cascade="all, delete-orphan")


class Enrollment(db.Model):
    __tablename__ = "enrollments"
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey("students.id"), nullable=False)
    course_id = db.Column(db.Integer, db.ForeignKey("courses.id"), nullable=False)
    academic_year = db.Column(db.String(20), default="2025/2026")
    semester = db.Column(db.String(20), default="1st Semester")
    date_enrolled = db.Column(db.DateTime, default=datetime.utcnow)

    __table_args__ = (db.UniqueConstraint("student_id", "course_id", name="uq_student_course"),)


class Attendance(db.Model):
    __tablename__ = "attendance"
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey("students.id"), nullable=False)
    course_id = db.Column(db.Integer, db.ForeignKey("courses.id"), nullable=False)
    date = db.Column(db.Date, default=date.today, nullable=False)
    status = db.Column(db.String(20), default="present")  # present/absent/late

    __table_args__ = (db.UniqueConstraint("student_id", "course_id", "date", name="uq_attendance_slot"),)


class Assignment(db.Model):
    __tablename__ = "assignments"
    id = db.Column(db.Integer, primary_key=True)
    course_id = db.Column(db.Integer, db.ForeignKey("courses.id"), nullable=False)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=True)
    due_date = db.Column(db.Date, nullable=True)
    max_score = db.Column(db.Integer, default=100)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    submissions = db.relationship("Submission", backref="assignment", cascade="all, delete-orphan")


class Submission(db.Model):
    __tablename__ = "submissions"
    id = db.Column(db.Integer, primary_key=True)
    assignment_id = db.Column(db.Integer, db.ForeignKey("assignments.id"), nullable=False)
    student_id = db.Column(db.Integer, db.ForeignKey("students.id"), nullable=False)
    content = db.Column(db.Text, nullable=True)  # text / link submission
    submitted_at = db.Column(db.DateTime, default=datetime.utcnow)
    score = db.Column(db.Float, nullable=True)
    feedback = db.Column(db.String(255), nullable=True)

    __table_args__ = (db.UniqueConstraint("assignment_id", "student_id", name="uq_assignment_student"),)


class Mark(db.Model):
    __tablename__ = "marks"
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey("students.id"), nullable=False)
    course_id = db.Column(db.Integer, db.ForeignKey("courses.id"), nullable=False)
    ca_score = db.Column(db.Float, default=0)      # continuous assessment, out of 30
    exam_score = db.Column(db.Float, default=0)    # exam, out of 70
    academic_year = db.Column(db.String(20), default="2025/2026")
    semester = db.Column(db.String(20), default="1st Semester")

    __table_args__ = (db.UniqueConstraint("student_id", "course_id", "semester", "academic_year", name="uq_mark_slot"),)

    @property
    def total(self):
        return round((self.ca_score or 0) + (self.exam_score or 0), 2)

    @property
    def grade(self):
        t = self.total
        if t >= 70:
            return "A"
        if t >= 60:
            return "B"
        if t >= 50:
            return "C"
        if t >= 45:
            return "D"
        return "F"


class TimetableSlot(db.Model):
    __tablename__ = "timetable"
    id = db.Column(db.Integer, primary_key=True)
    course_id = db.Column(db.Integer, db.ForeignKey("courses.id"), nullable=False)
    class_id = db.Column(db.Integer, db.ForeignKey("classes.id"), nullable=True)
    day = db.Column(db.String(20), nullable=False)  # Monday..Saturday
    start_time = db.Column(db.String(10), nullable=False)  # "09:00"
    end_time = db.Column(db.String(10), nullable=False)    # "11:00"
    venue = db.Column(db.String(100), nullable=True)

    class_group = db.relationship("ClassGroup")


class Announcement(db.Model):
    __tablename__ = "announcements"
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    body = db.Column(db.Text, nullable=False)
    target_role = db.Column(db.String(20), default="all")  # all/admin/lecturer/student
    posted_by_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    posted_by = db.relationship("User")


class SystemSetting(db.Model):
    __tablename__ = "system_settings"
    id = db.Column(db.Integer, primary_key=True)
    key = db.Column(db.String(100), unique=True, nullable=False)
    value = db.Column(db.String(255), nullable=True)


class AuditLog(db.Model):
    __tablename__ = "audit_logs"
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True)
    username = db.Column(db.String(80), nullable=True)
    role = db.Column(db.String(20), nullable=True)
    action = db.Column(db.String(255), nullable=False)
    details = db.Column(db.String(500), nullable=True)
    ip_address = db.Column(db.String(50), nullable=True)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

    user = db.relationship("User")
