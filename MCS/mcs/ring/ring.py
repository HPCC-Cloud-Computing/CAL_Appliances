import hashlib


class Ring(object):
    def __init__(self, username, size):
        self.id = int(hashlib.sha256(username).hexdigest(), 16) % size
        self.size = size
        self.nodes = []

    def generate_ring(self):
        pass
