# Sentiment Analysis for Confession Classification

This directory contains the sentiment analysis system for classifying confessions into 4 categories based on their tone and content.

## Categories

The system classifies confessions into 4 categories (3 trainable + 1 fallback):

### Trainable Categories (with examples):

1. **serious** - Really serious confessions like serious crimes, self-harm
   - Examples: "I killed somebody", "I've been thinking about hurting myself", "I committed a serious crime"

2. **silly** - Light, funny, minor infractions
   - Examples: "I took a candy bar from my friend", "I ate the last cookie without asking", "I pretended to be sick to skip work"

3. **aggressive** - Dismissive, hostile, actively disregarding the confession prompt
   - Examples: "This is dumb why are you asking me this", "I refuse to participate in this garbage", "What kind of stupid question is that"

### Fallback Category:

4. **standard** - Default category when confidence is too low for other categories
   - Used for normal everyday confessions that don't clearly fit serious/silly/aggressive
   - No training examples needed - assigned when similarity scores are below threshold

## Files

- `serious_examples.txt` - Training examples for serious confessions
- `silly_examples.txt` - Training examples for silly confessions
- `aggressive_examples.txt` - Training examples for aggressive/dismissive responses
- `precompute_centroids.py` - Script to generate centroid vectors for the 3 trainable categories
- Generated centroid files: `serious_centroid.pkl`, `silly_centroid.pkl`, `aggressive_centroid.pkl`
- Note: No `standard_examples.txt` - standard is fallback category

## Usage

1. First, run the precomputation script to generate centroids:
   ```bash
   python util/sentiment/precompute_centroids.py
   ```

2. The main classification happens in `fsm/states/confession_analyze_sentiment.py`

## Classification Method

The system uses fastText word embeddings to:
1. Convert each example sentence to a vector by averaging word vectors
2. Compute centroid vectors for the 3 trainable categories (serious, silly, aggressive)
3. For new input, calculate cosine similarity to each centroid
4. If highest similarity is above threshold → assign that category
5. If all similarities are below threshold → assign "standard" (fallback)

This approach ensures that:
- Clear cases (serious, silly, aggressive) are classified correctly
- Default to "standard" when we can't classify the confession into one of the other categories
- System is robust against edge cases 