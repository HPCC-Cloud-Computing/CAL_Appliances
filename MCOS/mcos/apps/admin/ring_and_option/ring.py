from random import shuffle

POWER_NUMBER = 12
REPLICA_FACTOR = 3


class RingCluster:
    def __init__(self, cluster_id, name, ip, port, weight):
        self.cluster_id = cluster_id
        self.name = name
        self.ip = ip
        self.port = port
        self.weight = weight
        self.part_number = 0

    def to_dict(self):
        return {
            'cluster_id': str(self.cluster_id),
            'name': self.name,
            'ip': self.ip,
            'port': self.port,
        }


class RingPartition:
    def __init__(self):
        self.cluster_refs = []

    def add_cluster_ref(self, cluster):
        self.cluster_refs.append(cluster)

    def to_dict(self):
        cluster_refs_list = []
        for cluster in self.cluster_refs:
            cluster_refs_list.append(str(cluster.cluster_id))
        return {
            'cluster_refs': cluster_refs_list
        }


# part : partition
class HashRing:
    def __init__(self, id=None, name=None, full_name=None, description=None, ring_type=None,
                 version=None, ring_clusters=None, replica_factor=REPLICA_FACTOR):
        self.id = id
        self.name = name
        self.full_name = full_name
        self.description = description
        self.ring_type = ring_type
        self.version = version
        self.ring_clusters = ring_clusters
        self.power_number = POWER_NUMBER
        self.replica_factor = replica_factor
        self.total_part = pow(2, POWER_NUMBER)
        self.total_part_frag = self.total_part * replica_factor
        self.total_cluster_weight = HashRing.calculate_total_weight(
            ring_clusters)
        self.frag_unit = \
            self.total_part_frag * 1.0 / self.total_cluster_weight
        self.set_cluster_frag_number(ring_clusters)
        part_condition, overweight_cluster = \
            self.check_part_number_condition(ring_clusters)
        if part_condition is False:
            raise Exception(
                'Cluster' + str(overweight_cluster.cluster_id) +
                ' is overweight: ' + str(overweight_cluster.weight) +
                ' - please resize it.')
        self.parts = []
        for i in range(0, self.total_part):
            self.parts.append(RingPartition())

    @staticmethod
    def calculate_total_weight(ring_clusters):
        total_weight = 0
        for cluster in ring_clusters:
            total_weight += cluster.weight
        return total_weight

    def check_part_number_condition(self, ring_clusters):
        for cluster in ring_clusters:
            if cluster.part_number > self.total_part:
                return False, cluster
        return True, None

    def set_cluster_frag_number(self, ring_clusters):
        cluster_number = len(ring_clusters)
        odd_part_number = self.total_part_frag
        for i in range(0, len(ring_clusters)):
            odd_part_number -= int(self.frag_unit * ring_clusters[i].weight)

        div_part_per_cluster = odd_part_number / cluster_number
        remain_part = odd_part_number - div_part_per_cluster * cluster_number
        for i in range(0, remain_part):
            ring_clusters[i].part_number = \
                int(self.frag_unit * ring_clusters[i].weight) + \
                div_part_per_cluster + 1
        for i in range(remain_part, len(ring_clusters)):
            ring_clusters[i].part_number = \
                int(self.frag_unit * ring_clusters[i].weight) + \
                div_part_per_cluster

    def assign_ref_cluster_to_part(self):
        ring_clusters = self.ring_clusters
        # initial first selected list for first cloud
        part_index_list = [i for i in range(0, self.total_part)]

        remain_part_index_list = [i for i in range(0, self.total_part)]
        shuffle(remain_part_index_list)
        for cluster in ring_clusters:
            if len(remain_part_index_list) < cluster.part_number:

                selected_part_index_list = remain_part_index_list
                pick_missing_parts = []
                for i in part_index_list:
                    if i not in selected_part_index_list:
                        pick_missing_parts.append(i)
                shuffle(pick_missing_parts)
                missing_node_number = cluster.part_number - \
                                      len(selected_part_index_list)
                old_selected_nodes = list(selected_part_index_list)
                selected_part_index_list.extend(
                    pick_missing_parts[0:missing_node_number])
                remain_part_index_list = pick_missing_parts[
                                         missing_node_number:]
                # according algorithm, these nodes in old_selected_nodes
                # (state of selected_nodes before extend to pick missing
                # nodes) must be append to new remain_nodes
                remain_part_index_list.extend(old_selected_nodes)
            else:
                selected_part_index_list = \
                    remain_part_index_list[0:cluster.part_number]
                remain_part_index_list = \
                    remain_part_index_list[cluster.part_number:]
            # get number of ring node  equals this cluster reference count
            for i in range(0, cluster.part_number):
                # set selected_node to reference to this cloud server,
                # with clusters[select_list[i]] is selected node
                selected_part = \
                    self.parts[selected_part_index_list[i]]
                selected_part.add_cluster_ref(cluster)
            selected_part_index_list = remain_part_index_list

    def to_dict(self):
        part_dict_list = []
        ring_clusters = {}
        for cluster in self.ring_clusters:
            ring_clusters[str(cluster.cluster_id)] = cluster.to_dict()
        for part in self.parts:
            part_dict_list.append(part.to_dict())
        ring_dict = {
            'id': self.id,
            'name': self.name,
            'full_name': self.full_name,
            'description': self.description,
            'ring_type': self.ring_type,
            'version': self.version,
            'ring_clusters': ring_clusters,
            'total_part': self.total_part,
            'power_number': self.power_number,
            'replica_factor': self.replica_factor,
            'total_cluster_weight': self.total_cluster_weight,
            'parts': part_dict_list
        }
        return ring_dict


# if __name__ == "__main__":
#     clusters = [
#         RingCluster('1', 'CAL-1', '127.0.0.1', '8001', 100),
#         RingCluster('2', 'CAL-2', '127.0.0.1', '8002', 100),
#         RingCluster('3', 'CAL-3', '127.0.0.1', '8003', 100),
#         RingCluster('1', 'CAL-1', '127.0.0.1', '8001', 100),
#         # RingCluster('2', 'CAL-2', '127.0.0.1', '8002', 100),
#         # RingCluster('3', 'CAL-3', '127.0.0.1', '8003', 100),
#
#         # RingCluster('4', 'CAL-4', '127.0.0.1', '8004', 500),
#         # RingCluster('1', 'CAL-1', '127.0.0.1', '8001', 1000),
#         # RingCluster('2', 'CAL-2', '127.0.0.1', '8002', 1000),
#         # RingCluster('3', 'CAL-3', '127.0.0.1', '8003', 1000),
#         # RingCluster('4', 'CAL-4', '127.0.0.1', '8004', 1000),
#         # RingCluster('5', 'CAL-5', '127.0.0.1', '8005', 15000),
#         # RingCluster('6', 'CAL-6', '127.0.0.1', '8006', 100),
#         # RingCluster('7', 'CAL-7', '127.0.0.1', '8007', 100),
#         # RingCluster('8', 'CAL-8', '127.0.0.1', '8008', 100),
#     ]
#     account_ring = HashRing(ring_clusters=clusters,replica_factor=3)
#     account_ring.assign_ref_cluster_to_part()
#     for cluster in account_ring.ring_clusters:
#         print(cluster.part_number)
#     ring_dict = account_ring.to_dict()
#     pass
