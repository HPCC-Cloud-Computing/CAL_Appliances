class Finger(object):
    def __init__(self, node_id, index, size, successor=None):
        self.start = (node_id + 2 ** index) % size
        self.successor = successor
        self.weight = 1
