"""empty message

Revision ID: 3cde77c2297e
Revises: 
Create Date: 2019-05-12 22:55:24.923507

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '3cde77c2297e'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('blacklist_token',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('token', sa.String(length=255), nullable=False),
    sa.Column('blacklisted_on', sa.DateTime(), nullable=False),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('token')
    )
    op.create_table('grounds',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('source_id', sa.Integer(), nullable=False),
    sa.Column('name', sa.String(length=255), nullable=False),
    sa.Column('district', sa.String(length=255), nullable=False),
    sa.Column('address', sa.String(length=255), nullable=False),
    sa.Column('website', sa.String(length=255), nullable=True),
    sa.Column('hasMusic', sa.Boolean(), nullable=False),
    sa.Column('hasWifi', sa.Boolean(), nullable=False),
    sa.Column('hasToilet', sa.Boolean(), nullable=False),
    sa.Column('hasEatery', sa.Boolean(), nullable=False),
    sa.Column('hasDressingRoom', sa.Boolean(), nullable=False),
    sa.Column('hasLighting', sa.Boolean(), nullable=False),
    sa.Column('paid', sa.Boolean(), nullable=False),
    sa.Column('latitude', sa.Float(), nullable=False),
    sa.Column('longitude', sa.Float(), nullable=False),
    sa.Column('create_at', sa.DateTime(), nullable=False),
    sa.Column('modified_at', sa.DateTime(), nullable=False),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('source_id')
    )
    op.create_table('users',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('email', sa.String(length=255), nullable=False),
    sa.Column('password', sa.String(length=255), nullable=False),
    sa.Column('name', sa.Text(), nullable=False),
    sa.Column('surname', sa.Text(), nullable=False),
    sa.Column('birthday', sa.DateTime(), nullable=False),
    sa.Column('image_url', sa.Text(), nullable=True),
    sa.Column('rating', sa.Integer(), nullable=False),
    sa.Column('registered_on', sa.DateTime(), nullable=False),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('email')
    )
    op.create_table('events',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('owner_id', sa.Integer(), nullable=True),
    sa.Column('activity', sa.Enum('easy_training', 'football', 'hockey', 'basketball', 'skating', 'ice_skating', 'workout', 'yoga', 'box', name='activity'), nullable=False),
    sa.Column('type', sa.Enum('training', 'match', 'tourney', name='eventtype'), nullable=False),
    sa.Column('participants_level', sa.Enum('beginner', 'average', 'experienced', 'expert', 'any', name='eventparticipantslevel'), nullable=False),
    sa.Column('participants_age_from', sa.Integer(), nullable=False),
    sa.Column('participants_age_to', sa.Integer(), nullable=False),
    sa.Column('ground_id', sa.Integer(), nullable=True),
    sa.Column('title', sa.Text(), nullable=False),
    sa.Column('description', sa.Text(), nullable=True),
    sa.Column('canceled', sa.Boolean(), nullable=False),
    sa.Column('begin_at', sa.DateTime(), nullable=False),
    sa.Column('end_at', sa.DateTime(), nullable=False),
    sa.Column('create_at', sa.DateTime(), nullable=False),
    sa.Column('modified_at', sa.DateTime(), nullable=False),
    sa.ForeignKeyConstraint(['ground_id'], ['grounds.id'], ),
    sa.ForeignKeyConstraint(['owner_id'], ['users.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('groundactivities',
    sa.Column('ground_id', sa.Integer(), nullable=False),
    sa.Column('activity', sa.Enum('easy_training', 'football', 'hockey', 'basketball', 'skating', 'ice_skating', 'workout', 'yoga', 'box', name='activity'), nullable=False),
    sa.ForeignKeyConstraint(['ground_id'], ['grounds.id'], ),
    sa.PrimaryKeyConstraint('ground_id', 'activity')
    )
    op.create_table('userratings',
    sa.Column('rated_user_id', sa.Integer(), nullable=False),
    sa.Column('rated_by_user_id', sa.Integer(), nullable=False),
    sa.ForeignKeyConstraint(['rated_by_user_id'], ['users.id'], ),
    sa.ForeignKeyConstraint(['rated_user_id'], ['users.id'], ),
    sa.PrimaryKeyConstraint('rated_user_id', 'rated_by_user_id')
    )
    op.create_table('eventmessages',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('event_id', sa.Integer(), nullable=True),
    sa.Column('sender_id', sa.Integer(), nullable=True),
    sa.Column('text', sa.Text(), nullable=False),
    sa.Column('create_at', sa.DateTime(), nullable=False),
    sa.ForeignKeyConstraint(['event_id'], ['events.id'], ),
    sa.ForeignKeyConstraint(['sender_id'], ['users.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('tourneyevents',
    sa.Column('event_id', sa.Integer(), nullable=False),
    sa.ForeignKeyConstraint(['event_id'], ['events.id'], ),
    sa.PrimaryKeyConstraint('event_id')
    )
    op.create_table('teams',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('max_participants', sa.Integer(), nullable=False),
    sa.Column('tourney_id', sa.Integer(), nullable=True),
    sa.Column('create_at', sa.DateTime(), nullable=False),
    sa.Column('modified_at', sa.DateTime(), nullable=False),
    sa.ForeignKeyConstraint(['tourney_id'], ['tourneyevents.event_id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('matchevents',
    sa.Column('event_id', sa.Integer(), nullable=False),
    sa.Column('team_a_id', sa.Integer(), nullable=True),
    sa.Column('team_b_id', sa.Integer(), nullable=True),
    sa.Column('team_a_score', sa.Integer(), nullable=True),
    sa.Column('team_b_score', sa.Integer(), nullable=True),
    sa.ForeignKeyConstraint(['event_id'], ['events.id'], ),
    sa.ForeignKeyConstraint(['team_a_id'], ['teams.id'], ),
    sa.ForeignKeyConstraint(['team_b_id'], ['teams.id'], ),
    sa.PrimaryKeyConstraint('event_id')
    )
    op.create_table('teamparticipants',
    sa.Column('team_id', sa.Integer(), nullable=False),
    sa.Column('paricipant_id', sa.Integer(), nullable=False),
    sa.ForeignKeyConstraint(['paricipant_id'], ['users.id'], ),
    sa.ForeignKeyConstraint(['team_id'], ['teams.id'], ),
    sa.PrimaryKeyConstraint('team_id', 'paricipant_id')
    )
    op.create_table('trainingevents',
    sa.Column('event_id', sa.Integer(), nullable=False),
    sa.Column('team_id', sa.Integer(), nullable=True),
    sa.ForeignKeyConstraint(['event_id'], ['events.id'], ),
    sa.ForeignKeyConstraint(['team_id'], ['teams.id'], ),
    sa.PrimaryKeyConstraint('event_id')
    )
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('trainingevents')
    op.drop_table('teamparticipants')
    op.drop_table('matchevents')
    op.drop_table('teams')
    op.drop_table('tourneyevents')
    op.drop_table('eventmessages')
    op.drop_table('userratings')
    op.drop_table('groundactivities')
    op.drop_table('events')
    op.drop_table('users')
    op.drop_table('grounds')
    op.drop_table('blacklist_token')
    # ### end Alembic commands ###