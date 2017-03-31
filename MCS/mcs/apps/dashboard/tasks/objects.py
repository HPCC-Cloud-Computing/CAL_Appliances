# from calplus import provider as calplus_provider
# from calplus.client import Client

import django_rq
from django_rq import job


SCHEDULER = django_rq.get_scheduler('default')


def get_available_replica(filepath, number_of_replicas=3):
    # TODO:
    # _count = 1
    # while number_of_replicas >= _count:
    #     replica_id = hashlib.sha256(filepath + '_' + str(_count))
    #     replica = models.Replica.objects.get(identifier=replica_id)
    #     # Check its status, if OK get it.
    #     if replica.status == 'AVAILABLE':
    #         break
    #         return replica
    #     _count += 1
    # return None
    pass


def upload_file(file, file_path, number_of_replicas=3):
    """Upload file"""
    # TODO:
    # from dashboard.models import FileReplica
    #
    # _count = 1
    # while number_of_replicas >= _count:
    #     replica_id, upload_result = upload_object.delay(file, file_path + '_' + str(_count))
    #     if upload_result:
    #         replica_status = UPDATE
    #     else:
    #         replica_status = NOT_UPDATE
    #     replica = FileReplica(identifier=replica_id, status=replica_status)
    #     replica.save()
    # # Check replica status and define File status
    pass



@job()
def upload_object(file, absolute_name):
    """Upload object to cloud node with absolute_name
    :param content(file type)
    :param absolute_name(string): actually it's filepath
    """
    # TODO:
    # object_id = hashlib.sha256(absolute_name).hexdigest()
    # cloud_node = find_successor(object_id)
    # _provider = calplus_provider.Provider(cloud_node.type, dict(json.loads(provider.config)))
    # cal_client = Client(version='1.0.0',
    #                     resource='object_storage',
    #                     provider=_provider)
    # # Check if container named 'files' exists
    # if not cal_client.stat_container('files'):
    #     cal_client.create_container('files')
    # # Upload
    # return (object_id, cal_client.upload_object('files', object_id, contents=file.chunk()))
    pass


def download_object(filepath, number_of_replicas):
    """Download object from Cloudnode"""
    # TODO:
    # # With filepath get all its replica
    # # Then check their status.
    # replica = get_available_replica(filepath, number_of_replicas=number_of_replicas)
    # # If don't find any available replica. Raise exception.
    # # Or may be easier if block download request before. If ObjectMetadata status
    # # is NOT_AVAILABLE (it means all replicas of this object are NOT_AVAILABLE.
    # if not replica:
    #     raise ObjectNotAvailableException()
    # replica_id = replica.id
    # cloud_node = find_successor(replica_id)
    # _provider = calplus_provider.Provider(cloud_node.type, dict(json.loads(provider.config)))
    # cal_client = Client(version='1.0.0',
    #                     resource='object_storage',
    #                     provider=_provider)
    # # Convert all response to the same format
    # result = conver_format(cal_client.download_object('files', replica_id))
    # return result
    pass
