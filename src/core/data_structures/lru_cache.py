from collections import OrderedDict

class LRUCache:

    def __init__(self, capacity: int):
        self._cache = OrderedDict()
        self._capacity = capacity

    def get(self, key):
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

    # Below only used for testing purposes.
    # def display(self):
    #     for (k, v) in self._cache.items():
    #         print(f'{(k, v)}')