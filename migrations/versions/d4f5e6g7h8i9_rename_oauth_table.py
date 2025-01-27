"""rename oauth table

Revision ID: d4f5e6g7h8i9
Revises: ccfec45f97e7
Create Date: 2025-01-26 17:12:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'd4f5e6g7h8i9'
down_revision = 'ccfec45f97e7'
branch_labels = None
depends_on = None


def upgrade():
    # Rename the table
    op.rename_table('flask_dance_oauth', 'oauth')


def downgrade():
    # Rename it back if we need to downgrade
    op.rename_table('oauth', 'flask_dance_oauth')
