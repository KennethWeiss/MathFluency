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