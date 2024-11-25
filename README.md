# Math Fluency

A Flask-based web application for improving math fluency.

## Setup

1. Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Unix/macOS
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Run the application:
```bash
flask run
```

The application will be available at http://localhost:5000

Go over requirements.txt
user.py user model added
//should be in models
forms.py for authentication forms.
login.html
register.html
welcome.html
app.py updated
has password hashing for security
Routes
    /login
    /register
    /welcome
    /logout

Reset password was added but not on page yet.

go over create test user

Adding teachers, students and classes
update user.py to add models
creates test user now creates teacher, student
reset_db.py to handle data migrations

est Teacher Created:
------------------------
Username: testteacher
Email: teacher@example.com
Password: teacher123
Class: Math 101

Test Student Created:
------------------------
Username: teststudent
Email: student@example.com
Password: student123
Enrolled in: Math 101

update app.py 
/dashboard has teacher and student route
dashboard.html

create_class.html

class.html
for viewing class

practice.html
basic practice page for student

