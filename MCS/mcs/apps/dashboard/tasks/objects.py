# from dashboard import utils
# from dashboard.models import File

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


def upload_file(file, content):
    """Upload file"""
    # TODO:
    # from mcs.wsgi import RINGS
    # ring = RINGS[username]
    # storage_node = ring.lookup(file.identifier)
    # update_status_file(file.path, File.NOT_AVAILABLE)
    # for cloud in storage_node.clouds.values():
    #     upload_object.delay(file.owner.username, content, file.path, cloud)
    pass


@job()
def upload_object(username, content, object, cloud):
    """Upload object to cloud node with absolute_name
    :param file_content(file type)
    :param file_path
    """
    # TODO:
    # _provider = calplus_provider.Provider(cloud.type, cloud.config)
    # _client = Client(version='1.0.0', resource='object_storage', provider=_provider)
    # if not _client.head_container(username):
    #     _client.create_container(username)
    # # TODO: Update calplus upload_object with headers/metadata
    # _client.upload_object(username, file_path, contents=file_content.chunk(),
    #                       metadata={'status': new_status})
    # # Update object status
    # _client.update_object(username, object, {'status': 'UPDATED'})
    # # Change file status after upload to the 1st cloud
    # if get_status_file(file_path) == File.NOT_AVAILABLE:
    #     update_status_file(file_path, File.AVAILABLE)
    #
    pass


def download_object(file_path, number_of_replicas):
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


def update_status_file(file_path, new_status):
    try:
        file = File.objects.get(path=file_path)
        file.status = new_status
        file.save()
    except File.DoesNotExist as e:
        # TODO:
        # Return message.error()
        raise e


def get_status_file(file_path):
    try:
        file = File.objects.get(path=file_path)
        return file.status
    except File.DoesNotExist as e:
        # TODO:
        # Return message.error()
        raise e


def update_status_object(username, cloud, object, new_status):
    # TODO:
    # _provider = calplus_provider.Provider(cloud.type, cloud.config)
    # _client = Client(version='1.0.0', resource='object_storage', provider=_provider)
    # _client.update_object(username, object, {'status': new_status})
    pass
