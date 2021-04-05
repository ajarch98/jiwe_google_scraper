from sqlalchemy import create_engine
from sqlalchemy import Column, Integer, String, ForeignKey, Table
from sqlalchemy.types import Date
from sqlalchemy.orm import relationship, backref, sessionmaker
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

attributes = Table(
    "attributes",
    Base.metadata,
    Column("value_id", Integer, ForeignKey("value.id")),
    Column("threat_id", Integer, ForeignKey("threat.id")),
    Column("country_id", Integer, ForeignKey("country.id")),
    Column("date_id", Integer, ForeignKey("date.id"))
)


class Value(Base):
    __tablename__ = "value"

    id = Column(Integer, primary_key=True)
    value = Column(Integer)


class Threat(Base):
    __tablename__ = "threat"

    id = Column(String, primary_key=True)
    name = Column(String)
    values = relationship(
        "Value",
        secondary=attributes,
        backref=backref("threat", uselist=False)
    )


class Country(Base):
    __tablename__ = "country"

    id = Column(Integer, primary_key=True)
    name = Column(String)
    values = relationship(
        "Value",
        secondary=attributes,
        backref=backref("country", uselist=False)
    )


class Date(Base):
    __tablename__ = "date"

    id = Column(Integer, primary_key=True)
    value = Column(Date, unique=True)
    values = relationship(
        "Value",
        secondary=attributes,
        backref=backref("date", uselist=False)
    )


class DbManager():
    """Class to create and handle database operations."""

    def __init__(self):
        """Initialize database manager."""
        self.engine_config = 'sqlite:///values_db.db'
        self.engine = create_engine(self.engine_config)
        Base.metadata.create_all(self.engine)

    def get_session(self):
        """Return session for database."""
        Session = sessionmaker(bind=self.engine)
        return Session()
