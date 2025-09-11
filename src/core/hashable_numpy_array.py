from rich.text import Text
import numpy as np
import xxhash

class Hashable_Numpy_Array():
    """
    See https://xxhash.com/ and https://pypi.org/project/xxhash/ for how the hashing works.

    WARN: Technically, the __eq__ method is incorrectly implemented, in 2 ways:

    1. If you try to compare a Hashable_Numpy_Array for equality with any object that does not have a .nparray attribute, it will raise an AttributeError.

    2. The np.array_equal function considers 2 numpy arrays equal if they contain equivalent numbers, even if the arrays are of different types. For example,
    np.array_equal(
        np.array([1,2], dtype=np.uint8),
        np.array([1,2], dtype=np.uint16)
    ) 
    returns True, even though the first array has dtype uint8 and the second array has dtype uint16. However, the __hash__ function only considers the raw bytes, and the raw bytes of those arrays differ. For example, the raw bytes of the first array is b'\x01\x02', and the raw bytes of the second array is b'\x01\x00\x02\x00', because each element is 16 bit in the second, and 8 bit in the first. Because the raw bytes of these arrays differ, their hashes most likely differ, even though they would compare equal under __eq__, which breaks the rule that equal object have equal hashes.

    However, that's okay, b/c the only place in this program that the __hash__ or __eq__ functions of this class are used are when inserting cache_game_states into a solver's evaluations_cache. The evaluations cache will only contain np arrays of the all the same shape and type, and since each every object in the cache will be a cache_game_state, the __eq__ function of this class will only ever be used to compare against other objects of this class, thus avoiding both of the above problems.
    """
    __slots__ = (
        "nparray",
    )
    def __init__(self, nparray: np.ndarray):
        self.nparray = nparray

    def __eq__(self, other):
        return np.array_equal(self.nparray, other.nparray)

    def __hash__(self):
        return xxhash.xxh64_intdigest(self.nparray)

    def __str__(self):
        return self.__repr__()

    def __repr__(self):
        return f"Hashable_Numpy_Array({repr(self.nparray)})"

def int_to_pretty_hex_Text(n: int, num_bytes=8):
    """
    Given an integer, converts it to a hex string, pads the hex string with leading 0s until the hex string contains `num_bytes` amount of bytes (2 hex digits = 1 byte), strips the leading '0x', uppercases all the letters, and inserts spaces between every byte.

    Returns
    -------
    A pretty hex Text like "46 98 35 FA D9 5C BB FA".
    """
    h = hex(n)[2:].upper()
    h = f'{h:0>{num_bytes * 2}}'
    l = []
    for(index, char) in enumerate(h):
        if((index % 2 == 0) and (index > 0)):
            l.append(" ")
        l.append(char)
    return Text(''.join(l), style='cyan')

# Testing stuff. Uncomment and run file directly to understand some stuff.
# from rich.console import Console
# console = Console()

# arr1 = np.array( [2,3,45,87, 6], dtype=np.uint8)
# arr2 = np.array([2,3,45,87, 6], dtype=np.uint16)
# console.print("arr1:", repr(arr1))
# console.print("arr2:", repr(arr2))
# console.print("np.array_equal(arr1, arr2) :", np.array_equal(arr1, arr2))

# h1 = Hashable_Numpy_Array(arr1).__hash__()
# h2 = Hashable_Numpy_Array(arr2).__hash__()


# print("arr1 hash: ", end="")
# console.print(int_to_pretty_hex_Text(h1))
# print("arr2 hash: ", end="")
# console.print(int_to_pretty_hex_Text(h2))

# print("hashes of bytes:")
# print("           ", end="")
# console.print(int_to_pretty_hex_Text((xxhash.xxh64(b"\x02\x03\x2D\x57\x06").intdigest())))
# print("           ", end="")
# console.print(int_to_pretty_hex_Text((xxhash.xxh64(b"\x02\x00\x03\x00\x2D\x00\x57\x00\x06\x00").intdigest())))

# print("arr1 bytes:", memoryview(arr1).tobytes(order='A').hex(" ").upper())
# print("arr2 bytes:", memoryview(arr2).tobytes(order='A').hex(" ").upper())


# d = dict()
# arr3 = np.array( [2,3,45,87, 6], dtype=np.uint8)
# print(arr3 is arr1)

# hashable1 = Hashable_Numpy_Array(arr1)
# hashable3 = Hashable_Numpy_Array(arr3)
# d[hashable1] = "Yeehaw"
# console.print(d)

# console.print("hashable1 is hashable3:", hashable1 is hashable3)
# console.print("hashable1 == hashable3:", hashable1 == hashable3)
# console.print("hashable3 in d:", hashable3 in d)
