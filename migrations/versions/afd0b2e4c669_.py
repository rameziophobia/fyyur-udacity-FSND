"""empty message

Revision ID: afd0b2e4c669
Revises: 3b3a4682ba98
Create Date: 2020-11-23 18:27:59.914058

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'afd0b2e4c669'
down_revision = '3b3a4682ba98'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('artist', sa.Column('seeking_description', sa.String(length=120), nullable=True))
    op.add_column('artist', sa.Column('seeking_venue', sa.Boolean(), nullable=True))
    op.add_column('artist', sa.Column('website', sa.String(length=120), nullable=True))
    op.add_column('venue', sa.Column('seeking_description', sa.String(length=120), nullable=True))
    op.add_column('venue', sa.Column('seeking_talent', sa.Boolean(), nullable=True))
    op.add_column('venue', sa.Column('website', sa.String(length=120), nullable=True))
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('venue', 'website')
    op.drop_column('venue', 'seeking_talent')
    op.drop_column('venue', 'seeking_description')
    op.drop_column('artist', 'website')
    op.drop_column('artist', 'seeking_venue')
    op.drop_column('artist', 'seeking_description')
    # ### end Alembic commands ###
