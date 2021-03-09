import numpy as np


def get_array_gini(arr):
    n = len(arr)
    return 2 / n * (np.sort(arr) * (np.arange(n) + 1)).sum() / arr.sum() - (n + 1) / n
