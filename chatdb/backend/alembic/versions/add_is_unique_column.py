"""add is_unique column to schemacolumn

Revision ID: add_is_unique_column
Revises: add_description_column
Create Date: 2023-07-11 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'add_is_unique_column'
down_revision = 'add_description_column'
branch_labels = None
depends_on = None


def upgrade():
    # 添加 is_unique 列到 schemacolumn 表
    op.add_column('schemacolumn', sa.Column('is_unique', sa.Boolean(), nullable=True, server_default='0'))
    
    # 更新现有记录，将 is_unique 设置为 False
    op.execute("UPDATE schemacolumn SET is_unique = 0 WHERE is_unique IS NULL")
    
    # 将列设置为非空
    op.alter_column('schemacolumn', 'is_unique', nullable=False)


def downgrade():
    # 删除 is_unique 列
    op.drop_column('schemacolumn', 'is_unique')
