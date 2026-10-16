from dotenv import load_dotenv
import os
from sqlalchemy import create_engine, text
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.orm import sessionmaker
load_dotenv()
DATABASE_URL = os.getenv("DATABASE_URL")
engine = create_async_engine(DATABASE_URL, echo = False)
AsyncSessionLocal = async_sessionmaker(autoflush=False, bind=engine, class_=AsyncSession, expire_on_commit=False)


TABLES = ["""
CREATE TABLE IF NOT EXISTS road_map(
id INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
user_id BIGINT NOT NULL,
is_active BOOLEAN,
google_tasklist_id VARCHAR(255),
goal_title VARCHAR(255) NOT NULL,
summary TEXT NOT NULL,
total_estimated_days INTEGER NOT NULL,
created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);""",
"""
CREATE TABLE IF NOT EXISTS phase_overview(
    id INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    phase_number INTEGER NOT NULL,
    week_number INTEGER,
    phase_title VARCHAR(255) NOT NULL,
    phase_description VARCHAR(255),
    duration_days INTEGER NOT NULL,
    status VARCHAR(20) DEFAULT 'NOT_STARTED',
    key_outcome VARCHAR(255),
    road_map_id INTEGER REFERENCES road_map(id),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP

    );
""",
"""
CREATE TABLE IF NOT EXISTS phase_task(
    id INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    phase_number INTEGER NOT NULL,
    week_number INTEGER NOT NULL,
    is_completed BOOLEAN DEFAULT FALSE,
    week_start_date DATE,
    phase_overview_id INTEGER REFERENCES phase_overview(id),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP

    );
""",
"""
CREATE TABLE IF NOT EXISTS task(
    id INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    title VARCHAR(255) NOT NULL,
    notes TEXT,
    calendar_start TIMESTAMPTZ NOT NULL,
    calendar_end TIMESTAMPTZ NOT NULL,
    phase_task_id INTEGER REFERENCES phase_task (id),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP

    );
"""]
async def init_db():
    async with engine.begin() as conn:
        for stmt in TABLES:
            await conn.execute(text(stmt))