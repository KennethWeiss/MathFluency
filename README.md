# Math Fluency

A comprehensive web application designed to help students practice and improve their math skills through interactive exercises and progress tracking.

## Features

- **Interactive Practice Sessions**
  - Addition (Levels 1-5)
  - Subtraction (Levels 1-5)
  - Multiplication (Times Tables 0-12)
  - Division (Levels 1-10)

- **Adaptive Learning**
  - Automatic level adjustment based on performance
  - Progress tracking and analytics
  - Detailed practice history

- **User Management**
  - Student accounts
  - Teacher accounts with class management
  - Admin dashboard
  - Google OAuth integration

- **Assignment System**
  - Teachers can create custom assignments
  - Progress tracking for assignments
  - Real-time feedback

## Technology Stack

- **Backend**
  - Flask 3.1.0
  - SQLAlchemy 2.0.36
  - Flask-SocketIO 5.5.1
  - Flask-Login 0.6.3
  - Python 3.8+

- **Frontend**
  - HTML5/CSS3
  - JavaScript
  - Bootstrap 5
  - WebSocket for real-time updates

- **Database**
  - SQLite (Development)
  - PostgreSQL (Production)

## Project Structure

```
MathFluency/
├── app.py                 # Main application entry point
├── models/              # Database models
│   ├── active_session.py        # Active practice session tracking
│   ├── assignments.py           # Assignment models and relationships
│   ├── class_.py                # Classroom management models
│   ├── oauth.py                 # OAuth authentication models
│   ├── practice_attempt.py      # Practice attempts model
│   ├── quiz.py                  # Quiz models and relationships
│   ├── user.py          # User model
│   └── 
├── routes/               # Route handlers
│   ├── auth_routes.py    # Authentication routes (login, registration, admin)
│   │   ├── admin # Admin dashboard and management
│   │   ├── admin/make_admin/<int:user_id> # Promote user to admin
│   │   ├── admin/toggle_teacher/<int:user_id> # Toggle teacher status
│   │   ├── admin/toggle_admin/<int:user_id> # Toggle admin status
│   │   ├── admin/delete_user/<int:user_id> # Delete user account
│   ├── assignment_routes.py # Assignment creation, management and grading
│   │   ├── assignments # View all assignments
│   │   ├── assignments/create # Create new assignment
│   │   ├── assignments/assignments/<int:id> # View specific assignment
│   │   ├── assignments/<int:id>/grade # Grade assignment
│   │   ├── assignments/<int:id>/edit # Edit assignment
│   │   ├── assignments/<int:id>/delete # Delete assignment
│   │   ├── assignments/<int:id>/grade/<int:student_id> # Grade student's assignment
│   │   ├── assignments/<int:id>/info> # Assignment information
│   │   ├── assignments/<int:id><int:assignment_id>/student/<int:student_id> # Student-specific assignment view
│   │   ├── assignments/assignments # List all assignments
│   │   ├── assignments/assignments/<int:id>/start # Start assignment
│   ├── auth_routes.py # User authentication and session management
│   │   ├── login # User login
│   │   ├── register # User registration
│   │   ├── logout # User logout
│   ├── class_routes.py # Classroom management and student enrollment
│   │   ├── classes # List all classes
│   │   ├── create_class # Create new class
│   │   ├── classes/<int:id>/edit # Edit class details
│   │   ├── classes/<int:id>students # View class students
│   │   ├── classes/<int:id>add_students # Add students to class
│   │   ├── classes/<int:id>remove_students # Remove students from class
│   │   ├── join # Join a class
│   │   ├── /upload_students # Bulk upload students
│   ├── layout_routes.py # UI layout and theme management
│   │   ├── /deltamath # DeltaMath style layout
│   │   ├── /99math # 99Math style layout
│   │   ├── /learning-path # Learning path view
│   │   ├── /dashboard # User dashboard
│   │   ├── /mastery-grid # Mastery grid view
│   │   ├── etc # Other layout options
│   ├── main_routes.py # Core application routes and navigation
│   │   ├── / # Home page
│   │   ├── /welcome # Welcome page
│   │   ├── /logout # Logout endpoint
│   ├── oauth.py # OAuth authentication and integration
│   │   ├── 
│   ├── practice_routes.py # Math practice session handling
│   │   ├── /practice # Start practice session
│   │   ├── /get_problem # Get new math problem
│   │   ├── /check_answer # Check problem answer
│   │   ├── /progress # View practice progress
│   ├── progress_routes.py # Student progress tracking and analytics
│   │   ├── /progress # View overall progress
│   │   ├── /student_progress/<int:student_id> # View student-specific progress
│   │   ├── /analyze_level/<operation>/<int:level> # Analyze performance by level
│   │   ├── /analyze_level/<operation>/<int:level>/<int:student_id> # Analyze student performance by level
│   │   ├── /incorrect_problems # View incorrect problems
│   ├── quiz_routes.py # Quiz creation, management and gameplay
│   │   ├── / # Quiz home
│   │   ├── /student # Student quiz interface
│   │   ├── /teacher # Teacher quiz interface
│   │   ├── /create # Create new quiz
│   │   ├── /teacher/<int:quiz_id> # Teacher quiz management
│   │   ├── /<int:quiz_id>/join # Join quiz session
│   │   ├── /<int:quiz_id>/status # Quiz status
│   │   ├── /<int:quiz_id>/leaderboard # Quiz leaderboard
│   └── teacher_routes.py # Teacher dashboard and classroom management
│   │   ├── /active_students # View active students with card display
├── services/           # Business logic
│   ├── progress_service.py # Progress tracking and analytics logic
├── standards/           # Math standards and curriculum
│   ├── CommonCoreMathBigIdeas.json  # Common Core math standards data
│   └── standard.py      # Standards implementation and utilities
├── static/           # Static assets (CSS, JS, images)
│   ├── css           # Stylesheets
│   ├── img           # Images and icons
│   ├── js            # JavaScript files
│   │   ├── main.js
│   │   ├── practice.js
│   │   ├── quiz.js
│   ├── favicon.ico
│   └── 
├── templates/          # HTML templates and views
├── tests/              # Unit and integration tests
├── utils/              # Utility functions and helpers
│   ├── math_problems.py   # Math problem generation utilities
│   │   ├── generate_problem
│   │   ├── generate_multiplication_problem
│   │   ├── get_random_number
│   │   ├── generate_custom_multiplication
│   │   ├── get_problem
│   └── practice_tracker.py # Practice session tracking and analytics
├── websockets
├── static/            # Static files (CSS, JS)
└── websockets/        # WebSocket handlers for real-time communication
```

## Setup and Installation

1. **Clone the Repository**
   ```bash
   git clone [repository-url]
   cd MathFluency
   ```

2. **Create Virtual Environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install Dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Environment Variables**
   Create a `.env` file with:
   ```
   SECRET_KEY=your-secret-key
   GOOGLE_CLIENT_ID=your-google-client-id
   GOOGLE_CLIENT_SECRET=your-google-client-secret
   DATABASE_URL=your-database-url
   ```

5. **Initialize Database**
   ```bash
   flask db upgrade
   python init_db.py
   ```

6. **Run the Application**
   ```bash
   python app.py
   ```

## Development

### Database Migrations
```bash
flask db migrate -m "Migration message"
flask db upgrade
```

### Running Tests
```bash
pytest
```

### Creating Test Users
```bash
python create_test_users.py
```

## Key Components

### Practice System
- Problems are generated dynamically based on level and operation
- Automatic difficulty adjustment based on performance
- Detailed progress tracking and analytics

### User Management
- Role-based access control (Student, Teacher, Admin)
- Google OAuth integration for easy login
- Secure password handling

### Assignment System
- Teachers can create custom assignments
- Real-time progress tracking
- Detailed performance analytics

## API Endpoints

### Practice Routes
- `POST /get_problem`: Get a new practice problem
- `POST /check_answer`: Submit and check an answer
- `GET /progress`: View practice progress

### Assignment Routes
- `POST /assignments/create`: Create new assignment
- `GET /assignments/<id>`: View assignment details
- `POST /assignments/<id>/submit`: Submit assignment

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## License

[License Type] - See LICENSE file for details

## Contact

[Your Contact Information]
