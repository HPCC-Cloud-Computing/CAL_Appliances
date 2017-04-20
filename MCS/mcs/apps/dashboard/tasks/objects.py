import copy

from dashboard import exceptions
from dashboard.models import File

from mcs.wsgi import RINGS


# SCHEDULER = django_rq.get_scheduler('default')


def upload_file(file, content):
    """Upload file
    :param file: object of model File.
    :param content: content of file (stream
.    """
    ring = RINGS[file.owner.username]
    node = ring.lookup(long(file.identifier))
    update_status_file(file.path, File.NOT_AVAILABLE)
    for cloud in node.clouds:
        # Put task to queue 'default'
        _content = copy.deepcopy(content)
        upload_object(cloud, _content, file)
        # upload_object.delay(cloud, _content, file)
    update_status_file(file.path, File.UPDATE)


# @job
def upload_object(cloud, content, file):
    """Upload object to cloud node with absolute_name
    :param cloud: object of model Cloud.
    :parem content: content of file (Stream).
    :param file: object of model File.
    """
    # Create container named = username if it doesnt exist
    container = file.owner.username

    try:
        cloud.connector.upload_object(container, file.path.strip('/'),
                                      contents=content.read(),
                                      content_length=content.size,
                                      metadata={'status': 'UPDATED'})
    except exceptions.UploadObjectError as e:
        # TODO:
        # return message.error(e)
        raise e
    # Update file's status
    if get_status_file(file.path) == File.NOT_AVAILABLE:
        update_status_file(file.path, File.AVAILABLE)


def download_file(file):
    """Download object from Cloud
    :param file: object of model File.
    """
    ring = RINGS[file.owner.username]
    node = ring.lookup(long(file.identifier))
    container = file.owner.username
    for cloud in node.clouds:
        try:
            object_stat = cloud.connector.stat_object(container, file.path.strip('/'))
        except:
            continue

        # Temporary handle.
        stream_key = 1
        if cloud.type == 'amazon':
            object_stat = object_stat['Metadata']
            stream_key = 'Body'
        object_status = [object_stat[key] for key in object_stat.keys() if 'status' in key]
        if object_status[0] == 'UPDATED':
            file_content = cloud.connector.download_object(container,
                                                           file.path.strip('/'))[stream_key]
            if cloud.type == 'amazon':
                return file_content.read()
            return file_content
    return None  # Should raise message error.


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
    """Get File object's status"""
    try:
        file = File.objects.get(path=file_path)
        return file.status
    except File.DoesNotExist as e:
        # TODO:
        # Return message.error()
        raise e


def update_status_object(cloud, container, object, new_status):
    """Upload exist object's status"""
    try:
        cloud.connector.update_object(container, object,
                                      metadata={'status': new_status})
    except exceptions.UpdateObjectError as e:
        raise e


def delete_file(file):
    """Delete file"""
    ring = RINGS[file.owner.username]
    node = ring.lookup(long(file.identifier))
    container = file.owner.username
    for cloud in node.clouds:
        cloud.connector.delete_object(container, file.path.strip('/'))
