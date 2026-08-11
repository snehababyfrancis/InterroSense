# =====================================
# FACE IMAGE TESTING – MOBILE NET MODEL
# =====================================

import numpy as np
from tensorflow.keras.preprocessing import image
from tensorflow.keras.models import load_model

# -------------------------------------
# CONFIG
# -------------------------------------
MODEL_PATH = r"introapp\mobilenet_face_lie_detection.h5"
IMG_SIZE = 224

# -------------------------------------
# LOAD TRAINED MODEL
# -------------------------------------
model = load_model(MODEL_PATH)
print("✅ Face MobileNet model loaded successfully")

# -------------------------------------
# IMAGE PREDICTION FUNCTION
# -------------------------------------
def predict_image(img_path):
    """
    Predict lie/truth from a single face image
    """
    img = image.load_img(img_path, target_size=(IMG_SIZE, IMG_SIZE))
    img = image.img_to_array(img) / 255.0
    img = np.expand_dims(img, axis=0)

    prob = model.predict(img, verbose=0)[0][0]

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

