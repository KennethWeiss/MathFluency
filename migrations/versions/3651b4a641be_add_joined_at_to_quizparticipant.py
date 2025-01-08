"""Add joined_at to QuizParticipant

Revision ID: 3651b4a641be
Revises: 962473717647
Create Date: 2025-01-07 19:47:00.211586

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '3651b4a641be'
down_revision = '962473717647'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('quiz', schema=None) as batch_op:
        batch_op.alter_column('teacher_id',
               existing_type=sa.INTEGER(),
               nullable=False)
        batch_op.alter_column('operation',
               existing_type=sa.VARCHAR(length=20),
               nullable=False)
        batch_op.alter_column('duration',
               existing_type=sa.INTEGER(),
               nullable=False)

    with op.batch_alter_table('quiz_participant', schema=None) as batch_op:
        batch_op.add_column(sa.Column('joined_at', sa.DateTime(), nullable=True))
        batch_op.alter_column('quiz_id',
               existing_type=sa.INTEGER(),
               nullable=False)
        batch_op.alter_column('user_id',
               existing_type=sa.INTEGER(),
               nullable=False)

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('quiz_participant', schema=None) as batch_op:
        batch_op.alter_column('user_id',
               existing_type=sa.INTEGER(),
               nullable=True)
        batch_op.alter_column('quiz_id',
               existing_type=sa.INTEGER(),
               nullable=True)
        batch_op.drop_column('joined_at')

    with op.batch_alter_table('quiz', schema=None) as batch_op:
        batch_op.alter_column('duration',
               existing_type=sa.INTEGER(),
               nullable=True)
        batch_op.alter_column('operation',
               existing_type=sa.VARCHAR(length=20),
               nullable=True)
        batch_op.alter_column('teacher_id',
               existing_type=sa.INTEGER(),
               nullable=True)

    # ### end Alembic commands ###