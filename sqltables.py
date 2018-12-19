from sqlalchemy import create_engine

engine = create_engine('sqlite:////Users/andpere/CDW/PycharmProjects/ProfanityBot/profanity.db',
                       connect_args={'check_same_thread': False})

# Allows us to take our objects and map to a row in the database.  Identity mapping
from sqlalchemy.orm import sessionmaker

Session = sessionmaker(bind=engine)
session = Session()

from sqlalchemy import Column, Integer, String

# Import declaritve base and
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()


# Creating Tables
class Profanity(Base):
    __tablename__ = "profanity"

    empid = Column(Integer, primary_key=True)
    roomid = Column(String(50))
    words = Column(String(50))


class Banlist(Base):
    __tablename__ = "banlist"

    empid = Column(Integer, primary_key=True)
    roomid = Column(String(50))
    user = Column(String(50))
    count = Column(Integer)


Base.metadata.create_all(engine)
