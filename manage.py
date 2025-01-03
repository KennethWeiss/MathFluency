from flask.cli import FlaskGroup
from app import app, db
from models.user import User

cli = FlaskGroup(app)

@cli.command("create_admin")
def create_admin():
    """Create an admin user"""
    admin = User(
        username='admin',
        email='kennethgweiss@gmail.com'  # Replace with your email
    )
    admin.set_password('admin123')  # Replace with your desired password
    admin.is_admin = True
    db.session.add(admin)
    db.session.commit()
    print(f"Created admin user: {admin.email}")

if __name__ == '__main__':
    cli()
