"""empty message

Revision ID: 8029b7f9ac6a
Revises: 4f33945b8bcd
Create Date: 2016-07-12 19:54:29.868434

"""

# revision identifiers, used by Alembic.
revision = '8029b7f9ac6a'
down_revision = '4f33945b8bcd'

from alembic import op
import sqlalchemy as sa


def upgrade():
    ### commands auto generated by Alembic - please adjust! ###
    op.add_column('scraper', sa.Column('added_by', sa.Integer(), nullable=True), schema='sm_dev')
    op.create_foreign_key(None, 'scraper', 'user', ['added_by'], ['id'], source_schema='sm_dev', referent_schema='sm_dev')
    ### end Alembic commands ###


def downgrade():
    ### commands auto generated by Alembic - please adjust! ###
    op.drop_constraint(None, 'scraper', schema='sm_dev', type_='foreignkey')
    op.drop_column('scraper', 'added_by', schema='sm_dev')
    ### end Alembic commands ###
