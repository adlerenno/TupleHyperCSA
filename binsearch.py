def search_right(a, x, lo=0, hi=None, *, key=None):
    """Return the index where to insert item x in list a, assuming a is sorted.

    The return value i is such that all e in a[:i] have e <= x, and all e in
    a[i:] have e > x.  So if x already appears in the list, a.insert(i, x) will
    insert just after the rightmost x already there.

    Optional args lo (default 0) and hi (default len(a)) bound the
    slice of a to be searched.
    """

    if lo < 0:
        raise ValueError('lo must be non-negative')
    if hi is None:
        hi = len(a)
    else:
        hi += 1

    r = range(lo, hi+1)
    # Note, the comparison uses "<" to match the
    # __lt__() logic in list.sort() and in heapq.
    if key is None:
        while lo < hi:
            mid = (lo + hi) // 2
            if x < a[mid]:
                hi = mid
            else:
                lo = mid + 1
        return lo-1
    else:
        while lo < hi:
            
            mid = (lo + hi) // 2
            if x < key(mid):
                hi = mid
            else:
                lo = mid + 1
    return lo-1

def search_left(a, x, lo=0, hi=None, *, key=None):
    """Return the index where to insert item x in list a, assuming a is sorted.

    The return value i is such that all e in a[:i] have e < x, and all e in
    a[i:] have e >= x.  So if x already appears in the list, a.insert(i, x) will
    insert just before the leftmost x already there.

    Optional args lo (default 0) and hi (default len(a)) bound the
    slice of a to be searched.
    """

    if lo < 0:
        raise ValueError('lo must be non-negative')
    if hi is None:
        hi = len(a)
    else:
        hi += 0

    r = range(lo, hi+1)
    # Note, the comparison uses "<" to match the
    # __lt__() logic in list.sort() and in heapq.
    if key is None:
        while lo < hi:
            mid = (lo + hi) // 2
            if a[mid] < x:
                lo = mid + 1
            else:
                hi = mid
        return lo
    else:
        while lo < hi:
            mid = (lo + hi) // 2
            if key(mid) < x:
                lo = mid + 1
            else:
                hi = mid
        return lo

def search_right_csa(a, query, lo=0, hi=None, *, key=None):
    if lo < 0:
        raise ValueError('lo must be non-negative')
    if hi is None:
        hi = len(a)
    else:
        hi += 1

    r = range(lo, hi+1)
    if len(query) == 0:
        return -1

    if key is None:
        while lo < hi:
            mid = (lo + hi) // 2
            index = mid
            for i in range(len(query)):
                if query[i] < a[index]:
                    hi = mid
                    break
                elif query[i] > a[index] or i == len(query)-1:
                    lo = mid + 1
                    break
                index = a[index]-1
        return lo-1 if lo-1 in r and a[lo-1] == query[0] else -1
    else:
        while lo < hi:
            mid = (lo + hi) // 2
            index = mid
            for i in range(len(query)):
                if query[i] < key(index):
                    hi = mid
                    break
                elif query[i] > key(index) or i == len(query)-1:
                    lo = mid + 1
                    break
                index = a[index]-1
    return lo-1 if lo-1 in r and key(lo-1) == query[0] else -1

def search_left_csa(a, query, lo=0, hi=None, *, key=None):
    if lo < 0:
        raise ValueError('lo must be non-negative')
    if hi is None:
        hi = len(a)
    else:
        hi += 0

    r = range(lo, hi+1)
    if len(query) == 0:
        return -1
    # Note, the comparison uses "<" to match the
    # __lt__() logic in list.sort() and in heapq.
    if key is None:
        while lo < hi:
            mid = (lo + hi) // 2
            index = mid
            for i in range(len(query)):
                if a[index] < query[i]:
                    lo = mid + 1
                    break
                elif a[index] > query[i] or i == len(query)-1:
                    hi = mid
                    break
                index = a[index]-1
        return lo if lo in r and a(lo) == query[0] else -1
    else:
        while lo < hi:
            mid = (lo + hi) // 2
            index = mid
            for i in range(len(query)):
                if key(index) < query[i]:
                    lo = mid + 1
                    break
                elif key(index) > query[i] or i == len(query)-1:
                    hi = mid
                    break
                index = a[index]-1
        return lo if lo in r and key(lo) == query[0] else -1

try:
    from _bisect import *
except ImportError:
    pass