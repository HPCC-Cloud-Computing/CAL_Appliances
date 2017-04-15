from UserDict import DictMixin
from eventlet.semaphore import Semaphore
from apps.lookup.ring.ring import Ring


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
        self.global_ring_dict_lock = Semaphore(1)
        self.version = 0

    def lock(self):
        if not self.locked():
            self.global_ring_dict_lock.acquire()
        else:
            raise GlobalException("Can not lock a Ring Dict was locked")

    def __enter__(self):
        self.global_ring_dict_lock.acquire()

    def __exit__(self, typ, val, tb):
        self.global_ring_dict_lock.release()

    def unlock(self):
        if self.locked():
            self.global_ring_dict_lock.release()
        else:
            raise GlobalException("Can not unlock a Ring Dict isn't locked")

    def locked(self):
        return self.global_ring_dict_lock.locked()


class GlobalException(Exception):
    def __init__(self, message):
        self.message = message


class GlobalRing():
    def __init__(self):
        self.ring = 0
        self.global_ring_lock = Semaphore(1)
        self.version = 0

    def lock(self):
        if not self.locked():
            self.global_ring_lock.acquire()
        else:
            raise GlobalException("Can not lock a Ring was locked")

    def __enter__(self):
        self.global_ring_lock.acquire()

    def __exit__(self, typ, val, tb):
        self.global_ring_lock.release()

    def unlock(self):
        if self.locked():
            self.global_ring_lock.release()
        else:
            raise GlobalException("Can not unlock a Ring isn't locked")

    def locked(self):
        return self.global_ring_lock.locked()
