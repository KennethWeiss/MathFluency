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
├── routes/               # Route handlers
│   ├── auth_routes.py    # Authentication routes
│   ├── practice_routes.py # Practice session routes
│   └── ...
├── models/              # Database models
│   ├── user.py          # User model
│   ├── practice.py      # Practice attempts model
│   └── ...
├── services/           # Business logic
│   └── progress_service.py # Progress tracking logic
├── utils/              # Utility functions
│   ├── math_problems.py   # Problem generation
│   └── practice_tracker.py # Practice session tracking
├── templates/          # HTML templates
├── static/            # Static files (CSS, JS)
└── websockets/        # WebSocket handlers
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
