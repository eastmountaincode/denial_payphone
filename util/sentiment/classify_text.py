#!/usr/bin/env python3
"""
Simple text classifier for testing confessions.

Usage:
    python classify_text.py "I killed someone"
    python classify_text.py --interactive
"""

import os
import sys
import numpy as np
import pickle
import fasttext

# Add config directory to path for constants
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
UTIL_DIR = os.path.dirname(SCRIPT_DIR)
BASE_DIR = os.path.dirname(UTIL_DIR)
CONFIG_DIR = os.path.join(BASE_DIR, "config")
sys.path.insert(0, CONFIG_DIR)

from constants import CLASSIFICATION_THRESHOLD, CLASSIFICATION_MARGIN

# Configuration
FASTTEXT_MODEL_PATH = "/home/denial/denial_payphone/fasttext/crawl-80d-2M-subword.bin"

# Centroid files
SERIOUS_CENTROID_FILE = os.path.join(SCRIPT_DIR, "serious_centroid.pkl")
SILLY_CENTROID_FILE = os.path.join(SCRIPT_DIR, "silly_centroid.pkl")
AGGRESSIVE_CENTROID_FILE = os.path.join(SCRIPT_DIR, "aggressive_centroid.pkl")

def sent_vec(text, model):
    """Convert sentence to vector by averaging word vectors."""
    words = text.lower().split()
    if not words:
        return np.zeros(model.get_dimension())
    
    vectors = []
    for word in words:
        try:
            vector = model.get_word_vector(word)
            vectors.append(vector)
        except:
            continue
    
    if not vectors:
        return np.zeros(model.get_dimension())
    
    return np.mean(vectors, axis=0)

def cosine_similarity(vec1, vec2):
    """Calculate cosine similarity between two vectors."""
    dot_product = np.dot(vec1, vec2)
    norm1 = np.linalg.norm(vec1)
    norm2 = np.linalg.norm(vec2)
    
    if norm1 == 0 or norm2 == 0:
        return 0.0
    
    return dot_product / (norm1 * norm2)

def load_centroids():
    """Load the precomputed centroids."""
    centroids = {}
    
    for name, file_path in [
        ("serious", SERIOUS_CENTROID_FILE),
        ("silly", SILLY_CENTROID_FILE), 
        ("aggressive", AGGRESSIVE_CENTROID_FILE)
    ]:
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"Centroid file not found: {file_path}")
        
        with open(file_path, 'rb') as f:
            centroids[name] = pickle.load(f)
    
    return centroids

def classify_text(text, model, centroids):
    """Classify a single text input with threshold and margin requirements."""
    if not text.strip():
        return "standard", {}
    
    # Convert text to vector
    test_vec = sent_vec(text, model)
    
    # Calculate similarities
    similarities = {}
    for name, centroid in centroids.items():
        similarities[name] = cosine_similarity(test_vec, centroid)
    
    # Find the category with highest similarity and second highest
    sorted_similarities = sorted(similarities.items(), key=lambda x: x[1], reverse=True)
    best_category, best_similarity = sorted_similarities[0]
    second_best_similarity = sorted_similarities[1][1]
    
    # Calculate margin between highest and second-highest
    margin = best_similarity - second_best_similarity
    
    # Classification logic:
    # 1. Highest similarity must be above threshold
    # 2. Margin between highest and second-highest must be sufficient
    if best_similarity >= CLASSIFICATION_THRESHOLD and margin >= CLASSIFICATION_MARGIN:
        classification = best_category
    else:
        classification = "standard"
    
    return classification, similarities

def main():
    """Main function."""
    
    # Check if centroids exist
    try:
        centroids = load_centroids()
    except FileNotFoundError as e:
        print(f"ERROR: {e}")
        print("Run 'python precompute_centroids.py' first to generate centroids.")
        sys.exit(1)
    
    # Load fastText model
    if not os.path.exists(FASTTEXT_MODEL_PATH):
        print(f"ERROR: fastText model not found at {FASTTEXT_MODEL_PATH}")
        sys.exit(1)
    
    print("Loading fastText model...")
    try:
        model = fasttext.load_model(FASTTEXT_MODEL_PATH)
    except Exception as e:
        print(f"ERROR loading model: {e}")
        sys.exit(1)
    
    # Check command line arguments
    if len(sys.argv) > 1:
        if sys.argv[1] == "--interactive":
            # Interactive mode
            print(f"\nClassification threshold: {CLASSIFICATION_THRESHOLD}")
            print(f"Classification margin: {CLASSIFICATION_MARGIN}")
            print("Enter text to classify (or 'quit' to exit):\n")
            
            while True:
                try:
                    text = input("> ").strip()
                    if text.lower() in ['quit', 'exit', 'q']:
                        break
                    if not text:
                        continue
                        
                    classification, similarities = classify_text(text, model, centroids)
                    
                    # Calculate margin for display
                    sorted_sims = sorted(similarities.items(), key=lambda x: x[1], reverse=True)
                    best_sim = sorted_sims[0][1]
                    second_best_sim = sorted_sims[1][1]
                    margin = best_sim - second_best_sim
                    
                    print(f"Category: {classification}")
                    sim_str = " | ".join([f"{cat}: {sim:.3f}" for cat, sim in similarities.items()])
                    print(f"Similarities: {sim_str}")
                    print(f"Margin: {margin:.3f} (required: {CLASSIFICATION_MARGIN})")
                    
                    # Show reasoning
                    if classification == "standard":
                        if best_sim < CLASSIFICATION_THRESHOLD:
                            print(f"→ Standard: highest similarity ({best_sim:.3f}) below threshold ({CLASSIFICATION_THRESHOLD})")
                        elif margin < CLASSIFICATION_MARGIN:
                            print(f"→ Standard: margin ({margin:.3f}) below required ({CLASSIFICATION_MARGIN})")
                    else:
                        print(f"→ {classification}: meets both threshold and margin requirements")
                    print()
                    
                except KeyboardInterrupt:
                    break
                except Exception as e:
                    print(f"Error: {e}")
                    
        else:
            # Single text from command line
            text = " ".join(sys.argv[1:])
            try:
                classification, similarities = classify_text(text, model, centroids)
                
                # Calculate margin for display
                sorted_sims = sorted(similarities.items(), key=lambda x: x[1], reverse=True)
                best_sim = sorted_sims[0][1]
                second_best_sim = sorted_sims[1][1]
                margin = best_sim - second_best_sim
                
                print(f"Text: \"{text}\"")
                print(f"Category: {classification}")
                sim_str = " | ".join([f"{cat}: {sim:.3f}" for cat, sim in similarities.items()])
                print(f"Similarities: {sim_str}")
                print(f"Margin: {margin:.3f} (required: {CLASSIFICATION_MARGIN})")
                
                # Show reasoning
                if classification == "standard":
                    if best_sim < CLASSIFICATION_THRESHOLD:
                        print(f"→ Standard: highest similarity ({best_sim:.3f}) below threshold ({CLASSIFICATION_THRESHOLD})")
                    elif margin < CLASSIFICATION_MARGIN:
                        print(f"→ Standard: margin ({margin:.3f}) below required ({CLASSIFICATION_MARGIN})")
                else:
                    print(f"→ {classification}: meets both threshold and margin requirements")
                
            except Exception as e:
                print(f"Error: {e}")
    else:
        # No arguments - show help
        print("Usage:")
        print("  python classify_text.py \"your confession here\"")
        print("  python classify_text.py --interactive")

if __name__ == "__main__":
    main() 