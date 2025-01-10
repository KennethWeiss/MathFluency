"""Reset alembic version

Revision ID: reset_alembic_version
Revises: 
Create Date: 2025-01-10 11:00:24.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'reset_alembic_version'
down_revision = None
branch_labels = None
depends_on = None

def upgrade():
    # Delete all entries from alembic_version table
    op.execute('DELETE FROM alembic_version')
    
    # Insert our new base revision
    op.execute("INSERT INTO alembic_version (version_num) VALUES ('reset_alembic_version')")

def downgrade():
    pass
