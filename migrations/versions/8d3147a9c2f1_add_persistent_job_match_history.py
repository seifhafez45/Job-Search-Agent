"""Add persistent job match history and skill-gap scores."""
from alembic import op
import sqlalchemy as sa


revision = "8d3147a9c2f1"
down_revision = "ca46c0634eb6"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column("skill_gap_reports", sa.Column("match_score", sa.Integer(), nullable=True))
    op.create_table(
        "job_matches",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("profile_id", sa.Integer(), nullable=False),
        sa.Column("external_id", sa.String(), nullable=False),
        sa.Column("title", sa.String(), nullable=False),
        sa.Column("company", sa.String(), nullable=True),
        sa.Column("location", sa.String(), nullable=True),
        sa.Column("url", sa.Text(), nullable=True),
        sa.Column("job_description_snapshot", sa.Text(), nullable=True),
        sa.Column("match_score", sa.Integer(), nullable=False),
        sa.Column("strengths", sa.Text(), nullable=False, server_default="[]"),
        sa.Column("weaknesses", sa.Text(), nullable=False, server_default="[]"),
        sa.Column("fit_summary", sa.Text(), nullable=True),
        sa.Column("search_keyword", sa.String(), nullable=True),
        sa.Column("search_country", sa.String(), nullable=True),
        sa.Column("is_remote", sa.Boolean(), nullable=True),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.ForeignKeyConstraint(["profile_id"], ["profiles.id"]),
    )
    op.create_index("ix_job_matches_user_id", "job_matches", ["user_id"])
    op.create_index("ix_job_matches_profile_id", "job_matches", ["profile_id"])


def downgrade():
    op.drop_index("ix_job_matches_profile_id", table_name="job_matches")
    op.drop_index("ix_job_matches_user_id", table_name="job_matches")
    op.drop_table("job_matches")
    op.drop_column("skill_gap_reports", "match_score")
