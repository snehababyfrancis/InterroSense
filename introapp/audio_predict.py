import os
import numpy as np
import librosa
# from moviepy.editor import VideoFileClip
from tensorflow.keras.models import load_model

# ------------------------------------------
# CONFIG
# ------------------------------------------
AUDIO_MODEL_PATH = r"introapp\audio_cnn_lie_detection.h5"
N_MFCC = 40
SR = 16000

# ------------------------------------------
# LOAD MODEL
# ------------------------------------------
audio_model = load_model(AUDIO_MODEL_PATH)
print("✅ Audio CNN model loaded successfully")

# ------------------------------------------
# AUDIO → MFCC FUNCTION (ROBUST)
# ------------------------------------------
def audio_to_mfcc(input_path):
    """

    - .wav (audio)

    Output MFCC shape: (40,)
    """

    ext = os.path.splitext(input_path)[1].lower()


    if ext == ".wav":
        y, sr = librosa.load(input_path, sr=SR)

    else:
        raise ValueError("Unsupported file format. Use .mp4 or .wav")

    # -------- MFCC EXTRACTION --------
    mfcc = librosa.feature.mfcc(
        y=y,
        sr=sr,
        n_mfcc=N_MFCC
    )

    # Mean over time (MUST match training)
    mfcc = np.mean(mfcc.T, axis=0)

    return mfcc

# ------------------------------------------
# PREDICTION FUNCTION
# ------------------------------------------
def predict_audio(input_path):
    mfcc = audio_to_mfcc(input_path)

    # CNN input shape: (1, 40, 1)
    mfcc = mfcc.reshape(1, N_MFCC, 1)

    prob = audio_model.predict(mfcc, verbose=0)[0][0]

    # Add calibration to reduce bias - more conservative approach
    calibrated_prob = (prob - 0.5) * 0.8 + 0.5  # Reduce amplification
    calibrated_prob = max(0.2, min(0.8, calibrated_prob))  # Wider range
    
    if calibrated_prob > 0.5:
        return {
            "prediction": "Lie",
            "confidence": round(float(calibrated_prob * 100), 2)
        }
    else:
        return {
            "prediction": "Truth",
            "confidence": round(float((1 - calibrated_prob) * 100), 2)
        }

