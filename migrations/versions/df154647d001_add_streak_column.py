"""Add streak column

Revision ID: df154647d001
Revises: 868a910249be
Create Date: 2025-01-04 18:48:09.868863

"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "df154647d001"
down_revision = "868a910249be"
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table("task", schema=None) as batch_op:
        batch_op.add_column(
            sa.Column(
                "streak", sa.Integer(), nullable=False, server_default=sa.text("0")
            )
        )

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table("task", schema=None) as batch_op:
        batch_op.drop_column("streak")

    # ### end Alembic commands ###
