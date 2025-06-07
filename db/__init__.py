from sqlalchemy import create_engine

from .models import Base
from config import load_config

config = load_config()


engine = create_engine(config['DATABASE_URL'], echo=False)


def init_db():
    """Init database"""
    Base.metadata.create_all(bind=engine)
