"""
Optional demo-data seeder.
Run with:  python seed.py
Creates a sample department, class, course, one admin, one lecturer,
one student, an enrollment and a few marks/attendance records so you
can explore the system immediately after deployment.

Safe to run multiple times - it skips anything that already exists.
"""
from datetime import date

from app import create_app, db
from app.models import (User, Department, ClassGroup, Course, Lecturer, Student,
                         Enrollment, Attendance, Mark, Announcement,
                         ROLE_ADMIN, ROLE_LECTURER, ROLE_STUDENT)

app = create_app()

with app.app_context():
    dept = Department.query.filter_by(code="NET").first()
    if not dept:
        dept = Department(name="Networking & IT Security", code="NET")
        db.session.add(dept)
        db.session.commit()

    cls = ClassGroup.query.filter_by(name="ND1 Networking A").first()
    if not cls:
        cls = ClassGroup(name="ND1 Networking A", level="Year 1", department_id=dept.id)
        db.session.add(cls)
        db.session.commit()

    course = Course.query.filter_by(code="NET201").first()
    if not course:
        course = Course(code="NET201", name="Routing & Switching Fundamentals",
                        credit_units=3, department_id=dept.id)
        db.session.add(course)
        db.session.commit()

    admin_user = User.query.filter_by(username="admin1").first()
    if not admin_user:
        admin_user = User(full_name="Grace Admin", username="admin1",
                          email="admin1@sms.local", role=ROLE_ADMIN)
        admin_user.set_password("Admin@123")
        db.session.add(admin_user)
        db.session.commit()

    lect_user = User.query.filter_by(username="lecturer1").first()
    if not lect_user:
        lect_user = User(full_name="Mr. John Networker", username="lecturer1",
                         email="lecturer1@sms.local", role=ROLE_LECTURER)
        lect_user.set_password("Lecturer@123")
        db.session.add(lect_user)
        db.session.commit()
        lect_profile = Lecturer(user_id=lect_user.id, staff_id="STF001",
                                department_id=dept.id, specialization="Network Security")
        db.session.add(lect_profile)
        db.session.commit()
    else:
        lect_profile = lect_user.lecturer_profile

    if not course.lecturer_id:
        course.lecturer_id = lect_profile.id
        db.session.commit()

    stu_user = User.query.filter_by(username="student1").first()
    if not stu_user:
        stu_user = User(full_name="Millan Joel", username="student1",
                        email="student1@sms.local", role=ROLE_STUDENT)
        stu_user.set_password("Student@123")
        db.session.add(stu_user)
        db.session.commit()
        stu_profile = Student(user_id=stu_user.id, reg_no="NET/2025/001",
                              class_id=cls.id, enrollment_date=date.today())
        db.session.add(stu_profile)
        db.session.commit()
    else:
        stu_profile = stu_user.student_profile

    if not Enrollment.query.filter_by(student_id=stu_profile.id, course_id=course.id).first():
        db.session.add(Enrollment(student_id=stu_profile.id, course_id=course.id))
        db.session.commit()

    if not Mark.query.filter_by(student_id=stu_profile.id, course_id=course.id).first():
        db.session.add(Mark(student_id=stu_profile.id, course_id=course.id, ca_score=25, exam_score=60))
        db.session.commit()

    if not Attendance.query.filter_by(student_id=stu_profile.id, course_id=course.id, date=date.today()).first():
        db.session.add(Attendance(student_id=stu_profile.id, course_id=course.id, date=date.today(), status="present"))
        db.session.commit()

    if not Announcement.query.first():
        db.session.add(Announcement(title="Welcome to the new semester!",
                                    body="Please check your timetable and enrolled courses.",
                                    target_role="all", posted_by_id=admin_user.id))
        db.session.commit()

    print("Demo data seeded successfully.")
    print("Login accounts created:")
    print("  Super Admin -> username: superadmin  / password: Admin@123 (auto-created on first boot)")
    print("  Admin       -> username: admin1      / password: Admin@123")
    print("  Lecturer    -> username: lecturer1   / password: Lecturer@123")
    print("  Student     -> username: student1    / password: Student@123")
