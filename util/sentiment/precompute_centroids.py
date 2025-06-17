#!/usr/bin/env python3
"""
Precompute sentiment centroids for confession classification.

This script should be run manually to generate centroid files that will be
loaded at runtime for fast sentiment classification.

Usage:
    python util/sentiment/precompute_centroids.py
"""

import os
import numpy as np
import fasttext
import pickle

# Path configuration
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
FASTTEXT_MODEL_PATH = "/home/denial/denial_payphone/fasttext/crawl-80d-2M-subword.bin"

# File paths for 4 sentiment categories
VERY_SERIOUS_EXAMPLES_FILE = os.path.join(SCRIPT_DIR, "very_serious_examples.txt")
STANDARD_EXAMPLES_FILE = os.path.join(SCRIPT_DIR, "standard_examples.txt")
NON_SERIOUS_EXAMPLES_FILE = os.path.join(SCRIPT_DIR, "non_serious_examples.txt")
FUCKING_AROUND_EXAMPLES_FILE = os.path.join(SCRIPT_DIR, "fucking_around_examples.txt")

VERY_SERIOUS_CENTROID_FILE = os.path.join(SCRIPT_DIR, "very_serious_centroid.pkl")
STANDARD_CENTROID_FILE = os.path.join(SCRIPT_DIR, "standard_centroid.pkl")
NON_SERIOUS_CENTROID_FILE = os.path.join(SCRIPT_DIR, "non_serious_centroid.pkl")
FUCKING_AROUND_CENTROID_FILE = os.path.join(SCRIPT_DIR, "fucking_around_centroid.pkl")


def sent_vec(text, model):
    """
    Convert sentence to vector by averaging word vectors.
    """
    words = text.lower().split()
    if not words:
        return np.zeros(model.get_dimension())
    
    vectors = []
    for word in words:
        try:
            vector = model.get_word_vector(word)
            vectors.append(vector)
        except:
            # Skip words not in vocabulary
            continue
    
    if not vectors:
        return np.zeros(model.get_dimension())
    
    return np.mean(vectors, axis=0)


def load_examples(filename):
    """
    Load examples from text file (one per line).
    """
    if not os.path.exists(filename):
        raise FileNotFoundError(f"Examples file not found: {filename}")
    
    with open(filename, 'r', encoding='utf-8') as f:
        examples = [line.strip() for line in f if line.strip()]
    
    print(f"Loaded {len(examples)} examples from {filename}")
    return examples


def compute_centroid(examples, model):
    """
    Compute centroid vector from list of example sentences.
    """
    print(f"Computing centroid from {len(examples)} examples...")
    vectors = [sent_vec(example, model) for example in examples]
    centroid = np.mean(vectors, axis=0)
    print(f"Centroid computed with dimension {centroid.shape}")
    return centroid


def save_centroid(centroid, filename):
    """
    Save centroid to pickle file.
    """
    with open(filename, 'wb') as f:
        pickle.dump(centroid, f)
    print(f"Centroid saved to {filename}")


def main():
    print("=== Sentiment Centroid Precomputation (4 Categories) ===")
    
    # Check if fastText model exists
    if not os.path.exists(FASTTEXT_MODEL_PATH):
        print(f"ERROR: fastText model not found at {FASTTEXT_MODEL_PATH}")
        print("Please ensure the fastText model is available.")
        return 1
    
    print(f"Loading fastText model from {FASTTEXT_MODEL_PATH}...")
    try:
        model = fasttext.load_model(FASTTEXT_MODEL_PATH)
        print(f"fastText model loaded successfully (dimension: {model.get_dimension()})")
    except Exception as e:
        print(f"ERROR loading fastText model: {e}")
        return 1
    
    try:
        # Load examples for all 4 categories
        print("\n--- Loading Examples ---")
        very_serious_examples = load_examples(VERY_SERIOUS_EXAMPLES_FILE)
        standard_examples = load_examples(STANDARD_EXAMPLES_FILE)
        non_serious_examples = load_examples(NON_SERIOUS_EXAMPLES_FILE)
        fucking_around_examples = load_examples(FUCKING_AROUND_EXAMPLES_FILE)
        
        # Compute centroids for all 4 categories
        print("\n--- Computing Centroids ---")
        very_serious_centroid = compute_centroid(very_serious_examples, model)
        standard_centroid = compute_centroid(standard_examples, model)
        non_serious_centroid = compute_centroid(non_serious_examples, model)
        fucking_around_centroid = compute_centroid(fucking_around_examples, model)
        
        # Save centroids for all 4 categories
        print("\n--- Saving Centroids ---")
        save_centroid(very_serious_centroid, VERY_SERIOUS_CENTROID_FILE)
        save_centroid(standard_centroid, STANDARD_CENTROID_FILE)
        save_centroid(non_serious_centroid, NON_SERIOUS_CENTROID_FILE)
        save_centroid(fucking_around_centroid, FUCKING_AROUND_CENTROID_FILE)
        
        print("\n=== Precomputation Complete ===")
        print(f"Very serious centroid: {VERY_SERIOUS_CENTROID_FILE}")
        print(f"Standard centroid: {STANDARD_CENTROID_FILE}")
        print(f"Non serious centroid: {NON_SERIOUS_CENTROID_FILE}")
        print(f"Fucking around centroid: {FUCKING_AROUND_CENTROID_FILE}")
        print("\nYou can now run the main program - centroids will be loaded from these files.")
        
        return 0
        
    except Exception as e:
        print(f"ERROR during precomputation: {e}")
        return 1


if __name__ == "__main__":
    exit(main()) 