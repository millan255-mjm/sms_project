# Student Management System (Python / Flask)

A complete, role-based Student Management System with a web GUI — built with
Flask, SQLAlchemy and Flask-Login. Runs locally and deploys straight to
Railway so you can access it online via a link.

## Roles included

- **Super Admin** — Manage Admins, Manage All Users, System Settings,
  Database Backup, Reports, Security & Permissions, **Audit Logs**
- **Admin** — Manage Students, Lecturers, Departments, Classes, Courses,
  Course Enrollment, Timetable, Announcements, Reports
- **Lecturer** — My Courses, My Students, Record Attendance, Enter Marks,
  Manage Assignments (with grading), Student Performance
- **Student** — Profile, My Courses, My Results, My Attendance, My Assignments
  (submit work)

The login page has four tabs so anyone can choose **Student / Lecturer /
Admin / Super Admin** and sign in with the matching account.

## 1. Run it locally

```bash
# 1. Create a virtual environment (recommended)
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate

# 2. Install dependencies
pip install -r requirements.txt

# 3. Run the app
python run.py
```

Open **http://127.0.0.1:5000** in your browser.

A **Super Admin** account is created automatically the first time the app
starts:

```
username: superadmin
password: Admin@123
```

**Change this password immediately** (Manage Admins → or ask the user to
change it — currently done by re-registering; you can also edit it directly
in the database, or extend `superadmin/routes.py` with a "change my
password" view).

### Optional: load demo data

To explore the system with a ready-made Admin, Lecturer and Student account,
department, class, course, enrollment and sample marks/attendance, run:

```bash
python seed.py
```

This creates:

| Role      | Username    | Password      |
|-----------|-------------|---------------|
| Admin     | admin1      | Admin@123     |
| Lecturer  | lecturer1   | Lecturer@123  |
| Student   | student1    | Student@123   |

## 2. Project structure

```
sms_project/
├── app/
│   ├── __init__.py          # app factory, extensions, auto-seed super admin
│   ├── models.py            # all database models
│   ├── utils.py             # role_required decorator, audit-log helper
│   ├── main_routes.py       # root "/" redirect logic
│   ├── auth/routes.py       # login / logout
│   ├── superadmin/routes.py
│   ├── admin/routes.py
│   ├── lecturer/routes.py
│   ├── student/routes.py
│   ├── templates/           # Jinja2 templates (base.html + role folders)
│   └── static/
│       ├── css/style.css    # black theme, responsive sidebar
│       └── js/script.js     # mobile sidebar toggle
├── config.py                 # reads SECRET_KEY / DATABASE_URL from env
├── run.py                    # entry point (also used by gunicorn: run:app)
├── seed.py                   # optional demo-data loader
├── smoke_test.py             # automated route test covering all 4 roles
├── requirements.txt
├── Procfile                  # for Railway/Heroku-style platforms
├── railway.json
└── .gitignore
```

## 3. Deploy online with Railway

1. Push this project to a GitHub repository.
2. Go to [railway.app](https://railway.app) → **New Project** → **Deploy from
   GitHub repo** → select your repository.
3. Railway auto-detects Python and uses the `Procfile`
   (`gunicorn run:app`) to start the server.
4. **Add a database (recommended for production):**
   - In your Railway project, click **+ New** → **Database** → **PostgreSQL**.
   - Railway automatically injects a `DATABASE_URL` environment variable into
     your app service — `config.py` already reads it and converts
     `postgres://` to `postgresql://` automatically. No code changes needed.
   - If you skip this step, the app falls back to a local SQLite file, which
     works fine for a single instance but is **not persistent** across
     redeploys on Railway (the filesystem resets). Adding Postgres is
     strongly recommended for anything beyond a quick test.
5. **Set environment variables** (Railway → your service → *Variables*):
   - `SECRET_KEY` → any long random string
   - `DEFAULT_SUPERADMIN_USERNAME` / `DEFAULT_SUPERADMIN_PASSWORD` (optional,
     otherwise defaults to `superadmin` / `Admin@123`)
6. Click **Deploy**. Railway will give you a public URL
   (e.g. `https://your-app.up.railway.app`) — that's your online link.
7. Log in with the Super Admin account, change the password, and start
   creating Admins, Lecturers and Students from the dashboard.

To load the demo data on Railway, open the service's **Shell** tab (or run a
one-off command) and execute `python seed.py`.

## 4. Notes & things you can extend

- **Assignment submissions** are text/link based (paste an answer or a link
  to your work, e.g. Google Drive/GitHub) rather than file uploads, to keep
  the system simple and easy to deploy without extra file-storage setup. You
  can add file uploads later using Flask's `request.files` plus a storage
  service (e.g. an S3-compatible bucket), since Railway's filesystem isn't
  persistent.
- **Database backup** (Super Admin → Database Backup) offers a one-click
  `.db` file download when running on SQLite. On PostgreSQL (Railway), use
  Railway's built-in database backup/snapshot tools instead — this is the
  safer approach in production.
- **Audit Logs** capture logins/logouts and every create/edit/delete action
  across the system, visible to the Super Admin.
- The CSS uses a fixed sidebar on desktop and a slide-out drawer (tap the
  hamburger button, top-left) on mobile, per your requirements.
- All forms use plain HTML/CSS/JS — no external UI framework — so there is
  nothing extra to install on the frontend.

## 5. Security checklist before going live

- [ ] Change the default Super Admin password
- [ ] Set a strong, random `SECRET_KEY` environment variable
- [ ] Use PostgreSQL (not SQLite) for production
- [ ] Restrict who you give Admin/Super Admin accounts to
- [ ] Regularly review Audit Logs
