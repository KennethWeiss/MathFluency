"""Safe create all tables

Revision ID: safe_create_all_tables
Revises: 
Create Date: 2025-01-09 22:05:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.engine.reflection import Inspector


# revision identifiers, used by Alembic.
revision = 'safe_create_all_tables'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # Get database connection and inspector
    conn = op.get_bind()
    inspector = Inspector.from_engine(conn)
    existing_tables = inspector.get_table_names()

    # Force drop and recreate alembic_version table
    try:
        op.drop_table('alembic_version')
    except:
        pass
    
    op.create_table('alembic_version',
        sa.Column('version_num', sa.String(length=32), nullable=False),
        sa.PrimaryKeyConstraint('version_num')
    )
    op.execute("INSERT INTO alembic_version (version_num) VALUES ('safe_create_all_tables')")

    # Create active_session table if it doesn't exist
    if 'active_session' not in existing_tables:
        op.create_table('active_session',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('user_id', sa.Integer(), nullable=False),
            sa.Column('activity_type', sa.String(length=50), nullable=True),
            sa.Column('details', sa.String(length=255), nullable=True),
            sa.Column('last_active', sa.DateTime(), nullable=True),
            sa.ForeignKeyConstraint(['user_id'], ['user.id'], ),
            sa.PrimaryKeyConstraint('id')
        )

    # Create user table if it doesn't exist
    if 'user' not in existing_tables:
        op.create_table('user',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('username', sa.String(length=64), nullable=False),
            sa.Column('email', sa.String(length=120), nullable=False),
            sa.Column('password_hash', sa.String(length=256)),
            sa.Column('is_teacher', sa.Boolean()),
            sa.Column('is_admin', sa.Boolean()),
            sa.Column('created_at', sa.DateTime()),
            sa.Column('google_id', sa.String(length=256)),
            sa.Column('avatar_url', sa.String(length=256)),
            sa.Column('first_name', sa.String(length=64)),
            sa.Column('last_name', sa.String(length=64)),
            sa.PrimaryKeyConstraint('id'),
            sa.UniqueConstraint('email'),
            sa.UniqueConstraint('google_id'),
            sa.UniqueConstraint('username')
        )

    # Create class table if it doesn't exist
    if 'class' not in existing_tables:
        op.create_table('class',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('name', sa.String(length=100), nullable=False),
            sa.Column('description', sa.Text()),
            sa.Column('class_code', sa.String(length=7)),
            sa.Column('created_at', sa.DateTime()),
            sa.PrimaryKeyConstraint('id'),
            sa.UniqueConstraint('class_code')
        )

    # Create teacher_class table if it doesn't exist
    if 'teacher_class' not in existing_tables:
        op.create_table('teacher_class',
            sa.Column('teacher_id', sa.Integer(), nullable=False),
            sa.Column('class_id', sa.Integer(), nullable=False),
            sa.ForeignKeyConstraint(['class_id'], ['class.id'], ),
            sa.ForeignKeyConstraint(['teacher_id'], ['user.id'], ),
            sa.PrimaryKeyConstraint('teacher_id', 'class_id')
        )

    # Create student_class table if it doesn't exist
    if 'student_class' not in existing_tables:
        op.create_table('student_class',
            sa.Column('student_id', sa.Integer(), nullable=False),
            sa.Column('class_id', sa.Integer(), nullable=False),
            sa.ForeignKeyConstraint(['class_id'], ['class.id'], ),
            sa.ForeignKeyConstraint(['student_id'], ['user.id'], ),
            sa.PrimaryKeyConstraint('student_id', 'class_id')
        )


def downgrade():
    op.drop_table('active_session')
    op.drop_table('student_class')
    op.drop_table('teacher_class')
    op.drop_table('class')
    op.drop_table('user')
    op.drop_table('alembic_version')
