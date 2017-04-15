RING_SIZE =5


class Finger(object):
    def __init__(self, node_id, index, node=None):
        self.start = (node_id + 2 ** index) % RING_SIZE
        self.node = node
        self.weight = 1
