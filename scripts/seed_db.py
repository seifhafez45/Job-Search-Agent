"""
Dev-only helper: creates all tables from app/models/ (bypassing Alembic) for
quick local setup. Use Alembic migrations for anything beyond local dev.
Run: python -m scripts.seed_db
"""
from app.database import Base, engine
import app.models  # noqa: F401 ensures all models are registered on Base


def main():
    Base.metadata.create_all(bind=engine)
    print("All tables created.")


if __name__ == "__main__":
    main()
