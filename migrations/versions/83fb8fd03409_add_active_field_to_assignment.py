"""Add active field to Assignment

Revision ID: 83fb8fd03409
Revises: 164fa0ae891d
Create Date: 2024-12-31 15:04:16.987444

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '83fb8fd03409'
down_revision = '164fa0ae891d'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('assignment', schema=None) as batch_op:
        batch_op.add_column(sa.Column('active', sa.Boolean(), nullable=True))

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('assignment', schema=None) as batch_op:
        batch_op.drop_column('active')

    # ### end Alembic commands ###
