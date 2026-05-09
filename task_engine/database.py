from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from task_engine.config import DATABASE_URL

# SQLite needs check_same_thread=False; PostgreSQL does not
_connect_args = {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}

engine = create_engine(DATABASE_URL, connect_args=_connect_args, echo=False)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def get_db():
    """FastAPI dependency: yields a database session and closes it after use."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def _migrate_sqlite():
    """Add any missing columns to existing SQLite tables. Safe to run on every startup."""
    if not DATABASE_URL.startswith("sqlite"):
        return  # PostgreSQL handles migrations differently

    import sqlite3
    db_path = DATABASE_URL.replace("sqlite:///", "").replace("sqlite://", "")
    if not db_path or db_path == ".":
        return

    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # Columns to add if missing: (table, column, type, default)
        pending = [
            ("tasks", "last_run_status", "VARCHAR(16)", "NULL"),
        ]

        for table, col, col_type, default in pending:
            existing = [row[1] for row in cursor.execute(f"PRAGMA table_info({table})").fetchall()]
            if col not in existing:
                cursor.execute(f"ALTER TABLE {table} ADD COLUMN {col} {col_type} DEFAULT {default}")
                conn.commit()
                import logging
                logging.getLogger(__name__).info(f"Migration: added column {table}.{col}")

        conn.close()
    except Exception as e:
        import logging
        logging.getLogger(__name__).warning(f"Migration warning: {e}")


def init_db():
    """Create all tables and apply any pending column migrations."""
    from task_engine import models  # noqa: F401 — registers models with Base
    Base.metadata.create_all(bind=engine)
    _migrate_sqlite()
