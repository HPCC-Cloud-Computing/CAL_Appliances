from UserDict import DictMixin
from eventlet.semaphore import Semaphore


# Singleton implementation

class _Singleton(type):
    """ A metaclass that creates a Singleton base class when called. """
    _instances = {}

    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            cls._instances[cls] = super(_Singleton, cls).__call__(*args,
                                                                  **kwargs)
        return cls._instances[cls]


class Singleton(_Singleton('SingletonMeta', (object,), {})):
    pass


class RingDict(Singleton, DictMixin, dict):
    def __init__(self):
        super(self.__class__, self).__init__()
        self.x = 0


class GlobalRingException(Exception):
    def __init__(self, message):
        self.message = message


class GlobalRing(object):
    def __init__(self):
        self.ring = 0
        self.global_lock = Semaphore(1)
        self.version = 0

    def lock(self):
        if not self.locked():
            self.global_lock.acquire()
        else:
            raise GlobalRingException("Can not lock a Ring was locked")

    def __enter__(self):
        self.global_lock.acquire()

    def __exit__(self, typ, val, tb):
        self.global_lock.release()

    def unlock(self):
        if self.locked():
            self.global_lock.release()
        else:
            raise GlobalRingException("Can not unlock a Ring isn't locked")

    def locked(self):
        return self.global_lock.locked()


class DataObjecRings:
    def __init__(self, ring_list):
        self.ring_list = ring_list
