from app import app, db
from models.user import User
from models.class_ import Class, teacher_class
from sqlalchemy import text
from datetime import datetime

def create_test_users():
    with app.app_context():
        
        # Create test teachers
        print("\nCreating teacher accounts...")
        teachers = [
            {
                'username': 'teacher1',
                'email': 'teacher1@example.com',
                'password': 'teacher123'
            },
            {
                'username': 'teacher2',
                'email': 'teacher2@example.com',
                'password': 'teacher123'
            },
            {
                'username': 'teacher3',
                'email': 'teacher3@example.com',
                'password': 'teacher123'
            }
        ]
        
        created_teachers = []
        for teacher_data in teachers:
            teacher = User(
                username=teacher_data['username'],
                email=teacher_data['email'],
                is_teacher=True
            )
            teacher.set_password(teacher_data['password'])
            db.session.add(teacher)
            created_teachers.append(teacher)
            print(f"Teacher created: {teacher.username}")
        
        db.session.commit()
        
        # Create test classes
        print("\nCreating classes...")
        classes = [
            {
                'name': 'Math 101',
                'description': 'Introduction to Mathematics',
                'primary_teacher': created_teachers[0]
            },
            {
                'name': 'Math 201',
                'description': 'Intermediate Mathematics',
                'primary_teacher': created_teachers[1]
            },
            {
                'name': 'Math 301',
                'description': 'Advanced Mathematics',
                'primary_teacher': created_teachers[2]
            },
            {
                'name': 'Math Club',
                'description': 'Math enthusiasts club - multiple teachers',
                'primary_teacher': created_teachers[0]
            }
        ]
        
        created_classes = []
        for class_data in classes:
            print(f"Creating class: {class_data['name']}")
            class_ = Class(
                name=class_data['name'],
                description=class_data['description']
            )
            print("\n Add class to session...")
            db.session.add(class_)
            db.session.commit()  # Commit to get the class ID
            
            # Add primary teacher
            print("Add primary teacher...")
            class_.add_teacher(class_data['primary_teacher'])
            print("Commit primary teacher...")
            
            # For Math Club, add all teachers
            if class_data['name'] == 'Math Club':
                for teacher in created_teachers:
                    if teacher != class_data['primary_teacher']:
                        class_.add_teacher(teacher)
            
            created_classes.append(class_)
            print(f"Class created: {class_.name}")
        
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
            },
            {
                'username': 'student3',
                'email': 'student3@example.com',
                'password': 'student123'
            },
            {
                'username': 'student4',
                'email': 'student4@example.com',
                'password': 'student123'
            },
            {
                'username': 'student5',
                'email': 'student5@example.com',
                'password': 'student123'
            }
        ]
        
        created_students = []
        for student_data in students:
            student = User(
                username=student_data['username'],
                email=student_data['email'],
                is_teacher=False
            )
            student.set_password(student_data['password'])
            db.session.add(student)
            created_students.append(student)
            print(f"Student created: {student.username}")
        
        db.session.commit()
        
        # Enroll students in classes
        print("\nEnrolling students in classes...")
        
        # Math 101 - All students
        for student in created_students:
            created_classes[0].add_student(student)
        db.session.commit()
        print(f"Enrolled all students in {created_classes[0].name}")
        
        # Math 201 - First 3 students
        for student in created_students[:3]:
            created_classes[1].add_student(student)
        db.session.commit()
        print(f"Enrolled first 3 students in {created_classes[1].name}")
        
        # Math 301 - Last 2 students
        for student in created_students[3:]:
            created_classes[2].add_student(student)
        db.session.commit()
        print(f"Enrolled last 2 students in {created_classes[2].name}")
        
        # Math Club - Students 2, 3, and 4
        for student in created_students[1:4]:
            created_classes[3].add_student(student)
        db.session.commit()
        print(f"Enrolled students 2-4 in {created_classes[3].name}")
        
        print("\nTest data creation completed!")
        print("\nCreated accounts:")
        print("\nTeachers:")
        for teacher in teachers:
            print(f"Username: {teacher['username']}, Password: {teacher['password']}")
        print("\nStudents:")
        for student in students:
            print(f"Username: {student['username']}, Password: {student['password']}")

if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser()
    parser.add_argument('--production', action='store_true', 
                       help='Run in production mode (requires DATABASE_URL to be set)')
    args = parser.parse_args()
    
    if args.production:
        print("Running in production mode - creating test users")
        create_test_users()
    else:
        print("Running in development mode - creating test users")
        create_test_users()
