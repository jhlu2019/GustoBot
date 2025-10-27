"""add description column to schemarelationship

Revision ID: add_description_column
Revises: 
Create Date: 2023-07-10 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'add_description_column'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # 添加 description 列到 schemarelationship 表
    op.add_column('schemarelationship', sa.Column('description', sa.Text(), nullable=True))


def downgrade():
    # 删除 description 列
    op.drop_column('schemarelationship', 'description')
