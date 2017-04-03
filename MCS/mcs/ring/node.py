import hashlib

from finger import Finger
from ring import RING_SIZE, FINGER_TABLE_SIZE


def in_interval(val, left, right, equal_left, equal_right):
    if (equal_left and val == left):
        return True

    if (equal_right and val == right):
        return True

    if (right > left):
        if (val > left and val < right):
            return True
        else:
            return False

    if (right < left):
        if (val < left):
            left = left - RING_SIZE
        else:
            if (val > left):
                right = right + RING_SIZE

        if (val > left and val < right):
            return True
        else:
            return False
    return True


class Node(object):
    def __init__(self, username, clouds):
        self.ring = hashlib.sha256(username).hexdigest()
        self.username = username
        self.clouds = clouds
        self.finger_table = []
        self.generate_id()

    def create(self):
        self.successor = self
        self.predecessor = None

    def generate_id(self):
        """Generate node's id by hashing username and cloud addresses"""
        ip_addresses = self.username
        for cloud in self.clouds:
            ip_addresses += cloud.address
        self.id = int(hashlib.sha256(ip_addresses).hexdigest(), 16) % RING_SIZE

    def init_finger_table(self, init_node):
        for i in range(0, FINGER_TABLE_SIZE):
            _finger = Finger(self.id, i)
            self.finger_table.append(_finger)
        self.finger_table[0].successor = init_node.find_successor(self.finger_table[0].start)
        self.successor = self.finger_table[0].successor
        self.predecessor = self.successor.predecessor
        self.successor.predecessor = self
        self.predecessor.successor = self

    def update_finger_table(self):
        pass

    def update_successor(self):
        pass

    def update_successor_list(self):
        pass

    def check_predecessor(self):
        pass

    def find_successor(self, node_id):
        pass

    def find_predecessor(self, node_id):
        if node_id == self.id:
            return self.predecessor
        node = self
        while not in_interval(node_id, node.id, node.successor.id):
            node = node.closest_preceding_node(node_id)
        return node

    def as_dict(self):
        pass

    def join(self):
        pass

    def closest_preceding_node(self, node_id):
        # for i in range(FINGER_TABLE_SIZE-1, -1, -1):
        #     finger = self.finger_table[i]
        #     if in_interval(finger.successor, self.id, node_id):
        #         return finger
        # return self
        pass

    def stabilize(self):
        pass

    def leave(self):
        pass

    def fix_fingers(self):
        pass

    def notify(self):
        pass
