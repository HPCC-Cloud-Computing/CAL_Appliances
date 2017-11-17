import os
import uuid
from sqlalchemy import Table, Column, Integer, Numeric, String
from sqlalchemy import Column, DateTime, String, Integer, ForeignKey, func
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.orm import relationship, backref
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()


# Ring table
class Ring(Base):
    __tablename__ = 'ring'

    # ring id, in uuid string format
    id = Column(String(255), primary_key=True)
    # ring name
    name = Column(String(255), nullable=False)
    # ring version
    version = Column(Integer, nullable=False)
    # relation describes which clusters were received this ring
    updated_clusters = relationship(
        'Cluster',
        secondary='updated_ring_cluster'
    )


# Cluster table
class Cluster(Base):
    __tablename__ = 'cluster'

    # cluster id, in uuid string format
    id = Column(String(255), primary_key=True)
    # cluster name
    name = Column(String(255))
    # address
    address_ip = Column(String(255))
    address_port = Column(String(255))
    # relation describes these rings which were sent to this cluster
    updated_rings = relationship(
        'Ring',
        secondary='updated_ring_cluster'
    )


# table which show a specified ring was updated in which clusters
class UpdatedRingCluster(Base):
    __tablename__ = 'updated_ring_cluster'
    # ring id
    ring_id = Column(String(255), ForeignKey('ring.id'), primary_key=True)
    # cluster id
    cluster_id = Column(String(255), ForeignKey('cluster.id'),
                        primary_key=True)
    # ring = relationship(Ring, backref=backref("ring_assoc"))
    # cluster = relationship(Cluster, backref=backref("cluster_assoc"))
