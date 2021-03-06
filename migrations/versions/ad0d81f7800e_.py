"""empty message

Revision ID: ad0d81f7800e
Revises: be42a074a67c
Create Date: 2017-11-13 19:28:55.900828

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'ad0d81f7800e'
down_revision = 'be42a074a67c'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('comments',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('body', sa.Text(), nullable=True),
    sa.Column('timestamp', sa.DateTime(), nullable=True),
    sa.Column('author_id', sa.Integer(), nullable=True),
    sa.Column('chapter_id', sa.Integer(), nullable=True),
    sa.ForeignKeyConstraint(['author_id'], ['users.id'], ),
    sa.ForeignKeyConstraint(['chapter_id'], ['chapters.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_comments_timestamp'), 'comments', ['timestamp'], unique=False)
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_index(op.f('ix_comments_timestamp'), table_name='comments')
    op.drop_table('comments')
    # ### end Alembic commands ###
