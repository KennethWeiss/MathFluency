"""Initial migration

Revision ID: d4f5e6g7h8i9
Revises: 
Create Date: 2025-02-24 20:45:58.072114

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'd4f5e6g7h8i9'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # Create User table
    op.create_table('user',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('email', sa.String(length=120), nullable=True),
        sa.Column('name', sa.String(length=120), nullable=True),
        sa.Column('role', sa.String(length=20), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('email')
    )

    # Create OAuth table
    op.create_table('oauth',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('provider', sa.String(length=50), nullable=False),
        sa.Column('provider_user_id', sa.String(length=256), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('token', sa.String(length=256), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['user.id'], ),
        sa.PrimaryKeyConstraint('id')
    )

    # Create Class table
    op.create_table('class',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=120), nullable=False),
        sa.Column('teacher_id', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['teacher_id'], ['user.id'], ),
        sa.PrimaryKeyConstraint('id')
    )

    # Create Standard table
    op.create_table('standard',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=120), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )

    # Create SubStandard table
    op.create_table('substandard',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('standard_id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=120), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(['standard_id'], ['standard.id'], ),
        sa.PrimaryKeyConstraint('id')
    )

    # Create Quiz table
    op.create_table('quiz',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('title', sa.String(length=120), nullable=False),
        sa.Column('creator_id', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('status', sa.String(length=20), nullable=True),
        sa.ForeignKeyConstraint(['creator_id'], ['user.id'], ),
        sa.PrimaryKeyConstraint('id')
    )

    # Create Assignment table
    op.create_table('assignment',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('title', sa.String(length=120), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('class_id', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('due_date', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['class_id'], ['class.id'], ),
        sa.PrimaryKeyConstraint('id')
    )

    # Create AssignmentProgress table
    op.create_table('assignment_progress',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('assignment_id', sa.Integer(), nullable=False),
        sa.Column('student_id', sa.Integer(), nullable=False),
        sa.Column('status', sa.String(length=20), nullable=True),
        sa.Column('started_at', sa.DateTime(), nullable=True),
        sa.Column('completed_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['assignment_id'], ['assignment.id'], ),
        sa.ForeignKeyConstraint(['student_id'], ['user.id'], ),
        sa.PrimaryKeyConstraint('id')
    )

    # Create PracticeAttempt table
    op.create_table('practice_attempt',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('student_id', sa.Integer(), nullable=False),
        sa.Column('assignment_id', sa.Integer(), nullable=True),
        sa.Column('problem_type', sa.String(length=50), nullable=False),
        sa.Column('problem', sa.String(length=256), nullable=False),
        sa.Column('answer', sa.String(length=256), nullable=False),
        sa.Column('student_answer', sa.String(length=256), nullable=True),
        sa.Column('is_correct', sa.Boolean(), nullable=True),
        sa.Column('time_taken', sa.Float(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['assignment_id'], ['assignment.id'], ),
        sa.ForeignKeyConstraint(['student_id'], ['user.id'], ),
        sa.PrimaryKeyConstraint('id')
    )

    # Create StudentStandardProgress table
    op.create_table('student_standard_progress',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('student_id', sa.Integer(), nullable=False),
        sa.Column('standard_id', sa.Integer(), nullable=False),
        sa.Column('mastery_level', sa.Float(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['standard_id'], ['standard.id'], ),
        sa.ForeignKeyConstraint(['student_id'], ['user.id'], ),
        sa.PrimaryKeyConstraint('id')
    )

    # Create StudentSubStandardProgress table
    op.create_table('student_substandard_progress',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('student_id', sa.Integer(), nullable=False),
        sa.Column('substandard_id', sa.Integer(), nullable=False),
        sa.Column('mastery_level', sa.Float(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['student_id'], ['user.id'], ),
        sa.ForeignKeyConstraint(['substandard_id'], ['substandard.id'], ),
        sa.PrimaryKeyConstraint('id')
    )


def downgrade():
    # Drop tables in reverse order of creation
    op.drop_table('student_substandard_progress')
    op.drop_table('student_standard_progress')
    op.drop_table('practice_attempt')
    op.drop_table('assignment_progress')
    op.drop_table('assignment')
    op.drop_table('quiz')
    op.drop_table('substandard')
    op.drop_table('standard')
    op.drop_table('class')
    op.drop_table('oauth')
    op.drop_table('user')
