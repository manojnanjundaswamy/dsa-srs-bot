import os
from dotenv import load_dotenv
from pathlib import Path

# Load .env from the project root (parent of task_engine/)
load_dotenv(dotenv_path=Path(__file__).parent.parent / ".env")

# Database URL — default SQLite, override with DATABASE_URL env var for PostgreSQL:
#   DATABASE_URL=postgresql://user:pass@localhost:5432/task_engine
DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./tasks.db")

# Claude API key (shared with reminder_bot.py)
CLAUDE_API_KEY: str = os.getenv("ANTHROPIC_API_KEY") or os.getenv("CLAUDE_API_KEY") or ""

# API server settings
API_HOST: str = os.getenv("API_HOST", "127.0.0.1")
API_PORT: int = int(os.getenv("API_PORT", "8080"))
