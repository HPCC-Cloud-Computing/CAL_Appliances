import os
import uuid
from sqlalchemy import Table, Column, Integer, Numeric, String
from sqlalchemy import Column, DateTime, String, Integer, ForeignKey, func, Float, Boolean
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.orm import relationship, backref
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()


# Ring table, use to quick load ring to memcached

class ObjectInfo(Base):
    __tablename__ = 'object'
    # object name
    object_name = Column(String(255), primary_key=True, nullable=False)
    # account name
    account_name = Column(String(255), primary_key=True, nullable=False)
    # container name
    container_name = Column(String(255), primary_key=True, nullable=False)
    # total size, in bytes
    size = Column(Integer, nullable=False)
    # last_updated
    last_update = Column(DateTime, nullable=False)

    time_stamp = Column(DateTime, nullable=False)

    is_deleted = Column(Boolean, default=False)


from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

engine = create_engine('sqlite:///rings/container_db.sqlite')

Session = sessionmaker()
Session.configure(bind=engine)
Base.metadata.create_all(engine)
