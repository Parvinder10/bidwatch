"""
Database connection, session management, and schema initialization for BIDWATCH.
Supports both SQLite (default local) and PostgreSQL (production).
"""

import os
import sqlite3
from pathlib import Path
from typing import Optional, Union, Dict, Any, List
import pandas as pd
from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine, Connection

# Base directories
BASE_DIR = Path(__file__).resolve().parent.parent.parent
DEFAULT_DB_PATH = BASE_DIR / "data" / "processed" / "bidwatch.db"
DEFAULT_SCHEMA_PATH = BASE_DIR / "sql" / "schema.sql"

def get_database_url(custom_path: Optional[Union[str, Path]] = None) -> str:
    """Return database connection URL. Respects DATABASE_URL env var if set."""
    env_url = os.getenv("DATABASE_URL")
    if env_url:
        return env_url
    db_path = Path(custom_path) if custom_path else DEFAULT_DB_PATH
    db_path.parent.mkdir(parents=True, exist_ok=True)
    return f"sqlite:///{db_path.as_posix()}"

def get_engine(custom_path: Optional[Union[str, Path]] = None) -> Engine:
    """Create SQLAlchemy engine with appropriate pooling and pragmas."""
    url = get_database_url(custom_path)
    if url.startswith("sqlite"):
        engine = create_engine(url, connect_args={"check_same_thread": False})
    else:
        engine = create_engine(url, pool_pre_ping=True)
    return engine

def get_connection(custom_path: Optional[Union[str, Path]] = None) -> Connection:
    """Get an active SQLAlchemy connection."""
    return get_engine(custom_path).connect()

def initialize_database(
    schema_path: Optional[Union[str, Path]] = None,
    db_path: Optional[Union[str, Path]] = None,
    drop_existing: bool = False
) -> None:
    """Initialize relational database tables from schema.sql."""
    schema_file = Path(schema_path) if schema_path else DEFAULT_SCHEMA_PATH
    if not schema_file.exists():
        raise FileNotFoundError(f"Schema file not found at {schema_file}")
    
    with open(schema_file, "r", encoding="utf-8") as f:
        schema_sql = f.read()
    
    engine = get_engine(db_path)
    with engine.begin() as conn:
        if drop_existing:
            # Drop tables in reverse foreign key order
            drop_order = [
                "investigative_leads", "cancellations", "amendments", "awards",
                "bids", "tenders", "raw_suppliers", "suppliers", "buyers"
            ]
            for table in drop_order:
                conn.execute(text(f"DROP TABLE IF EXISTS {table};"))
        
        # SQLite executes scripts split by statements
        for statement in schema_sql.split(";"):
            clean_stmt = statement.strip()
            if clean_stmt:
                conn.execute(text(clean_stmt))

def query_df(query: str, params: Optional[Dict[str, Any]] = None, db_path: Optional[Union[str, Path]] = None) -> pd.DataFrame:
    """Execute SQL query and return a Pandas DataFrame."""
    engine = get_engine(db_path)
    with engine.connect() as conn:
        return pd.read_sql_query(text(query), conn, params=params)

def execute_dml(query: str, params: Optional[Dict[str, Any]] = None, db_path: Optional[Union[str, Path]] = None) -> int:
    """Execute INSERT/UPDATE/DELETE statement and return rowcount."""
    engine = get_engine(db_path)
    with engine.begin() as conn:
        result = conn.execute(text(query), params or {})
        return result.rowcount
