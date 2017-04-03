import hashlib

FINGER_TABLE_SIZE = 5
RING_SIZE = 2 ** FINGER_TABLE_SIZE


class Ring(object):
    def __init__(self, username):
        self.id = int(hashlib.sha256(username).hexdigest(), 16) % RING_SIZE
        self.size = RING_SIZE
        self.nodes = []

    def generate_ring(self):
        pass
