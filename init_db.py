from app import app, db
from models.user import User
from models.class_ import Class

def init_db():
    with app.app_context():
        # Drop all tables
        print("Dropping all tables...")
        db.drop_all()
        
        # Create all tables
        print("Creating all tables...")
        db.create_all()
        
        print("Database initialized successfully!")

if __name__ == '__main__':
    init_db()
