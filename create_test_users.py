from app import app, db
from models.user import User
from models.class_ import Class

def create_test_users():
    with app.app_context():
        # First, clear existing data
        print("\nClearing existing data...")
        User.query.delete()
        Class.query.delete()
        db.session.commit()
        
        # Create test teacher
        print("\nCreating teacher account...")
        teacher = User(
            username='teacher1',
            email='teacher1@example.com',
            is_teacher=True
        )
        teacher.set_password('teacher123')
        db.session.add(teacher)
        db.session.commit()
        print(f"Teacher created with ID: {teacher.id}")
        
        # Create a class
        print("\nCreating class...")
        math_class = Class(
            name='Math 101',
            description='Introduction to Mathematics',
            teacher_id=teacher.id
        )
        db.session.add(math_class)
        db.session.commit()
        print(f"Class created with ID: {math_class.id}")
        
        # Create test students
        print("\nCreating student accounts...")
        students = [
            {
                'username': 'student1',
                'email': 'student1@example.com',
                'password': 'student123'
            },
            {
                'username': 'student2',
                'email': 'student2@example.com',
                'password': 'student123'
            }
        ]
        
        created_students = []
        for student_data in students:
            student = User(
                username=student_data['username'],
                email=student_data['email'],
                is_teacher=False,
                class_id=math_class.id,
                teacher_id=teacher.id
            )
            student.set_password(student_data['password'])
            db.session.add(student)
            created_students.append(student)
        
        db.session.commit()
        
        # Verify the data
        print("\nVerifying data...")
        teacher = User.query.filter_by(username='teacher1').first()
        if teacher:
            print(f"\nTeacher verification:")
            print(f"ID: {teacher.id}")
            print(f"Username: {teacher.username}")
            print(f"Is Teacher: {teacher.is_teacher}")
            print(f"Number of classes: {teacher.classes.count()}")
            print(f"Number of students: {teacher.students.count()}")
        
        math_class = Class.query.filter_by(name='Math 101').first()
        if math_class:
            print(f"\nClass verification:")
            print(f"ID: {math_class.id}")
            print(f"Name: {math_class.name}")
            print(f"Teacher ID: {math_class.teacher_id}")
            print(f"Number of students: {math_class.students.count()}")
        
        print("\nStudent verification:")
        for student in User.query.filter_by(is_teacher=False).all():
            print(f"\nStudent: {student.username}")
            print(f"ID: {student.id}")
            print(f"Teacher ID: {student.teacher_id}")
            print(f"Class ID: {student.class_id}")
        
        print("\nTest accounts created successfully!")
        print("\nTeacher Account:")
        print("----------------")
        print(f"Username: {teacher.username}")
        print(f"Password: teacher123")
        print(f"Email: {teacher.email}")
        
        print("\nStudent Accounts:")
        print("----------------")
        for student_data in students:
            print(f"\nUsername: {student_data['username']}")
            print(f"Password: {student_data['password']}")
            print(f"Email: {student_data['email']}")
        
        print("\nClass created:")
        print("----------------")
        print(f"Name: {math_class.name}")
        print(f"Description: {math_class.description}")
        print(f"Teacher: {teacher.username}")

if __name__ == '__main__':
    create_test_users()
