# fsm/states/confession_analyze_sentiment.py

import os
import numpy as np
import pickle
from session_states import S

import fsm.common  # Setup paths to util directory

from general_util import play_and_log
from log import log_event

# Path to precomputed centroid files for 3 trainable categories
SENTIMENT_DIR = os.path.join(fsm.common.UTIL_DIR, "sentiment")
SERIOUS_CENTROID_FILE = os.path.join(SENTIMENT_DIR, "serious_centroid.pkl")
SILLY_CENTROID_FILE = os.path.join(SENTIMENT_DIR, "silly_centroid.pkl")
AGGRESSIVE_CENTROID_FILE = os.path.join(SENTIMENT_DIR, "aggressive_centroid.pkl")

# Similarity threshold for classification (if below, classify as "standard")
CLASSIFICATION_THRESHOLD = 0.5

# Cached centroids (loaded once)
_serious_centroid = None
_silly_centroid = None
_aggressive_centroid = None


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


def cosine_similarity(vec1, vec2):
    """
    Calculate cosine similarity between two vectors.
    """
    dot_product = np.dot(vec1, vec2)
    norm1 = np.linalg.norm(vec1)
    norm2 = np.linalg.norm(vec2)
    
    if norm1 == 0 or norm2 == 0:
        return 0.0
    
    return dot_product / (norm1 * norm2)


def load_precomputed_centroids():
    """
    Load precomputed centroids from pickle files for the 3 trainable categories.
    """
    global _serious_centroid, _silly_centroid, _aggressive_centroid
    
    if (_serious_centroid is None or _silly_centroid is None or _aggressive_centroid is None):
        
        # Check if centroid files exist
        centroid_files = [
            (SERIOUS_CENTROID_FILE, "Serious"),
            (SILLY_CENTROID_FILE, "Silly"),
            (AGGRESSIVE_CENTROID_FILE, "Aggressive")
        ]
        
        for file_path, name in centroid_files:
            if not os.path.exists(file_path):
                raise FileNotFoundError(f"{name} centroid file not found: {file_path}")
        
        # Load centroids
        with open(SERIOUS_CENTROID_FILE, 'rb') as f:
            _serious_centroid = pickle.load(f)
            
        with open(SILLY_CENTROID_FILE, 'rb') as f:
            _silly_centroid = pickle.load(f)
            
        with open(AGGRESSIVE_CENTROID_FILE, 'rb') as f:
            _aggressive_centroid = pickle.load(f)
    
    return _serious_centroid, _silly_centroid, _aggressive_centroid


def classify_sentiment(transcript, model):
    """
    Classify transcript sentiment into one of 4 categories: serious, silly, aggressive, standard.
    Uses threshold-based approach: if similarity to any trained category is above threshold,
    assign that category; otherwise assign "standard" as fallback.
    Returns tuple: (classification, similarities_dict)
    """
    if not transcript.strip():
        return "standard", {}
    
    # Load precomputed centroids for the 3 trainable categories
    serious_centroid, silly_centroid, aggressive_centroid = load_precomputed_centroids()
    
    # Convert transcript to vector
    test_vec = sent_vec(transcript, model)
    
    # Calculate similarities to the 3 trained centroids
    similarities = {
        "serious": cosine_similarity(test_vec, serious_centroid),
        "silly": cosine_similarity(test_vec, silly_centroid),
        "aggressive": cosine_similarity(test_vec, aggressive_centroid)
    }
    
    # Find the category with highest similarity
    best_category = max(similarities, key=similarities.get)
    best_similarity = similarities[best_category]
    
    # If highest similarity is above threshold, assign that category
    # Otherwise, assign "standard" as fallback
    if best_similarity >= CLASSIFICATION_THRESHOLD:
        classification = best_category
    else:
        classification = "standard"
        
    # Add standard similarity for logging (always 0 since it's fallback)
    similarities["standard"] = 0.0 if classification != "standard" else 1.0
    
    return classification, similarities


def handle_confession_analyze_sentiment(engine):
    """
    Analyze the sentiment of the recorded confession and play appropriate response.
    
    Args:
        engine: SessionEngine instance with fasttext_model, session_folder, etc.
        
    Returns:
        S.POST_CONFESSION_INFO_REQUEST after playing the sentiment-based response
        
    Raises:
        SessionAbort: If user hangs up or audio playback fails
    """
    
    # Load the transcript from the file created in the previous state
    transcript_path = os.path.join(str(engine.session_folder), f"confession_transcript_{engine.session_id}.txt")
    
    if not os.path.exists(transcript_path):
        log_event(engine.session_id, "sentiment_analysis_error", "Transcript file not found")
        print("[FSM] Warning - No transcript file found, using empty transcript")
        transcript = ""
    else:
        with open(transcript_path, 'r', encoding='utf-8') as f:
            transcript = f.read().strip()
        print(f"[FSM]: Loaded transcript for sentiment analysis: '{transcript[:100]}{'...' if len(transcript) > 100 else ''}'")
    
    # Perform sentiment classification
    log_event(engine.session_id, "sentiment_analysis_start")
    
    classification, similarities = classify_sentiment(transcript, engine.fasttext_model)
    
    # Log the results
    log_event(engine.session_id, "confession_classified", {
        "classification": classification
    })
    
    print(f"[FSM]: Sentiment classification: {classification}")
    
    # Determine which audio file to play based on classification
    if classification == "serious":
        audio_file = "post_confession_message.wav"  # TODO: Replace with serious_response.wav
        log_description = "serious response"
    elif classification == "silly":
        audio_file = "post_confession_message.wav"  # TODO: Replace with silly_response.wav
        log_description = "silly response"
    elif classification == "aggressive":
        audio_file = "post_confession_message.wav"  # TODO: Replace with aggressive_response.wav
        log_description = "aggressive response"
    elif classification == "standard":
        audio_file = "post_confession_message.wav"  # TODO: Replace with standard_response.wav
        log_description = "standard response (fallback)"
    else:
        # Fallback fallback
        audio_file = "post_confession_message.wav"
        log_description = "default response"
    
    # Play the appropriate response
    if not play_and_log(audio_file, str(engine.audio_dir), engine.sensor, engine.session_id, log_description):
        raise engine.SessionAbort
    
    print(f"[FSM] Played {classification} response - moving to post confession info request")
    return S.POST_CONFESSION_INFO_REQUEST 