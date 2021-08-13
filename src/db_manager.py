from sqlalchemy.types import BOOLEAN
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer, String, ForeignKey, Table, DateTime, create_engine

import datetime

Base = declarative_base()


class NewsItem(Base):
    __tablename__ = "news_item"

    id = Column(Integer, primary_key=True, autoincrement=True)
    url = Column(String, unique=True)
    title = Column(String)
    description = Column(String)
    publishing_time = Column(DateTime)
    is_approved = Column(BOOLEAN)
    scraping_time = Column(DateTime)

    def __init__(self, **kwargs):
        self.scraping_time = datetime.datetime.now()
        for k, v in kwargs.items():
            setattr(self, k, v)


# class User(Base):
#     __tablename__ = "user"
# 
#     id = Column(Integer, primary_key=True)
#     username = Column(String)
#     password_hash = Column(String)


class DBManager:
    def __init__(self):
        """Initialize database manager."""
        self.engine_config = 'sqlite:///values_db.db'
        self.engine = create_engine(self.engine_config)
        Base.metadata.create_all(self.engine)

    def get_session(self):
        """Return session for database."""
        Session = sessionmaker(bind=self.engine)
        return Session()
