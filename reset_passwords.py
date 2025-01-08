from app import app, db
from models.user import User

def reset_user_passwords():
    with app.app_context():
        # Reset teacher1's password
        teacher = User.query.filter_by(username='teacher1').first()
        if teacher:
            teacher.set_password('teacher123')
            print(f'Reset password for user: {teacher.username}')
        else:
            # Create teacher1 if it doesn't exist
            teacher = User(
                username='teacher1',
                email='teacher1@example.com',
                is_teacher=True
            )
            teacher.set_password('teacher123')
            db.session.add(teacher)
            print(f'Created new teacher user: {teacher.username}')

        # Reset student1's password
        student = User.query.filter_by(username='student1').first()
        if student:
            student.set_password('student123')
            print(f'Reset password for user: {student.username}')
        else:
            # Create student1 if it doesn't exist
            student = User(
                username='student1',
                email='student1@example.com',
                is_teacher=False
            )
            student.set_password('student123')
            db.session.add(student)
            print(f'Created new student user: {student.username}')

        db.session.commit()
        print('All passwords have been reset/users created')

if __name__ == '__main__':
    reset_user_passwords()
