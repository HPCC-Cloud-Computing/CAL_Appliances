from lookup.ring.ring import RING_SIZE


def decr(value, size):
    """Decrement"""
    if size <= value:
        return value - size
    else:
        return RING_SIZE - (size - value)


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
            left = left - RING_SIZE
        else:
            if (val > left):
                right = right + RING_SIZE

        if (val > left and val < right):
            return True
        else:
            return False
    return True
