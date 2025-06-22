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

# File paths for 3 trainable sentiment categories (standard is fallback)
SERIOUS_EXAMPLES_FILE = os.path.join(SCRIPT_DIR, "serious_examples.txt")
SILLY_EXAMPLES_FILE = os.path.join(SCRIPT_DIR, "silly_examples.txt")
AGGRESSIVE_EXAMPLES_FILE = os.path.join(SCRIPT_DIR, "aggressive_examples.txt")

SERIOUS_CENTROID_FILE = os.path.join(SCRIPT_DIR, "serious_centroid.pkl")
SILLY_CENTROID_FILE = os.path.join(SCRIPT_DIR, "silly_centroid.pkl")
AGGRESSIVE_CENTROID_FILE = os.path.join(SCRIPT_DIR, "aggressive_centroid.pkl")


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
    print("=== Sentiment Centroid Precomputation (3 Trainable Categories + Standard Fallback) ===")
    
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
        # Load examples for the 3 trainable categories
        print("\n--- Loading Examples ---")
        serious_examples = load_examples(SERIOUS_EXAMPLES_FILE)
        silly_examples = load_examples(SILLY_EXAMPLES_FILE)
        aggressive_examples = load_examples(AGGRESSIVE_EXAMPLES_FILE)
        
        # Compute centroids for the 3 trainable categories
        print("\n--- Computing Centroids ---")
        serious_centroid = compute_centroid(serious_examples, model)
        silly_centroid = compute_centroid(silly_examples, model)
        aggressive_centroid = compute_centroid(aggressive_examples, model)
        
        # Save centroids for the 3 trainable categories
        print("\n--- Saving Centroids ---")
        save_centroid(serious_centroid, SERIOUS_CENTROID_FILE)
        save_centroid(silly_centroid, SILLY_CENTROID_FILE)
        save_centroid(aggressive_centroid, AGGRESSIVE_CENTROID_FILE)
        
        print("\n=== Precomputation Complete ===")
        print(f"Serious centroid: {SERIOUS_CENTROID_FILE}")
        print(f"Silly centroid: {SILLY_CENTROID_FILE}")
        print(f"Aggressive centroid: {AGGRESSIVE_CENTROID_FILE}")
        print("\nNote: 'standard' is a fallback category - no centroid needed.")
        print("Classification logic: if similarity to any centroid is too low → standard")
        print("\nYou can now run the main program - centroids will be loaded from these files.")
        
        return 0
        
    except Exception as e:
        print(f"ERROR during precomputation: {e}")
        return 1


if __name__ == "__main__":
    exit(main()) 