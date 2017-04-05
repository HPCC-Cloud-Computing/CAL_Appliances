import hashlib

from finger import Finger
from mcs.apps.lookup.ring import RING_SIZE, FINGER_TABLE_SIZE
from utils import in_interval, decr


class Node(object):
    def __init__(self, username, clouds):
        self.ring = hashlib.sha256(username).hexdigest()
        self.username = username
        self.clouds = clouds
        self.finger_table = []
        self.generate_id()
        self._generate_finger_table()

    def create(self):
        self.successor = self
        self.predecessor = None

    def generate_id(self):
        """Generate node's id by hashing username and cloud addresses"""
        ip_addresses = self.username
        for cloud in self.clouds:
            ip_addresses += cloud.address
        self.id = int(hashlib.sha256(ip_addresses).hexdigest(), 16) % RING_SIZE

    def find_successor(self, id):
        """Ask node n to find id's successor"""
        node = self.find_predecessor(id)
        return node.successor

    def find_predecessor(self, id):
        """Ask node n to find id's precedecessor"""
        if id == self.id:
            return self.predecessor
        node = self
        while not in_interval(id, node.id,
                              node.successor.id, equal_right=True):
            node = node.closest_preceding_finger(id)
        return node

    def closest_preceding_finger(self, id):
        """Return closest finger preceding id"""
        for i in range(FINGER_TABLE_SIZE - 1, -1, -1):
            _node = self.finger_table[i].node
            if in_interval(_node.id, self.id, id):
                return _node
        return self

    def join(self, exist_node):
        """Node join the network with exist_node
        is an arbitrary in the network."""
        if exist_node:
            self.init_finger_table(exist_node)
            self.update_others()
            # Move keys in (predecessor, self] from successor
        else:
            # if n is the only node in the network
            for i in range(FINGER_TABLE_SIZE):
                self.finger_table[i].node = self
            self.predecessor = self

    def _generate_finger_table(self):
        for i in range(0, FINGER_TABLE_SIZE):
            _finger = Finger(self.id, i)
            self.finger_table.append(_finger)

    def init_finger_table(self, exist_node):
        """Initialize finger table of local node
        exist_node is an arbitrary node already in the network"""
        self.finger_table[0].node = \
            exist_node.find_successor(self.finger_table[0].start)
        self.successor = self.finger_table[0].node
        self.predecessor = self.successor.predecessor
        self.successor.predecessor = self
        self.predecessor.successor = self
        for i in range(FINGER_TABLE_SIZE - 1):
            if in_interval(self.finger_table[i + 1].start,
                           self.id, self.finger_table[i].node.id,
                           equal_left=True):
                self.finger_table[i + 1].node = self.finger_table[i].node
            else:
                self.finger_table[i + 1].node = \
                    exist_node.find_successor(self.finger_table[i + 1].start)

    def update_others(self):
        """Update all nodes whose finger table"""
        for i in range(FINGER_TABLE_SIZE):
            # Find last node p whose ith finger might be n
            prev = decr(self.id, 2 ** i)
            p = self.find_predecessor(prev)
            if prev == p.successor.id:
                p = p.successor
            p.update_finger_table(self, i)

    def update_finger_table(self, s, i):
        """If s is ith finger of n, update n's finger table with s"""
        if in_interval(s.id, self.id,
                       self.finger_table[i].node.id, equal_left=True):
            self.finger_table[i].node = s
            p = self.predecessor
            p.update_finger_table(s, i)

    def update_others_leave(self):
        for i in range(FINGER_TABLE_SIZE):
            prev = decr(self.id, 2 ** i)
            p = self.find_predecessor(prev)
            p.update_finger_table(self.successor, i)
