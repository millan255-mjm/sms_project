from app import create_app

app = create_app()
app.config["WTF_CSRF_ENABLED"] = False
client = app.test_client()

results = []

def check(method, url, data=None, expect=(200, 302), label=""):
    if method == "GET":
        r = client.get(url, follow_redirects=False)
    else:
        r = client.post(url, data=data or {}, follow_redirects=False)
    ok = r.status_code in expect
    results.append((ok, method, url, r.status_code, label))
    return r

def login(username, password, role):
    return client.post("/login", data={"username": username, "password": password, "role": role}, follow_redirects=True)

def logout():
    client.get("/logout", follow_redirects=True)

# ---- Guest ----
check("GET", "/", label="root redirect")
check("GET", "/login", label="login page")

# ---- Super Admin ----
r = login("superadmin", "Admin@123", "superadmin")
assert b"Super Admin Dashboard" in r.data, "superadmin login failed"
for url in ["/superadmin/dashboard", "/superadmin/admins", "/superadmin/admins/add",
            "/superadmin/users", "/superadmin/settings", "/superadmin/backup",
            "/superadmin/reports", "/superadmin/security", "/superadmin/audit-logs"]:
    check("GET", url, label="superadmin page")

check("POST", "/superadmin/admins/add", data={"full_name": "Test Admin", "username": "testadmin",
      "password": "pass1234", "email": "ta@x.com"}, label="create admin")
r = check("GET", "/superadmin/backup/download", label="backup download")
logout()

# ---- Admin ----
r = login("admin1", "Admin@123", "admin")
assert b"Admin Dashboard" in r.data, "admin login failed"
for url in ["/admin/dashboard", "/admin/departments", "/admin/departments/add",
            "/admin/classes", "/admin/classes/add", "/admin/courses", "/admin/courses/add",
            "/admin/lecturers", "/admin/lecturers/add", "/admin/students", "/admin/students/add",
            "/admin/enrollment", "/admin/timetable", "/admin/timetable/add",
            "/admin/announcements", "/admin/announcements/add", "/admin/reports"]:
    check("GET", url, label="admin page")

check("POST", "/admin/departments/add", data={"name": "Software Engineering", "code": "SE"}, label="create dept")
check("POST", "/admin/classes/add", data={"name": "ND2 SE B", "level": "Year 2", "department_id": "1"}, label="create class")
check("POST", "/admin/announcements/add", data={"title": "Test", "body": "Body text", "target_role": "all"}, label="create announcement")
logout()

# ---- Lecturer ----
r = login("lecturer1", "Lecturer@123", "lecturer")
assert b"Welcome" in r.data, "lecturer login failed"
for url in ["/lecturer/dashboard", "/lecturer/my-courses", "/lecturer/my-students",
            "/lecturer/attendance", "/lecturer/marks", "/lecturer/assignments", "/lecturer/performance"]:
    check("GET", url, label="lecturer page")

check("GET", "/lecturer/attendance?course_id=1", label="attendance for course")
check("POST", "/lecturer/attendance", data={"course_id": "1", "att_date": "2026-09-27", "status_1": "present"}, label="save attendance")
check("GET", "/lecturer/marks?course_id=1", label="marks for course")
check("POST", "/lecturer/marks", data={"course_id": "1", "ca_1": "28", "exam_1": "65"}, label="save marks")
check("POST", "/lecturer/assignments/add", data={"course_id": "1", "title": "Assignment 1", "description": "Do it", "due_date": "2026-10-01", "max_score": "100"}, label="create assignment")
check("GET", "/lecturer/assignments/1/submissions", label="view submissions")
check("GET", "/lecturer/performance?course_id=1", label="performance for course")
logout()

# ---- Student ----
r = login("student1", "Student@123", "student")
assert b"Welcome" in r.data, "student login failed"
for url in ["/student/dashboard", "/student/profile", "/student/courses",
            "/student/results", "/student/attendance", "/student/assignments"]:
    check("GET", url, label="student page")

check("GET", "/student/assignments/1/submit", label="assignment submit form")
check("POST", "/student/assignments/1/submit", data={"content": "My answer here"}, label="submit assignment")
check("POST", "/student/profile", data={"phone": "08012345678", "address": "Lagos"}, label="update profile")
logout()

print("\n===== RESULTS =====")
failures = [r for r in results if not r[0]]
for ok, method, url, status, label in results:
    mark = "OK " if ok else "FAIL"
    print(f"[{mark}] {method:5s} {url:50s} -> {status}  ({label})")

print(f"\n{len(results) - len(failures)}/{len(results)} checks passed.")
if failures:
    print("FAILURES DETECTED")
else:
    print("ALL CHECKS PASSED")
