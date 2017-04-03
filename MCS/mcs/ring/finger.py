from ring import RING_SIZE


class Finger(object):
    def __init__(self, node_id, index, successor=None):
        self.start = (node_id + 2 ** index) % RING_SIZE
        self.successor = successor
        self.weight = 1
