# Math Fluency



A web application to help students practice and improve their math skills through interactive exercises and progress tracking.

## Features

- **User Authentication**: Secure login and registration system
- **Interactive Practice**: 
  - Addition practice with multiple difficulty levels
  - Multiplication practice with tables from 0 to 12
  - Real-time feedback on answers
- **Progress Tracking**: 
  - Detailed statistics on practice attempts
  - Performance metrics by operation type
  - Time tracking for problem-solving speed

## Technical Stack

- **Backend**: Flask (Python)
- **Database**: SQLAlchemy with SQLite
- **Frontend**: HTML, JavaScript, Bootstrap 5
- **Authentication**: Flask-Login

## Project Structure

### Models
- `User`: Handles user authentication and profile data    
    - `Teacher`: Represents teachers
    - `Student`: Represents students  

    - `Class`: Associates users with classes

- `Assignment`: Associates problems with assignments
- `Problem`: Stores math problems and their attributes
- `PracticeAttempt`: Tracks individual practice attempts and performance

### Routes
- `/`: Welcome page and user dashboard
    - uses a jinja2 template to display teacher and student
- `/practice`: Interactive math practice interface
- `/progress`: Performance statistics and tracking
- `/record_attempt`: API endpoint for recording practice attempts

## Template Structure

The application uses Flask's template inheritance system for consistent layout and styling across pages:

### Base Template (`templates/base.html`)
- Provides the common HTML structure and navigation
- Contains blocks for page-specific customization:
  - `title`: Page title
  - `content`: Main page content
  - `extra_css`: Additional CSS files
  - `extra_js`: Additional JavaScript

### Page Templates
- `welcome.html`: Landing page and user dashboard
- `practice.html`: Math practice interface with problem generation
- `progress.html`: User progress tracking and statistics

All pages extend the base template and override specific blocks as needed, ensuring consistent styling and navigation while maintaining clean, modular code.

## Setup and Installation

1. Clone the repository
2. Create a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```
3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
4. Initialize the database:
   ```bash
   flask db upgrade
   ```
5. Run the application:
   ```bash
   flask run
   ```

## Development

The application is built with extensibility in mind. Key areas for future development include:
- Additional operation types (subtraction, division)
- Advanced analytics and progress visualization
- Teacher/admin dashboard for monitoring student progress
- Adaptive difficulty based on user performance


## Test User
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

student2
student123


app.py
    /get_problem - Generates a new problem:
    Takes operation and level from the form data
    Uses our get_problem() function to generate a problem and answer
    Returns JSON with the problem text and correct answer

app.py updated
            GET THE PAGE THE USER WANTED TO GO TO BEFORE LOGGING IN
            next_page = request.args.get('next')
            return redirect(next_page) if next_page else redirect(url_for('welcome'))

create_class.html

class.html
for viewing class

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


I'm trying to think of a better way to have students practice problems they are struggling with. 
I am think of creating a table that tracks problem areas this becomes a review diagnostic tool.

