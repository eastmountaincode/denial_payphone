import os
import pickle
import numpy as np
from itertools import combinations

SEMANTIC_THRESHOLD = 0.15  # Minimum cosine distance you consider "well-separated"

def load_centroid(filename):
    with open(filename, 'rb') as f:
        return pickle.load(f)

def cosine_distance(a, b):
    sim = np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b) + 1e-8)
    return 1 - sim

centroid_files = [f for f in os.listdir('.') if f.endswith('_centroid.pkl')]
centroids = {fname: load_centroid(fname) for fname in centroid_files}

print(f"Comparing centroids (threshold = {SEMANTIC_THRESHOLD}):\n")

too_close = []
for (name1, vec1), (name2, vec2) in combinations(centroids.items(), 2):
    cos_dist = cosine_distance(vec1, vec2)
    flag = "OK" if cos_dist >= SEMANTIC_THRESHOLD else "TOO CLOSE"
    print(f"{name1} <-> {name2}:  cosine distance = {cos_dist:.4f}  [{flag}]")
    if cos_dist < SEMANTIC_THRESHOLD:
        too_close.append((name1, name2, cos_dist))

if too_close:
    print("\nWarning: Some centroid pairs are too close together (possible overlap):")
    for name1, name2, dist in too_close:
        print(f"  {name1} <-> {name2}: {dist:.4f}")
else:
    print("\nAll centroid pairs are well-separated.")

