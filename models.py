import json
import os
from datetime import datetime

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer, String, Text, create_engine
from sqlalchemy.orm import declarative_base, relationship, sessionmaker


Base = declarative_base()


def _normalize_database_url() -> str:
    url = os.getenv("DATABASE_URL", os.getenv("POSTGRES_URL", "sqlite:///./app.db"))
    if url.startswith("postgresql+asyncpg://"):
        url = url.replace("postgresql+asyncpg://", "postgresql+psycopg://", 1)
    elif url.startswith("postgres://"):
        url = url.replace("postgres://", "postgresql+psycopg://", 1)
    return url


DATABASE_URL = _normalize_database_url()

connect_args = {}
if not DATABASE_URL.startswith("sqlite"):
    lower_url = DATABASE_URL.lower()
    if "localhost" not in lower_url and "127.0.0.1" not in lower_url:
        connect_args = {"sslmode": "require"}

engine = create_engine(DATABASE_URL, connect_args=connect_args, future=True)
SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)


class MpPlanSnapshot(Base):
    __tablename__ = "mp_plan_snapshots"

    id = Integer().with_variant(Integer, "sqlite")
    id = __import__("sqlalchemy").Column(Integer, primary_key=True, index=True)
    name = __import__("sqlalchemy").Column(String(120), nullable=False)
    query = __import__("sqlalchemy").Column(Text, nullable=False)
    preferences_json = __import__("sqlalchemy").Column(Text, nullable=False, default="{}")
    summary = __import__("sqlalchemy").Column(Text, nullable=False, default="")
    score = __import__("sqlalchemy").Column(Float, nullable=False, default=0.0)
    brief_json = __import__("sqlalchemy").Column(Text, nullable=False, default="{}")
    weekly_board_json = __import__("sqlalchemy").Column(Text, nullable=False, default="[]")
    grocery_basket_json = __import__("sqlalchemy").Column(Text, nullable=False, default="[]")
    prep_steps_json = __import__("sqlalchemy").Column(Text, nullable=False, default="[]")
    total_cost = __import__("sqlalchemy").Column(Float, nullable=False, default=0.0)
    total_protein = __import__("sqlalchemy").Column(Integer, nullable=False, default=0)
    created_at = __import__("sqlalchemy").Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = __import__("sqlalchemy").Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    meals = relationship("MpSnapshotMeal", back_populates="snapshot", cascade="all, delete-orphan")


class MpSnapshotMeal(Base):
    __tablename__ = "mp_snapshot_meals"

    id = __import__("sqlalchemy").Column(Integer, primary_key=True, index=True)
    snapshot_id = __import__("sqlalchemy").Column(Integer, ForeignKey("mp_plan_snapshots.id"), nullable=False, index=True)
    day_label = __import__("sqlalchemy").Column(String(20), nullable=False)
    meal_slot = __import__("sqlalchemy").Column(String(20), nullable=False)
    recipe_name = __import__("sqlalchemy").Column(String(140), nullable=False)
    dietary_tags = __import__("sqlalchemy").Column(String(120), nullable=False, default="")
    prep_minutes = __import__("sqlalchemy").Column(Integer, nullable=False, default=20)
    cost_per_serving = __import__("sqlalchemy").Column(Float, nullable=False, default=5.0)
    protein_g = __import__("sqlalchemy").Column(Integer, nullable=False, default=25)
    carbs_g = __import__("sqlalchemy").Column(Integer, nullable=False, default=30)
    fat_g = __import__("sqlalchemy").Column(Integer, nullable=False, default=10)
    portions = __import__("sqlalchemy").Column(Integer, nullable=False, default=2)
    rationale = __import__("sqlalchemy").Column(Text, nullable=False, default="")
    is_swapped = __import__("sqlalchemy").Column(Boolean, nullable=False, default=False)

    snapshot = relationship("MpPlanSnapshot", back_populates="meals")


def create_all() -> None:
    Base.metadata.create_all(bind=engine)


def dumps_json(data) -> str:
    return json.dumps(data, ensure_ascii=False)


def loads_json(data: str, fallback):
    try:
        return json.loads(data)
    except Exception:
        return fallback
