import hashlib


class Node(object):
    class Successor(object):
        """
        List manager for successor references.
        It is responsible that entries in the successor list and first finger are consistent.
        """

        def __init__(self, finger_table):
            self.list = []
            self._backup = None
            self.max_entries = 3
            self._finger_table = finger_table

        def set(self, new_successor, replace_old=True):
            if len(self.list) == 0:
                self.list = [new_successor]
            else:
                self.list[0] = new_successor
            self._correct_finger_table(new_successor, replace_old=replace_old)

        def get(self):
            return self.list[0]

        def update_others(self, successors, ignore_keys=-1):
            if successors:
                self._backup = self.list
                self.list = [self.get()] + [x for x in successors if x['node_id'] != ignore_keys]
                del self.list[self.max_entries:]

        def delete_first(self):
            del self.list[0]
            self._correct_finger_table(self.get(), replace_old=True)

        def count_occurrence(self, successor):
            return self.list.count(successor)

        def _correct_finger_table(self, new_successor, replace_old=False, offset=0):
            old_peer = self._finger_table[offset].get("successor")
            self._finger_table[offset]["successor"] = new_successor

            if old_peer is None or not replace_old:
                return

            for entry in self._finger_table[offset + 1]:
                if entry and entry["successor"].get("node_id") == old_peer["node_id"]:
                    entry["successor"] = new_successor
                else:
                    break

    def __init__(self, username, clouds):
        self.ring = hashlib.sha256(username).hexdigest()
        self.username = username
        self.clouds = clouds
        self.successors = []
        self.finger_table = []
        self.generate_id()

    def create(self):
        if len(self.successors) == 0:
            self.successors = [self.id]
        else:
            self.successors[0] = self.id
        self.predecessor = None

    def generate_id(self):
        """Generate node's id by hashing username and cloud addresses"""
        ip_addresses = self.username
        for cloud in self.clouds:
            ip_addresses += cloud.address
        self.id = int(hashlib.sha256(ip_addresses).hexdigest(), 16)

    def init_finger_table(self):
        pass

    def update_finger_table(self):
        pass

    def update_successor(self):
        pass

    def update_successor_list(self):
        pass

    def check_predecessor(self):
        pass

    def find_successor(self):
        pass

    def as_dict(self):
        pass

    def join(self):
        pass

    def closest_preceding_node(self, node_id, key_id):
        pass

    def stabilize(self):
        pass

    def leave(self):
        pass

    def fix_fingers(self):
        pass

    def notify(self):
        pass
