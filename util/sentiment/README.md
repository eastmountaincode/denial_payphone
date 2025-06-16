# Sentiment Analysis Setup

This directory contains the sentiment classification system for confession analysis.

## Files

- `serious_examples.txt` - Example sentences for "serious" confessions
- `silly_examples.txt` - Example sentences for "silly" confessions  
- `precompute_centroids.py` - Script to compute and save centroid vectors
- `serious_centroid.pkl` - Precomputed serious centroid (generated)
- `silly_centroid.pkl` - Precomputed silly centroid (generated)

## Setup Process

### 1. First Time Setup
Run the precomputation script to generate centroid files:

```bash
# From the main project directory
python util/sentiment/precompute_centroids.py
```

This will:
- Load the fastText model
- Process the example sentences
- Compute average vectors (centroids) for serious and silly categories
- Save the centroids to pickle files

### 2. Adding More Examples
To improve classification accuracy:

1. Edit `serious_examples.txt` or `silly_examples.txt`
2. Add new example sentences (one per line)
3. Re-run the precomputation script

### 3. Tuning the Threshold
The classification threshold can be adjusted in the main state handler:
- Located in `fsm/states/confession_analyze_sentiment.py`
- Variable: `CLASSIFICATION_THRESHOLD = 0.02`
- Higher values = more conservative (more "neutral" classifications)
- Lower values = more aggressive (more "serious"/"silly" classifications)

## How It Works

1. **Precomputation Phase** (run once):
   - Converts example sentences to fastText vectors
   - Computes centroid (average) for each category
   - Saves centroids to disk

2. **Runtime Classification** (per confession):
   - Loads precomputed centroids (fast)
   - Converts user transcript to fastText vector
   - Calculates cosine similarity to each centroid
   - Uses gap score to classify: `gap = sim_serious - sim_silly`

## Classification Logic

```python
gap = similarity_serious - similarity_silly

if gap > +0.02:    → "serious"
elif gap < -0.02:  → "silly"  
else:              → "neutral"
```

The gap score and classification are logged for analysis and tuning. 