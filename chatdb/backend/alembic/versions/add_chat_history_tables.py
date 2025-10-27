"""Add chat history tables

Revision ID: add_chat_history_tables
Revises: add_is_unique_column
Create Date: 2024-01-01 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql

# revision identifiers, used by Alembic.
revision = 'add_chat_history_tables'
down_revision = 'add_is_unique_column'
branch_labels = None
depends_on = None


def upgrade():
    # Create chatsession table
    op.create_table('chatsession',
        sa.Column('id', sa.String(255), nullable=False),
        sa.Column('title', sa.String(500), nullable=False),
        sa.Column('connection_id', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=True),
        sa.ForeignKeyConstraint(['connection_id'], ['dbconnection.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_chatsession_id'), 'chatsession', ['id'], unique=False)

    # Create chatmessage table
    op.create_table('chatmessage',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('session_id', sa.String(255), nullable=False),
        sa.Column('message_type', sa.String(50), nullable=False),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('message_metadata', sa.JSON(), nullable=True),
        sa.Column('region', sa.String(50), nullable=True),
        sa.Column('order_index', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.ForeignKeyConstraint(['session_id'], ['chatsession.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_chatmessage_id'), 'chatmessage', ['id'], unique=False)

    # Create chathistorysnapshot table
    op.create_table('chathistorysnapshot',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('session_id', sa.String(255), nullable=False),
        sa.Column('query', sa.Text(), nullable=False),
        sa.Column('response_data', sa.JSON(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.ForeignKeyConstraint(['session_id'], ['chatsession.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_chathistorysnapshot_id'), 'chathistorysnapshot', ['id'], unique=False)


def downgrade():
    # Drop tables in reverse order
    op.drop_index(op.f('ix_chathistorysnapshot_id'), table_name='chathistorysnapshot')
    op.drop_table('chathistorysnapshot')

    op.drop_index(op.f('ix_chatmessage_id'), table_name='chatmessage')
    op.drop_table('chatmessage')

    op.drop_index(op.f('ix_chatsession_id'), table_name='chatsession')
    op.drop_table('chatsession')
