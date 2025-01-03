from flask.cli import FlaskGroup
from app import app, db
from models.user import User
import os

cli = FlaskGroup(app)

@cli.command("create_admin")
def create_admin():
    """Create an admin user"""
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
    db.session.commit()
    print(f"Created admin user: {admin_email}")

if __name__ == '__main__':
    cli()
