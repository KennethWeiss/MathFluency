from flask.cli import FlaskGroup
from app import app, db
from models.user import User
from models.class_ import Class
from models.practice_attempt import PracticeAttempt
from models.assignment import Assignment, AssignmentProgress, AttemptHistory
import os
from sqlalchemy import inspect

cli = FlaskGroup(app)

def table_exists(table_name):
    """Check if a table exists in the database"""
    inspector = inspect(db.engine)
    return table_name in inspector.get_table_names()

@cli.command("init_db")
def init_db():
    """Initialize the database only if tables don't exist"""
    if not table_exists('user'):
        print("Creating database tables in order...")
        # Create tables in order of dependencies
        models = [
            User,           # First create User table
            Class,          # Then Class table (depends on User)
            PracticeAttempt # Then PracticeAttempt (depends on User and Class)
        ]
        
        for model in models:
            print(f"Creating table: {model.__tablename__}")
            model.__table__.create(db.engine)
            
        print("Database initialized!")
    else:
        print("Database tables already exist, skipping initialization")

@cli.command("create_admin")
def create_admin():
    """Create an admin user if one doesn't exist"""
    admin_email = os.environ.get('ADMIN_EMAIL')
    admin_password = os.environ.get('ADMIN_PASSWORD')
    
    if not admin_email or not admin_password:
        print("Error: ADMIN_EMAIL and ADMIN_PASSWORD environment variables must be set")
        return

    # Check if admin already exists
    existing_admin = User.query.filter_by(email=admin_email).first()
    if existing_admin:
        print(f"Admin user {admin_email} already exists")
        return

    admin = User(
        username=admin_email.split('@')[0],  # Use part of email as username
        email=admin_email
    )
    admin.set_password(admin_password)
    admin.is_admin = True
    db.session.add(admin)
    try:
        db.session.commit()
        print(f"Created admin user: {admin_email}")
    except Exception as e:
        db.session.rollback()
        print(f"Error creating admin user: {str(e)}")

@cli.command("safe_setup_db")
def safe_setup_db():
    """Safely initialize database and create admin user without dropping existing data"""
    print("Checking database...")
    init_db()
    print("Checking admin user...")
    create_admin()
    print("Setup complete!")

@cli.command("full_init_db")
def full_init_db():
    """Fully initialize the database by dropping all tables and recreating them"""
    with app.app_context():
        # Drop all tables
        db.drop_all()
        # Create all tables
        db.create_all()
        print("Database initialized successfully!")

@app.cli.command("reset-db")
def reset_db():
    """Reset the database by dropping and recreating all tables."""
    with app.app_context():
        # Drop all tables
        db.drop_all()
        # Create all tables
        db.create_all()
        # Create alembic_version table with current head
        from flask_migrate import stamp
        stamp()

if __name__ == '__main__':
    cli()
