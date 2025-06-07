from sqlalchemy.orm import sessionmaker, scoped_session
from contextlib import contextmanager
from . import engine


SessionLocal = scoped_session(sessionmaker(
    autocommit=False, autoflush=False, bind=engine))


@contextmanager
def get_db_session():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
