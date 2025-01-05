"""Add number of days completed column

Revision ID: fa5ff0ea7eab
Revises: 5da7b534611d
Create Date: 2025-01-04 18:53:18.570172

"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "fa5ff0ea7eab"
down_revision = "5da7b534611d"
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table("user", schema=None) as batch_op:
        batch_op.add_column(
            sa.Column("days_completed", sa.Integer(), nullable=False))

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table("user", schema=None) as batch_op:
        batch_op.drop_column("days_completed")

    # ### end Alembic commands ###
