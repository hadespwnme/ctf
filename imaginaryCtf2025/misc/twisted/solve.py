import re
import numpy as np


def load_vectors(path: str) -> np.ndarray:
    text = open(path, 'r').read()
    # Extract floats; drop the first element of each 4-tuple (quaternion scalar)
    nums = list(map(float, re.findall(r"[-+]?\d+\.\d+(?:e[+-]?\d+)?", text)))
    rows = [nums[i:i + 4] for i in range(0, len(nums), 4)]
    Y = np.array([r[1:] for r in rows])
    return Y


def kabsch(A: np.ndarray, B: np.ndarray) -> np.ndarray:
    # Finds R minimizing ||R A - B||_F, with det(R) = +1
    H = B.T @ A
    U, S, Vt = np.linalg.svd(H)
    R = U @ Vt
    if np.linalg.det(R) < 0:
        Vt[-1, :] *= -1
        R = U @ Vt
    return R


def decode(output_path: str, scale: float = 1.25) -> str:
    Y = load_vectors(output_path)
    s = scale
    ASCII_MIN, ASCII_MAX = 32, 126

    # Alternating minimization: snap to nearest ASCII, then align via Kabsch
    best_err = float('inf')
    best_X = None

    for seed in range(50):
        rng = np.random.default_rng(seed)
        B = np.eye(3)
        # Initialize around typical printable ASCII mean
        X = np.full_like(Y, 95.0)
        t = Y.mean(axis=0) - s * (B @ X.mean(axis=0))

        for _ in range(250):
            # Snap to nearest ASCII after inverting current transform
            X_est = (B.T @ (Y - t).T / s).T
            X = np.rint(X_est)
            X = np.clip(X, ASCII_MIN, ASCII_MAX)

            # Use known flag prefix to break symmetries
            X[0] = np.array([105, 99, 116])  # 'ict'
            X[1, 0] = 102                    # 'f'
            X[1, 1] = 123                    # '{'

            # Recompute rotation with Kabsch and translation from means
            Xc = X - X.mean(axis=0)
            Yc = (Y - t) / s
            B = kabsch(Xc, Yc)
            t = Y.mean(axis=0) - s * (B @ X.mean(axis=0))

        Y_pred = (s * (B @ X.T)).T + t
        err = float(np.linalg.norm(Y - Y_pred))
        if err < best_err:
            best_err = err
            best_X = X.astype(int)

    decoded = ''.join(''.join(chr(int(c)) for c in row) for row in best_X)
    return decoded


if __name__ == '__main__':
    flag = decode('output.txt')
    print(flag)

