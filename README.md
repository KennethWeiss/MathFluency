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

go over create test user

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


WHERE TO START
1.Problem Model Structure:
    Basic problem attributes:
        Problem text/description
        Difficulty level
        Category (e.g., addition, subtraction, word problems)
        Correct answer
        Points/score value
    Optional features:
        Multiple choice options
        Hints
        Step-by-step solutions
2.Assignment System:
    Teachers can:
        Create assignments with selected problems
        Set due dates
        Assign to entire class or specific students
        Set minimum score requirements
    Students can:
        See assigned problems
        Track completion status
        View their scores and progress
3.Practice Mode:
    Students can:
    Choose problem categories
    Select difficulty levels
    Practice without time pressure
    Track personal improvement
4.Progress Tracking:
    Track attempts and success rates
    Show improvement over time
    Generate reports for teachers
    Identify areas needing more practice
    Would you like me to start implementing any of these components? We could begin with:

Creating the Problem model
Setting up the assignment system
Building the practice mode interface
Implementing progress tracking
What aspect would you like to tackle first?

Go up for more info
I started with creating the Problem model and setting up the assignment system.
Next, I would like to build the practice mode interface and implement progress tracking.


app.py
/get_problem - Generates a new problem:
Takes operation and level from the form data
Uses our get_problem() function to generate a problem and answer
Returns JSON with the problem text and correct answer