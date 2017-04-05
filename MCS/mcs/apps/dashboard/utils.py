import hashlib
import os

from django.conf import settings


def user_directory_path(instance):
    # file will be uploaded to MEDIA_ROOT/user_<id>/2017/12/03/
    return 'user_{0}/%Y/%m/%d/'.format(instance.owner.id)


def handle_uploaded_file(file, filepath):
    """Handle uploaded file. Hash its path then store it.
    Tempory before push it to cloudnode.

    Arguments:
        file {[UploadedFile]}
        filepath {[hashing_id]} -- [description]
    """
    # Delete auto-saved file. Find more pythonic way to handle this in
    # future.
    try:
        os.remove(os.path.join(settings.MEDIA_ROOT, file.name))
    except OSError:
        pass

    _new_file_name = hashlib.sha256(filepath)
    with open('/tmp/' + _new_file_name.hexdigest(), 'wb+') as destination:
        for chunk in file.chunks():
            destination.write(chunk)


def get_folder_by_path(jsondata, path, result):
    """Get folder data from json data, with given path"""
    if isinstance(jsondata, dict):
        if jsondata['path'] == path.strip():
            result.append(jsondata)
        else:
            if jsondata['type'] == 'folder':
                get_folder_by_path(jsondata['children'], path, result)
    elif isinstance(jsondata, list):
        for item in jsondata:
            get_folder_by_path(item, path, result)


def generate_hash_key(str_to_hash):
    """Generate hash key for given string"""
    return int(hashlib.sha256(str_to_hash).hexdigest(), 16) % 64
