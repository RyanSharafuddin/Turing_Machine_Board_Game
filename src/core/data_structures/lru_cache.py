from collections import OrderedDict

class LRUCache:
    """
    WARN: if None is stored as a value in this cache, it will not work properly. See docstring for the function get(self, key) for further details.
    """

    def __init__(self, capacity: int):
        self._cache = OrderedDict()
        self._capacity = capacity

    def get(self, key):
        """
        WARN: This function assumes that no values stored in the cache are None.
        If a stored value is None, then the variable result will be None,
        and the dictionary will incorrectly not move the key to the end.
        A solution to this would be to have the line
        self._sentinel_object = object() in __init__, and then use the line
        result = self._cache.get(key, self._sentinel_object), and then check
        that result is not self._sentinel_object, since it would be
        guaranteed that no values in the cache will be the sentinel object.
        However, I'm not doing that for this application, b/c I know I'm
        not storing None in any LRU cache, and doing this would slightly slow
        down the get function, b/c the interpreter would have to load
        self._sentinel_object into memory every time it executed this function,
        due to Python 'variables' really being name-bindings.
        """
        result = self._cache.get(key)
        if (result is not None):
            self._cache.move_to_end(key, last=True) # moved to end
        return result

    def put(self, key, value):
        self._cache[key] = value
        self._cache.move_to_end(key, last=True) # moved to end
        if (len(self._cache) > self._capacity):
            self._cache.popitem(last=False) # remove lru item at beginning

    def __contains__(self, item):
        return (item in self._cache)

    def del_item(self, item):
        """
        Just like regular dict, will raise KeyError if called on a key that's not in the cache.
        """
        del self._cache[item]

    def clear(self):
        self._cache.clear()