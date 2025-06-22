#!/usr/bin/env python3
"""
Simple test script for sentiment classification.
Tests sample confessions to see how they get categorized.

Usage:
    python test_classification.py
"""

import os
import sys
import numpy as np
import pickle
import fasttext

# Add parent directories to path
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
UTIL_DIR = os.path.dirname(SCRIPT_DIR)
BASE_DIR = os.path.dirname(UTIL_DIR)
sys.path.insert(0, UTIL_DIR)
sys.path.insert(0, BASE_DIR)

FASTTEXT_MODEL_PATH = "/home/denial/denial_payphone/fasttext/crawl-80d-2M-subword.bin"

# Import from the actual FSM state module
from fsm.states.confession_analyze_sentiment import classify_sentiment, CLASSIFICATION_THRESHOLD

def test_samples():
    """Test a variety of sample confessions"""
    
    # Load fastText model
    if not os.path.exists(FASTTEXT_MODEL_PATH):
        print(f"ERROR: fastText model not found at {FASTTEXT_MODEL_PATH}")
        print("Update the path in this script for your system.")
        return
        
    print("Loading fastText model...")
    model = fasttext.load_model(FASTTEXT_MODEL_PATH)
    print(f"Model loaded (dimension: {model.get_dimension()})")
    
    # Test samples for each category
    test_confessions = [
        # Should be SERIOUS
        ("I killed someone", "serious"),
        ("I'm thinking about suicide", "serious"),
        ("I committed murder", "serious"),
        ("I've been cutting myself", "serious"),
        
        # Should be SILLY  
        ("I ate the last cookie", "silly"),
        ("I took a pen from work", "silly"),
        ("I pretended to be sick", "silly"),
        ("I used my roommate's shampoo", "silly"),
        
        # Should be AGGRESSIVE
        ("This is dumb why are you asking me this", "aggressive"),
        ("I refuse to participate in this garbage", "aggressive"),
        ("What kind of stupid question is that", "aggressive"),
        ("This whole thing is a waste of time", "aggressive"),
        
        # Should be STANDARD (ambiguous)
        ("I sometimes tell white lies", "standard"),
        ("I gossiped about a friend", "standard"),
        ("I was late to work yesterday", "standard"),
        ("I forgot to call my mom back", "standard"),
    ]
    
    print(f"\n=== Testing Classification (threshold = {CLASSIFICATION_THRESHOLD}) ===\n")
    
    correct = 0
    total = len(test_confessions)
    
    for confession, expected in test_confessions:
        try:
            classification, similarities = classify_sentiment(confession, model)
            
            # Check if correct
            is_correct = "✓" if classification == expected else "✗"
            if classification == expected:
                correct += 1
                
            print(f"{is_correct} \"{confession}\"")
            print(f"   → Predicted: {classification} | Expected: {expected}")
            
            # Show similarities
            sim_str = " | ".join([f"{cat}: {sim:.3f}" for cat, sim in similarities.items() if cat != "standard"])
            print(f"   → Similarities: {sim_str}")
            print()
            
        except Exception as e:
            print(f"✗ \"{confession}\" → ERROR: {e}")
            print()
    
    accuracy = correct / total * 100
    print(f"=== Results: {correct}/{total} correct ({accuracy:.1f}%) ===")
    
    if accuracy < 75:
        print("\n💡 Tips to improve accuracy:")
        print("- Adjust CLASSIFICATION_THRESHOLD in confession_analyze_sentiment.py")
        print("- Add more diverse examples to training files")
        print("- Run precompute_centroids.py again after adding examples")

def interactive_test():
    """Interactive mode to test custom confessions"""
    
    # Load fastText model
    if not os.path.exists(FASTTEXT_MODEL_PATH):
        print(f"ERROR: fastText model not found at {FASTTEXT_MODEL_PATH}")
        return
        
    print("Loading fastText model...")
    model = fasttext.load_model(FASTTEXT_MODEL_PATH)
    
    print("\n=== Interactive Classification Test ===")
    print("Enter confessions to test (or 'quit' to exit):\n")
    
    while True:
        confession = input("Confession: ").strip()
        
        if confession.lower() in ['quit', 'exit', 'q']:
            break
            
        if not confession:
            continue
            
        try:
            classification, similarities = classify_sentiment(confession, model)
            
            print(f"   → Classification: {classification}")
            sim_str = " | ".join([f"{cat}: {sim:.3f}" for cat, sim in similarities.items() if cat != "standard"])
            print(f"   → Similarities: {sim_str}")
            print()
            
        except Exception as e:
            print(f"   → ERROR: {e}")
            print()

def main():
    """Main function with options"""
    
    if len(sys.argv) > 1 and sys.argv[1] == "--interactive":
        interactive_test()
    else:
        test_samples()
        
        print("\nTip: Run with --interactive for custom testing")

if __name__ == "__main__":
    main() 