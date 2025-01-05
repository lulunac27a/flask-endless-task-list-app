"""Add daily streak column

Revision ID: c0fcd66c3df6
Revises: 5e8982aea1ef
Create Date: 2025-01-04 18:51:36.383519

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'c0fcd66c3df6'
down_revision = '5e8982aea1ef'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('user', schema=None) as batch_op:
        batch_op.add_column(sa.Column('last_completion_date', sa.Date(), nullable=False))
        batch_op.add_column(sa.Column('daily_streak', sa.Integer(), nullable=False))

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('user', schema=None) as batch_op:
        batch_op.drop_column('daily_streak')
        batch_op.drop_column('last_completion_date')

    # ### end Alembic commands ###
