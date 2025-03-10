"""Add times completed column

Revision ID: 8f05b938c89f
Revises: df154647d001
Create Date: 2025-01-04 18:49:08.275615

"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "8f05b938c89f"
down_revision = "df154647d001"
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table("task", schema=None) as batch_op:
        batch_op.add_column(
            sa.Column(
                "times_completed",
                sa.Integer(),
                nullable=False,
                server_default=sa.text("0"),
            )
        )

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table("task", schema=None) as batch_op:
        batch_op.drop_column("times_completed")

    # ### end Alembic commands ###
