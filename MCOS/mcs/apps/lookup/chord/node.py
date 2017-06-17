import hashlib
import logging

from django.conf import settings

from lookup.chord.finger import Finger
from lookup.chord.utils import in_interval, decr

LOG = logging.getLogger(__name__)


class Node(object):
    """Abstract Node in Ring"""

    def __init__(self, username, id):
        """
        :param username (string):
        :param clouds (list): List of cloud object.
        """
        self.id = id
        self.username = username
        self.clouds = []
        self.finger_table = []
        self._generate_finger_table()

    def add_cloud_to_node(self, cloud):
        self.clouds.append(cloud)

    def successor(self):
        return self.finger_table[0].node

    def find_successor(self, id):
        """Ask node n to find id's successor"""
        LOG.debug('Node {} - Find successor for {}'.format(str(self.id), str(id)))
        if in_interval(id, self.predecessor.id, self.id, equal_right=True):
            return self
        node = self.find_predecessor(id)
        return node.successor()

    def find_predecessor(self, id):
        """Ask node n to find id's precedecessor"""
        LOG.debug('Node {} - Find predecessor for {}'.format(str(self.id), str(id)))
        if id == self.id:
            return self.predecessor
        node = self
        while not in_interval(id, node.id,
                              node.successor().id, equal_right=True):
            node = node.closest_preceding_finger(id)
        return node

    def closest_preceding_finger(self, id):
        """Return closest finger preceding id"""
        LOG.debug('Node {} - Get closest preceding finger for {}'.format(str(self.id), str(id)))
        for i in range(settings.FINGER_TABLE_SIZE - 1, -1, -1):
            _node = self.finger_table[i].node
            if _node and in_interval(_node.id, self.id, id):
                return _node
        return self

    def join(self, exist_node):
        """Node join the network with exist_node
        is an arbitrary in the network."""
        LOG.debug('Node {} - join to ring with node {}'.format(str(exist_node.id), str(self.id)))
        if self == exist_node:
            for i in range(settings.FINGER_TABLE_SIZE):
                self.finger_table[i].node = self
            self.predecessor = self
        else:
            self.init_finger_table(exist_node)
            self.update_others()
            # Move keys in (predecessor, self] from successor
            self.move_keys()

    def _generate_finger_table(self):
        """Generate finger's start in finger table"""
        for i in range(0, settings.FINGER_TABLE_SIZE):
            _finger = Finger(self.id, i)
            self.finger_table.append(_finger)

    def init_finger_table(self, exist_node):
        """Initialize finger table of local node
        exist_node is an arbitrary node already in the network"""
        LOG.debug('Node {} - Init finger table for {}'.format(str(exist_node.id), str(self.id)))
        self.finger_table[0].node = \
            exist_node.find_successor(self.finger_table[0].start)
        self.predecessor = self.successor().predecessor
        self.successor().predecessor = self
        self.predecessor.finger_table[0].node = self
        for i in range(settings.FINGER_TABLE_SIZE - 1):
            if in_interval(self.finger_table[i + 1].start,
                           self.id, self.finger_table[i].node.id,
                           equal_left=True):
                self.finger_table[i + 1].node = self.finger_table[i].node
            else:
                self.finger_table[i + 1].node = \
                    exist_node.find_successor(self.finger_table[i + 1].start)

    def update_others(self):
        """Update all nodes whose finger table"""
        LOG.debug('Node {} - Update others'.format(str(self.id)))
        for i in range(settings.FINGER_TABLE_SIZE):
            # Find last node p whose ith finger might be n
            prev = decr(self.id, 2 ** i)
            p = self.find_predecessor(prev)
            if prev == p.successor().id:
                p = p.successor()
            p.update_finger_table(self, i)

    def update_finger_table(self, s, i):
        """If s is ith finger of n, update n's finger table with s"""
        LOG.debug('Node {} - Update finger table for {}'.format(str(self.id), s.id))
        if in_interval(s.id, self.id,
                       self.finger_table[i].node.id,
                       equal_left=True) and self.id != s.id:
            self.finger_table[i].node = s
            p = self.predecessor
            p.update_finger_table(s, i)

    def update_others_leave(self):
        for i in range(settings.FINGER_TABLE_SIZE):
            prev = decr(self.id, 2 ** i)
            p = self.find_predecessor(prev)
            p.update_finger_table(self.successor(), i)

    def leave(self):
        """Leave ring"""
        # Not tested
        self.successor().predecessor = self.predecessor
        self.predecessor.finger_table[0].node = self.successor()
        self.update_others_leave()
        # Moe keys

    def move_keys(self):
        pass
