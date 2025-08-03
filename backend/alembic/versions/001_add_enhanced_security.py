"""Add enhanced security features

Revision ID: 001_enhanced_security
Revises: 
Create Date: 2024-01-01 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers
revision = '001_enhanced_security'
down_revision = None
branch_labels = None
depends_on = None

def upgrade():
    """Add enhanced security features to existing tables"""
    
    # Modify api_keys table for enhanced security
    op.add_column('api_keys', sa.Column('key_hash', sa.String(200), nullable=True))
    op.add_column('api_keys', sa.Column('key_prefix', sa.String(12), nullable=True))
    op.add_column('api_keys', sa.Column('allowed_ips', sa.Text(), nullable=True))
    op.add_column('api_keys', sa.Column('permissions', sa.Text(), nullable=True))
    
    # Create unique index on key_hash
    op.create_index('idx_api_keys_key_hash', 'api_keys', ['key_hash'], unique=True)
    
    # Migrate existing keys (if any) - this would need to be done carefully in production
    # For new installations, this migration is safe
    
    # Add performance indexes
    op.create_index('idx_users_email', 'users', ['email'])
    op.create_index('idx_users_username', 'users', ['username'])
    op.create_index('idx_api_keys_user_id', 'api_keys', ['user_id'])
    op.create_index('idx_prediction_history_user_id', 'prediction_history', ['user_id'])
    op.create_index('idx_prediction_history_created_at', 'prediction_history', ['created_at'])
    
    # Add constraint to ensure either key_hash or key is set (during migration period)
    # op.create_check_constraint('check_api_key_format', 'api_keys', 'key_hash IS NOT NULL OR key IS NOT NULL')

def downgrade():
    """Remove enhanced security features"""
    
    # Remove indexes
    op.drop_index('idx_prediction_history_created_at', 'prediction_history')
    op.drop_index('idx_prediction_history_user_id', 'prediction_history')
    op.drop_index('idx_api_keys_user_id', 'api_keys')
    op.drop_index('idx_users_username', 'users')
    op.drop_index('idx_users_email', 'users')
    op.drop_index('idx_api_keys_key_hash', 'api_keys')
    
    # Remove columns
    op.drop_column('api_keys', 'permissions')
    op.drop_column('api_keys', 'allowed_ips')
    op.drop_column('api_keys', 'key_prefix')
    op.drop_column('api_keys', 'key_hash')