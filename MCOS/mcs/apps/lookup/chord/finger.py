from django.conf import settings


class Finger(object):
    def __init__(self, node_id, index, node=None):
        self.start = (node_id + 2 ** index) % settings.RING_SIZE
        self.node = node
        self.weight = 1
