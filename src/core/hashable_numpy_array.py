import numpy as np

class Hashable_Numpy_Array():
    __slots__ = (
        "nparray",
    )
    def __init__(self, nparray: np.ndarray):
        self.nparray = nparray

    def __eq__(self, other):
        return np.array_equal(self, other)

    def __hash__(self):
        pass