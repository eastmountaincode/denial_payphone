import os
import pickle
import numpy as np
from itertools import combinations

def load_centroid(filename):
    with open(filename, 'rb') as f:
        return pickle.load(f)

def cosine_distance(a, b):
    # Cosine similarity
    sim = np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b) + 1e-8)
    # Cosine distance
    return 1 - sim

# Find all centroid pickle files in current directory
centroid_files = [f for f in os.listdir('.') if f.endswith('_centroid.pkl')]
centroids = {fname: load_centroid(fname) for fname in centroid_files}

print("Comparing centroids in current directory:\n")

for (name1, vec1), (name2, vec2) in combinations(centroids.items(), 2):
    cos_dist = cosine_distance(vec1, vec2)
    print(f"{name1} <-> {name2}")
    print(f"    Cosine distance   : {cos_dist:.4f}")

