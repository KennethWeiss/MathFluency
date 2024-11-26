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
        Flask==2.3.3
        python-dotenv==1.0.0
        Flask-SQLAlchemy==3.0.5
        Flask-Login==0.6.2
        Flask-WTF==1.1.1
        werkzeug==2.3.7
        email-validator==2.0.0.post2

user.py user model added
    users with teacher and student specific fields

forms.py for authentication forms.
    imports into app.py

login.html
register.html
welcome.html
    Has a neat way of using jinja2 to display teacher and student

app.py updated
            GET THE PAGE THE USER WANTED TO GO TO BEFORE LOGGING IN
            next_page = request.args.get('next')
            return redirect(next_page) if next_page else redirect(url_for('welcome'))
   

has password hashing for security
Routes
    /login
    /register
    /welcome
    /logout

Reset password was added but not on page yet.
    removed

go over create test user

Adding teachers, students and classes
update user.py to add models
creates test user now creates teacher, student
reset_db.py to handle data migrations

Test Teacher Created:
------------------------
Username: teacher1
Email: teacher@example.com
Password: teacher123
Class: Math 101

Test Student Created:
------------------------
Username: student1
Email: student@example.com
Password: student123
Enrolled in: Math 101

also
student2
student123



create_class.html

class.html
for viewing class

practice.html
basic practice page for student

