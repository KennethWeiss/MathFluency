# Math Fluency

A web application designed to help students practice and master basic math operations through interactive exercises and detailed progress tracking. Teachers can monitor their students' progress and identify areas needing additional focus.

## Features

### User System
- **Role-Based Access**:
  - Teachers can view student progress and manage classes
  - Students can practice problems and track their own progress
- **Secure Authentication**:
  - User registration with email verification
  - Password hashing and secure session management

### Practice System
- **Addition Practice**:
  - Level 1: Adding 1 to single digit
  - Level 2: Adding 2 to single digit
  - Level 3: Make 10
  - Level 4: Add single digit to double digit
  - Level 5: Add double digit to double digit
- **Multiplication Practice**:
  - Tables 0-12 with progressive difficulty
  - Adaptive problem selection based on performance
- **Real-time Feedback**:
  - Immediate answer validation
  - Streak tracking for motivation
  - Time tracking per problem

### Progress Tracking
- **Detailed Statistics**:
  - Overall accuracy and attempt counts
  - Current streak tracking
  - Average completion time
  - Level-specific performance metrics
- **Teacher Dashboard**:
  - View individual student progress
  - Track class-wide performance
  - Identify common problem areas

## Technical Architecture

### Backend Framework
- **Flask** (Python web framework)
  - Blueprints for modular route organization
  - Jinja2 templating for dynamic HTML
  - Flask-Login for authentication

### Database
- **SQLAlchemy ORM**
  - User model (teachers and students)
  - Class model for grouping students
  - PracticeAttempt model for tracking progress
- **SQLite** for data storage

### Frontend
- **Bootstrap 5** for responsive design
- **JavaScript** for interactive features
- **HTML5/CSS3** for structure and styling

## Project Structure

### Core Components
```
MathFluency/
├── app.py                 # Application entry point
├── routes/               # Route blueprints
│   ├── auth_routes.py    # Authentication routes
│   └── practice_routes.py # Practice functionality
├── services/             # Business logic
│   └── progress_service.py # Progress calculation
├── models/               # Database models
│   ├── user.py
│   ├── class_.py
│   └── practice_attempt.py
├── templates/            # Jinja2 templates
│   ├── base.html        # Base template
│   ├── welcome.html     # Dashboard
│   └── progress.html    # Progress view
└── static/              # Static assets
```

### Key Routes
- `/` - Home/landing page
- `/auth/login` - User login
- `/auth/register` - User registration
- `/welcome` - User dashboard
- `/practice` - Practice interface
- `/progress` - Progress tracking
- `/student_progress/<id>` - Individual student progress (teachers only)

### Templates
- **Base Template**: Common layout and navigation
- **Welcome**: Role-specific dashboard
- **Progress**: Statistical display with charts
- **Practice**: Interactive problem solving

## Routes Documentation

The application is organized into several route blueprints, each handling specific functionality:

### Authentication Routes (`auth_routes.py`)
- `/login` (GET, POST): User login page and authentication
  - Template: `login.html`
  - DB: Queries User table for authentication
- `/register` (GET, POST): New user registration
  - Template: `register.html`
  - DB: Creates new User record
- `/logout`: Logs out the current user
  - Redirects to home page

### Main Routes (`main_routes.py`)
- `/` (GET): Home page
  - Template: `index.html` or redirects to welcome
- `/welcome` (GET): Dashboard after login
  - Template: `welcome.html`
  - Different views for teachers (shows students/classes) and students (shows enrolled class)

### Practice Routes (`practice_routes.py`)
- `/practice` (GET): Main practice interface
  - Template: `practice.html`
  - Supports both free practice and assignment modes
- `/get_problem` (POST): API endpoint for getting math problems
  - Generates problems based on operation/level or assignment settings
- `/check_answer` (POST): Validates answers and records attempts
  - DB: Updates PracticeAttempt and AssignmentProgress

### Assignment Routes (`assignment_routes.py`)
Teacher Routes:
- `/assignments` (GET): List all teacher's assignments
  - Template: `assignments/teacher_list.html`
- `/assignments/create` (GET, POST): Create new assignments
  - Template: `assignments/create.html`
  - DB: Creates Assignment and AssignmentProgress records
- `/assignments/<id>` (GET): View assignment details
  - Template: `assignments/view.html`
- `/assignments/<id>/grade` (GET): Grade assignment interface
  - Template: `assignments/grade.html`
- `/assignments/<id>/edit` (GET, POST): Edit assignment
  - Template: `assignments/edit.html`
  - DB: Updates Assignment record

Student Routes:
- `/assignments/student` (GET): List student's assignments
  - Template: `assignments/student_list.html`
- `/assignments/<id>/start` (GET): Start an assignment
  - Template: `practice.html` with assignment mode
  - DB: Updates AssignmentProgress

### Progress Routes (`progress_routes.py`)
- `/progress` (GET): View overall progress
  - Template: `progress/overview.html`
  - Shows stats across all operations
- `/progress/student/<id>` (GET): View specific student's progress (teachers only)
  - Template: `progress/student.html`
  - Shows detailed student performance
- `/progress/analyze/<operation>/<level>` (GET): Detailed level analysis
  - Template: `progress/level_analysis.html`
  - Shows performance metrics and problem patterns
- `/progress/incorrect` (GET): View incorrect problems
  - Template: `progress/incorrect.html`
  - Lists problems that need more practice

### Layout Routes (`layout_routes.py`)
- Contains shared layout components and navigation elements
- Manages common UI elements across the application

Each route is protected with appropriate authentication checks using Flask-Login's `@login_required` decorator where necessary. Teachers have additional authorization checks for teacher-specific routes.

## Setup and Installation

1. **Clone the Repository**
   ```bash
   git clone <repository-url>
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

4. **Initialize Database**
   ```bash
   flask db upgrade
   ```

5. **Create Test Users**
   ```bash
   python create_test_users.py
   ```

6. **Run the Application**
   ```bash
   flask run
   ```

## Test Accounts

### Teacher Account
- Username: teacher1
- Email: teacher@example.com
- Password: teacher123
- Class: Math 101

### Student Accounts
1. First Student
   - Username: student1
   - Password: student123
   - Class: Math 101

2. Second Student
   - Username: student2
   - Password: student123
   - Class: Math 101

## Development Roadmap

### Current Features
- [x] User authentication system
- [x] Basic practice interface
- [x] Progress tracking
- [x] Teacher dashboard

### Planned Features
- [ ] Additional operation types (subtraction, division)
- [ ] Advanced analytics dashboard
- [ ] Problem area diagnostics
- [ ] Adaptive difficulty system
- [ ] Parent portal
- [ ] Homework assignment system

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

## License

This project is licensed under the MIT License - see the LICENSE file for details.
