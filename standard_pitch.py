import math


table = [16.35 * (2 ** (i / 12)) for i in range(97)]


def predict_to_standard(target):
    if target < 15.3: # C0 - 2^(1/12)
        return 0
    C0 = 16.35
    r = 2 ** (1 / 12)
    n_exact = (math.log(target) - math.log(C0)) / math.log(r)
    if n_exact - math.floor(n_exact) >= 0.5:
        return table[math.ceil(n_exact)]
    else:
        return table[math.floor(n_exact)]


if __name__ == "__main__":
    print(16.35 - 2 ** (1 / 12))