# fsm/states/confession_analyze_sentiment.py

import os
import numpy as np
import pickle
from session_states import S

import fsm.common  # Setup paths to util directory

from general_util import play_and_log
from log import log_event

# Path to precomputed centroid files for 4 categories
SENTIMENT_DIR = os.path.join(fsm.common.UTIL_DIR, "sentiment")
VERY_SERIOUS_CENTROID_FILE = os.path.join(SENTIMENT_DIR, "very_serious_centroid.pkl")
STANDARD_CENTROID_FILE = os.path.join(SENTIMENT_DIR, "standard_centroid.pkl")
NON_SERIOUS_CENTROID_FILE = os.path.join(SENTIMENT_DIR, "non_serious_centroid.pkl")
FUCKING_AROUND_CENTROID_FILE = os.path.join(SENTIMENT_DIR, "fucking_around_centroid.pkl")

# Cached centroids (loaded once)
_very_serious_centroid = None
_standard_centroid = None
_non_serious_centroid = None
_fucking_around_centroid = None


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
    Load precomputed centroids from pickle files for all 4 categories.
    """
    global _very_serious_centroid, _standard_centroid, _non_serious_centroid, _fucking_around_centroid
    
    if (_very_serious_centroid is None or _standard_centroid is None or 
        _non_serious_centroid is None or _fucking_around_centroid is None):
        print("Loading precomputed sentiment centroids for 4 categories...")
        
        # Check if centroid files exist
        centroid_files = [
            (VERY_SERIOUS_CENTROID_FILE, "Very serious"),
            (STANDARD_CENTROID_FILE, "Standard"),
            (NON_SERIOUS_CENTROID_FILE, "Non serious"),
            (FUCKING_AROUND_CENTROID_FILE, "Fucking around")
        ]
        
        for file_path, name in centroid_files:
            if not os.path.exists(file_path):
                raise FileNotFoundError(f"{name} centroid file not found: {file_path}")
        
        # Load centroids
        with open(VERY_SERIOUS_CENTROID_FILE, 'rb') as f:
            _very_serious_centroid = pickle.load(f)
        
        with open(STANDARD_CENTROID_FILE, 'rb') as f:
            _standard_centroid = pickle.load(f)
            
        with open(NON_SERIOUS_CENTROID_FILE, 'rb') as f:
            _non_serious_centroid = pickle.load(f)
            
        with open(FUCKING_AROUND_CENTROID_FILE, 'rb') as f:
            _fucking_around_centroid = pickle.load(f)
        
        print(f"Loaded centroids - Very serious: {_very_serious_centroid.shape}, "
              f"Standard: {_standard_centroid.shape}, Non serious: {_non_serious_centroid.shape}, "
              f"Fucking around: {_fucking_around_centroid.shape}")
    
    return _very_serious_centroid, _standard_centroid, _non_serious_centroid, _fucking_around_centroid


def classify_sentiment(transcript, model):
    """
    Classify transcript sentiment into one of 4 categories: very_serious, standard, non_serious, fucking_around.
    Returns tuple: (classification, similarities_dict)
    """
    if not transcript.strip():
        return "standard", {}
    
    # Load precomputed centroids
    very_serious_centroid, standard_centroid, non_serious_centroid, fucking_around_centroid = load_precomputed_centroids()
    
    # Convert transcript to vector
    test_vec = sent_vec(transcript, model)
    
    # Calculate similarities to all 4 centroids
    similarities = {
        "very_serious": cosine_similarity(test_vec, very_serious_centroid),
        "standard": cosine_similarity(test_vec, standard_centroid),
        "non_serious": cosine_similarity(test_vec, non_serious_centroid),
        "fucking_around": cosine_similarity(test_vec, fucking_around_centroid)
    }
    
    # Find the category with highest similarity
    classification = max(similarities, key=similarities.get)
    
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
        print("[FSM]: Warning - No transcript file found, using empty transcript")
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
    if classification == "very_serious":
        audio_file = "post_confession_message.wav"  # TODO: Replace with very_serious_response.wav
        log_description = "very serious response"
    elif classification == "standard":
        audio_file = "post_confession_message.wav"  # TODO: Replace with standard_response.wav
        log_description = "standard response"
    elif classification == "non_serious":
        audio_file = "post_confession_message.wav"  # TODO: Replace with non_serious_response.wav
        log_description = "non serious response"
    elif classification == "fucking_around":
        audio_file = "post_confession_message.wav"  # TODO: Replace with fucking_around_response.wav
        log_description = "fucking around response"
    else:
        # Fallback
        audio_file = "post_confession_message.wav"
        log_description = "default response"
    
    # Play the appropriate response
    if not play_and_log(audio_file, str(engine.audio_dir), engine.sensor, engine.session_id, log_description):
        raise engine.SessionAbort
    
    print(f"[FSM] Played {classification} response - moving to post confession info request")
    return S.POST_CONFESSION_INFO_REQUEST 