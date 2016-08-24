"""empty message

Revision ID: 22f788327537
Revises: 669b1347d9df
Create Date: 2016-07-11 16:27:33.591965

"""

# revision identifiers, used by Alembic.
revision = '22f788327537'
down_revision = '669b1347d9df'

from alembic import op
import sqlalchemy as sa


def upgrade():
    ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('apikey', 'host', schema='sm_dev')
    ### end Alembic commands ###


def downgrade():
    ### commands auto generated by Alembic - please adjust! ###
    op.add_column('apikey', sa.Column('host', sa.VARCHAR(length=255), autoincrement=False, nullable=True), schema='sm_dev')
    ### end Alembic commands ###
