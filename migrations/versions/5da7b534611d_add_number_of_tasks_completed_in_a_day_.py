"""Add number of tasks completed in a day column

Revision ID: 5da7b534611d
Revises: c0fcd66c3df6
Create Date: 2025-01-04 18:52:22.404495

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '5da7b534611d'
down_revision = 'c0fcd66c3df6'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('user', schema=None) as batch_op:
        batch_op.add_column(sa.Column('daily_tasks_completed', sa.Integer(), nullable=False))

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('user', schema=None) as batch_op:
        batch_op.drop_column('daily_tasks_completed')

    # ### end Alembic commands ###
