from sqlalchemy import text
from app.db.session import engine, Base
from app.models import Artist, Playlist, Snapshot, Placement


def init_db():
    Base.metadata.create_all(bind=engine)
    # Add total_tracks to placements if missing (existing DBs)
    try:
        with engine.begin() as conn:
            conn.execute(text("ALTER TABLE placements ADD COLUMN total_tracks INTEGER"))
    except Exception:
        pass  # Column already exists or DB doesn't support ALTER


if __name__ == "__main__":
    init_db()
    print("Database tables created successfully!")
