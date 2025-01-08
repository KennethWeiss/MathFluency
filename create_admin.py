from app import app, db
from models.user import User

def create_admin_user():
    with app.app_context():
        # Check if admin user already exists
        admin = User.query.filter_by(username='admin').first()
        if admin:
            print('Admin user already exists')
            return
        
        # Create new admin user
        admin = User(
            username='admin',
            email='admin@example.com',
            is_teacher=True,
            is_admin=True
        )
        admin.set_password('admin123')
        db.session.add(admin)
        db.session.commit()
        print('Admin user created successfully')

if __name__ == '__main__':
    create_admin_user()
