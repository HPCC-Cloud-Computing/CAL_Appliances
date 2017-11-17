import os
import uuid
from sqlalchemy import Table, Column, Integer, Numeric, String
from sqlalchemy import Column, DateTime, String, Integer, ForeignKey, func
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.orm import relationship, backref
from sqlalchemy.ext.declarative import declarative_base
from mcos.settings import shared_db_connection_url
from .models import Base, Cluster, Ring, UpdatedRingCluster


class SharedDatabaseConnection:
    def __init__(self):
        self.engine = create_engine(shared_db_connection_url)
        self.Session = sessionmaker()
        self.Session.configure(bind=self.engine)
        Base.metadata.create_all(self.engine)
        self.session = self.Session()

        # self.session = Session()

    def add_cluster_to_shared_database(self, cluster_id, cluster_name,
                                       address_ip, address_port):
        new_cluster_info = Cluster(id=cluster_id, name=cluster_name,
                                   address_ip=address_ip,
                                   address_port=address_port)
        self.session.add(new_cluster_info)
        self.session.commit()

    def get_cluster(self, cluster_id):
        data = self.session.query(Cluster).filter_by(
            id=str(cluster_id)).first()
        return data

    def get_ring_list(self):
        data = self.session.query(Ring).all()
        return data

    def get_cluster_list(self):
        return self.session.query(Cluster).all()

    def add_updated_cluster(self, ring, updated_cluster):
        ring.updated_clusters.append(updated_cluster)
        self.session.add(ring)
        self.session.commit()

    def close(self):
        self.session.close()
