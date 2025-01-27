"""update_oauth_model

Revision ID: 04f3a6dcf636
Revises: 0e4a3b7acab3
Create Date: 2025-01-26 16:43:33.698120

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '04f3a6dcf636'
down_revision = '0e4a3b7acab3'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('flask_dance_oauth', schema=None) as batch_op:
        batch_op.add_column(sa.Column('provider_user_id', sa.String(length=256), nullable=False))
        batch_op.drop_column('created_at')

    with op.batch_alter_table('practice_attempt', schema=None) as batch_op:
        batch_op.alter_column('created_at',
               existing_type=sa.DATETIME(),
               nullable=False)

    with op.batch_alter_table('user', schema=None) as batch_op:
        batch_op.alter_column('is_teacher',
               existing_type=sa.BOOLEAN(),
               nullable=False)
        batch_op.alter_column('is_admin',
               existing_type=sa.BOOLEAN(),
               nullable=False)
        batch_op.alter_column('created_at',
               existing_type=sa.DATETIME(),
               nullable=False)

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('user', schema=None) as batch_op:
        batch_op.alter_column('created_at',
               existing_type=sa.DATETIME(),
               nullable=True)
        batch_op.alter_column('is_admin',
               existing_type=sa.BOOLEAN(),
               nullable=True)
        batch_op.alter_column('is_teacher',
               existing_type=sa.BOOLEAN(),
               nullable=True)

    with op.batch_alter_table('practice_attempt', schema=None) as batch_op:
        batch_op.alter_column('created_at',
               existing_type=sa.DATETIME(),
               nullable=True)

    with op.batch_alter_table('flask_dance_oauth', schema=None) as batch_op:
        batch_op.add_column(sa.Column('created_at', sa.DATETIME(), nullable=False))
        batch_op.drop_column('provider_user_id')

    # ### end Alembic commands ###
