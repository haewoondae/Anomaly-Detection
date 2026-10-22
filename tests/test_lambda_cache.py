import os, sys
import numpy as np
import scipy.stats as stats

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'src')))
from models.osESD_Test import get_lambda, get_lambda_author


def uncached_get_lambda(alpha, size):
    if size < 4:
        return 0.0
    p = 1 - alpha / (2 * size)
    t = stats.t.ppf(p, size - 2)
    return (size - 1) * t / np.sqrt((size - 2 + t * t) * size)


def uncached_get_lambda_author(alpha, size):
    if size < 4:
        return 0.0
    p = 1 - alpha / (2 * size)
    t = stats.t.ppf(p, size - 2)
    return (size - 1) * t / np.sqrt((size + t * t) * size)


def test_bit_identical_lambda():
    alphas = [0.001, 0.005, 0.01, 0.05]
    sizes = range(4, 260)
    for alpha in alphas:
        for size in sizes:
            # 1. Standard Rosner lambda
            cached_val = get_lambda(alpha, size)
            uncached_val = uncached_get_lambda(alpha, size)
            assert cached_val == uncached_val, f"Mismatch in get_lambda(alpha={alpha}, size={size})"
            
            # 2. Author lambda
            cached_author = get_lambda_author(alpha, size)
            uncached_author = uncached_get_lambda_author(alpha, size)
            assert cached_author == uncached_author, f"Mismatch in get_lambda_author(alpha={alpha}, size={size})"
    print(f"PASS: Bit-for-bit identical test passed for {len(alphas)} alphas x {len(sizes)} sizes ({len(alphas)*len(sizes)*2} evaluations)!")


if __name__ == "__main__":
    test_bit_identical_lambda()
