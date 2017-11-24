import os
import uuid
from sqlalchemy import Table, Column, Integer, Numeric, String
from sqlalchemy import Column, DateTime, String, Integer, ForeignKey, func, Float
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.orm import relationship, backref
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()


# Ring table, use to quick load ring to memcached

class ContainerInfo(Base):
    __tablename__ = 'container'
    # account name
    account_name = Column(String(255), primary_key=True, nullable=False)
    # container name
    container_name = Column(String(255), primary_key=True, nullable=False)
    # object count
    object_count = Column(Integer, nullable=False)
    # total size, in MB
    size = Column(Float, nullable=False)
    # ring type
    date_created = Column(DateTime, nullable=False)


from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

engine = create_engine('sqlite:///rings/account_db.sqlite')

Session = sessionmaker()
Session.configure(bind=engine)
Base.metadata.create_all(engine)
