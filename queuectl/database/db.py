from pathlib import Path

from sqlalchemy import MetaData, create_engine

BASE_DIR = Path(__file__).resolve().parents[2]
DATABASE_PATH = BASE_DIR / "queue.db"

engine = create_engine(
    f"sqlite:///{DATABASE_PATH}",
    connect_args={"check_same_thread": False},
    future=True,
)

metadata = MetaData()


def init_database():
    metadata.create_all(engine)