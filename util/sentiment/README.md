# Sentiment Analysis for Confession Classification

This directory contains the sentiment analysis system for classifying confessions into 4 categories based on their tone and content.

## Categories

The system now classifies confessions into 4 distinct categories:

1. **very_serious** - Deep, genuinely remorseful confessions
   - Examples: "I hurt someone and I regret it deeply", "I have been struggling with addiction"

2. **standard** - Normal everyday confessions and mistakes  
   - Examples: "I sometimes tell white lies to avoid conflict", "I gossiped about a friend behind their back"

3. **non_serious** - Light, minor infractions
   - Examples: "I took a candy bar from my friend", "I ate the last cookie without asking"

4. **fucking_around** - Dismissive, actively disregarding the confession prompt
   - Examples: "This is dumb why are you asking me this", "I refuse to participate in this garbage"

## Files

- `very_serious_examples.txt` - Training examples for very serious confessions
- `standard_examples.txt` - Training examples for standard confessions  
- `non_serious_examples.txt` - Training examples for non-serious confessions
- `fucking_around_examples.txt` - Training examples for dismissive responses
- `precompute_centroids.py` - Script to generate centroid vectors for classification
- Generated centroid files: `*_centroid.pkl` (created by precompute script)

## Usage

1. First, run the precomputation script to generate centroids:
   ```bash
   python util/sentiment/precompute_centroids.py
   ```

2. The main classification happens in `fsm/states/confession_analyze_sentiment.py`

## Classification Method

The system uses fastText word embeddings to:
1. Convert each example sentence to a vector by averaging word vectors
2. Compute centroid vectors for each category
3. For new input, find the category with highest cosine similarity

This replaces the previous 2-category system (serious/silly) with a more nuanced 4-category approach that better captures the range of user responses. 