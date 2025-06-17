# fsm/states/confession_analyze_sentiment.py

import os
import numpy as np
import pickle
from session_states import S

import fsm.common  # Setup paths to util directory

from general_util import play_and_log
from log import log_event

# Path to precomputed centroid files
SENTIMENT_DIR = os.path.join(fsm.common.UTIL_DIR, "sentiment")
SERIOUS_CENTROID_FILE = os.path.join(SENTIMENT_DIR, "serious_centroid.pkl")
SILLY_CENTROID_FILE = os.path.join(SENTIMENT_DIR, "silly_centroid.pkl")

# Threshold for classification
CLASSIFICATION_THRESHOLD = 0.02

# Cached centroids (loaded once)
_serious_centroid = None
_silly_centroid = None


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
    Load precomputed centroids from pickle files.
    """
    global _serious_centroid, _silly_centroid
    
    if _serious_centroid is None or _silly_centroid is None:
        print("Loading precomputed sentiment centroids...")
        
        # Check if centroid files exist
        if not os.path.exists(SERIOUS_CENTROID_FILE):
            raise FileNotFoundError(f"Serious centroid file not found: {SERIOUS_CENTROID_FILE}")
        if not os.path.exists(SILLY_CENTROID_FILE):
            raise FileNotFoundError(f"Silly centroid file not found: {SILLY_CENTROID_FILE}")
        
        # Load centroids
        with open(SERIOUS_CENTROID_FILE, 'rb') as f:
            _serious_centroid = pickle.load(f)
        
        with open(SILLY_CENTROID_FILE, 'rb') as f:
            _silly_centroid = pickle.load(f)
        
        print(f"Loaded centroids - Serious: {_serious_centroid.shape}, Silly: {_silly_centroid.shape}")
    
    return _serious_centroid, _silly_centroid


def classify_sentiment(transcript, model):
    """
    Classify transcript sentiment as serious, silly, or neutral.
    Returns tuple: (classification, gap_score)
    """
    if not transcript.strip():
        return "neutral", 0.0
    
    # Load precomputed centroids
    serious_centroid, silly_centroid = load_precomputed_centroids()
    
    # Convert transcript to vector
    test_vec = sent_vec(transcript, model)
    
    # Calculate similarities
    sim_serious = cosine_similarity(test_vec, serious_centroid)
    sim_silly = cosine_similarity(test_vec, silly_centroid)
    
    # Calculate gap (positive = serious, negative = silly)
    gap = sim_serious - sim_silly
    
    # Classify based on threshold
    if gap > CLASSIFICATION_THRESHOLD:
        classification = "serious"
    elif gap < -CLASSIFICATION_THRESHOLD:
        classification = "silly"
    else:
        classification = "neutral"
    
    return classification, gap


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
        print("FSM: Warning - No transcript file found, using empty transcript")
        transcript = ""
    else:
        with open(transcript_path, 'r', encoding='utf-8') as f:
            transcript = f.read().strip()
        print(f"FSM: Loaded transcript for sentiment analysis: '{transcript[:100]}{'...' if len(transcript) > 100 else ''}'")
    
    # Perform sentiment classification
    log_event(engine.session_id, "sentiment_analysis_start")
    print("FSM: Analyzing confession sentiment with fastText...")
    
    classification, gap = classify_sentiment(transcript, engine.fasttext_model)
    
    # Log the results
    log_event(engine.session_id, "confession_classified", {
        "classification": classification,
        "gap": gap,
        "transcript_length": len(transcript)
    })
    
    print(f"FSM: Sentiment classification: {classification} (gap: {gap:.4f})")
    
    # Determine which audio file to play based on classification
    # For now, using the same file as requested, but setting up the infrastructure
    if classification == "serious":
        audio_file = "post_confession_message.wav"  # TODO: Replace with serious_response.wav
        log_description = "serious response"
    elif classification == "silly":
        audio_file = "post_confession_message.wav"  # TODO: Replace with silly_response.wav
        log_description = "silly response"
    else:  # neutral
        audio_file = "post_confession_message.wav"  # TODO: Replace with neutral_response.wav
        log_description = "neutral response"
    
    # Play the appropriate response
    if not play_and_log(audio_file, str(engine.audio_dir), engine.sensor, engine.session_id, log_description):
        raise engine.SessionAbort
    
    print(f"FSM: Played {classification} response - moving to post confession info request")
    return S.POST_CONFESSION_INFO_REQUEST 