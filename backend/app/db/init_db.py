from sqlalchemy import text

from app.db.session import Base, engine
from app.models import Artist, Placement, Playlist, Snapshot, User


def init_db():
    Base.metadata.create_all(bind=engine)
    # Add total_tracks to placements if missing (existing DBs)
    try:
        with engine.begin() as conn:
            conn.execute(text("ALTER TABLE placements ADD COLUMN total_tracks INTEGER"))
    except Exception:
        pass  # Column already exists or DB doesn't support ALTER
    # Add user_id to artists if missing (existing DBs)
    try:
        with engine.begin() as conn:
            conn.execute(text("ALTER TABLE artists ADD COLUMN user_id INTEGER"))
    except Exception:
        pass  # Column already exists

    # Migration: allow same artist for different users (unique per user, not global)
    need_migrate = True
    try:
        with engine.begin() as conn:
            conn.execute(text("CREATE TABLE IF NOT EXISTS _migrations (name TEXT PRIMARY KEY)"))
        with engine.connect() as conn:
            r = conn.execute(text("SELECT 1 FROM _migrations WHERE name = 'artists_unique_per_user'")).fetchone()
            if r is not None:
                need_migrate = False
    except Exception:
        need_migrate = False

    if need_migrate:
        try:
            with engine.begin() as conn:
                conn.execute(text("PRAGMA foreign_keys=OFF"))
                conn.execute(text("""
                    CREATE TABLE artists_new (
                        id INTEGER NOT NULL PRIMARY KEY,
                        user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
                        spotify_artist_id VARCHAR NOT NULL,
                        name VARCHAR NOT NULL,
                        spotify_url VARCHAR NOT NULL,
                        image_url VARCHAR,
                        refresh_tier VARCHAR DEFAULT 'default',
                        created_at DATETIME,
                        updated_at DATETIME,
                        last_snapshot_at DATETIME
                    )
                """))
                conn.execute(text("CREATE UNIQUE INDEX uq_artist_user_spotify_id ON artists_new (user_id, spotify_artist_id)"))
                conn.execute(text("""
                    INSERT INTO artists_new (id, user_id, spotify_artist_id, name, spotify_url, image_url, refresh_tier, created_at, updated_at, last_snapshot_at)
                    SELECT id, user_id, spotify_artist_id, name, spotify_url, image_url, refresh_tier, created_at, updated_at, last_snapshot_at FROM artists
                """))
                conn.execute(text("DROP TABLE artists"))
                conn.execute(text("ALTER TABLE artists_new RENAME TO artists"))
                conn.execute(text("PRAGMA foreign_keys=ON"))
                conn.execute(text("INSERT INTO _migrations (name) VALUES ('artists_unique_per_user')"))
        except Exception:
            pass  # Already migrated or error


if __name__ == "__main__":
    init_db()
    print("Database tables created successfully!")
