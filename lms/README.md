# LearnHub LMS - Learning Management System (MVP)

A simple, full-stack **Learning Management System** built with **Python, Django, HTML, CSS (Bootstrap) and JavaScript**.
Learners study at their own pace, instructors publish content and track progress.

## Features (MVP)

**Authentication and roles**
- Sign up / login / logout with two roles: **Student** and **Instructor**

**Instructor**
- Create, edit and delete courses
- Add lessons with text notes, a YouTube video and downloadable material (PDF/PPT/etc.)
- Create quizzes with multiple-choice questions (auto-graded)
- Create assignments, view student submissions, give a grade and feedback
- See enrolled students and their progress per course

**Student**
- Browse and search courses, enroll in a course
- Open lessons, watch videos, download material, mark lessons complete
- Track progress with a progress bar per course
- Take quizzes and see the score instantly
- Upload assignments (and resubmit), see grade and feedback

## Tech stack
Python 3, Django 5, SQLite, Bootstrap 5, HTML/CSS/JavaScript

## Run locally

```bash
git clone https://github.com/<your-username>/learnhub-lms.git
cd learnhub-lms
python -m venv venv
venv\Scripts\activate          # Windows   (Mac/Linux: source venv/bin/activate)
pip install -r requirements.txt
python manage.py migrate
python manage.py seed_demo     # optional: demo users + sample course
python manage.py runserver
```

Open http://127.0.0.1:8000/

**Demo logins** (after `seed_demo`): `instructor1` / `student1`, password `demo12345`

To use the Django admin: `python manage.py createsuperuser` then visit `/admin/`.

## Run tests
```bash
python manage.py test
```

## Data model
`User` + `Profile(role)` -> `Course` -> `Lesson`, `Quiz` -> `Question` -> `Choice`, `Assignment` -> `Submission`,
`Enrollment`, `LessonProgress`, `QuizAttempt`

## Future improvements
- Course categories, thumbnails and ratings
- Certificates on course completion
- Discussion forum / announcements
- Email notifications and deadlines reminders
- REST API (Django REST Framework) and a React front end
- Deployment with PostgreSQL and cloud file storage
