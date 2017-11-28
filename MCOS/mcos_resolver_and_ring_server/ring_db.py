import os
import uuid
from sqlalchemy import Table, Column, Integer, Numeric, String
from sqlalchemy import Column, DateTime, String, Integer, ForeignKey, func, Boolean
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.orm import relationship, backref
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()


# Ring table, use to quick load ring to memcached

class Ring(Base):
    __tablename__ = 'ring'
    # ring_id
    id = Column(String(255), primary_key=True)
    # ring name
    name = Column(String(255), nullable=False)
    # ring version
    version = Column(Integer, nullable=False)
    # ring type
    ring_type = Column(Integer, nullable=False)



from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

engine = create_engine('sqlite:///rings/ring_db.sqlite')

Session = sessionmaker()
Session.configure(bind=engine)
Base.metadata.create_all(engine)
