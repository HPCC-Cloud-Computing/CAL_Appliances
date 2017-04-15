import logging
import pickle

import os
# from lookup.chord.ring import RING_SIZE
from django.conf import settings

LOG = logging.getLogger(__name__)


def decr(value, size):
    """Decrement"""
    if size <= value:
        return value - size
    else:
        return settings.RING_SIZE - (size - value)


def in_interval(val, left, right, equal_left=False, equal_right=False):
    """Check val is in (left, right) or not"""
    if (equal_left and val == left):
        return True

    if (equal_right and val == right):
        return True

    if (right > left):
        if (val > left and val < right):
            return True
        else:
            return False

    if (right < left):
        if (val < left):
            left = left - settings.RING_SIZE
        else:
            if (val > left):
                right = right + settings.RING_SIZE

        if (val > left and val < right):
            return True
        else:
            return False
    return True


def check_diff_seq_elements(data):
    """Check if 3 sequential elements in list are diff
    For e.x: data = [1, 2, 3] -> return True.
    data = [1,2,3] -> return False
    """
    seq_list = zip(data[:-1], data[1:], data[2:])
    for three_ele in seq_list:
        if three_ele[0] == three_ele[1] or three_ele[1] == three_ele[2] or three_ele[0] == three_ele[2]:
            return False
    return True


def save(obj, path):
    """Save Classifier object to pickle file."""
    if os.path.isfile(path):
        LOG.info('File existed! Use load() method.')
    else:
        pickle.dump(obj, open(path, 'wb'), pickle.HIGHEST_PROTOCOL)


def load(path):
    """Load Classifier object from pickle file"""
    if not os.path.isfile(path):
        LOG.info('File doesnt existed!')
        raise IOError()
    else:
        return pickle.load(open(path, 'rb'))
