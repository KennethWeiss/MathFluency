from app import app, db
from models.user import User

def update_teacher_privileges():
    with app.app_context():
        teacher = User.query.filter_by(username='teacher1').first()
        if teacher:
            teacher.is_teacher = True
            db.session.commit()
            print(f'Updated teacher privileges for: {teacher.username}')
        else:
            print('Teacher1 user not found')

if __name__ == '__main__':
    update_teacher_privileges()
