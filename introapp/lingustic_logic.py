import re
from collections import Counter

# -------------------------------
# CONFIG
# -------------------------------

FILLER_WORDS = {
    "um", "uh", "er", "erm", "hmm", "ah", "uhh", "umm", "like", "you", "know"
}

FIRST_PERSON_PRONOUNS = {
    "i", "me", "my", "mine", "myself"
}

NEGATIVE_WORDS = {
    "not", "never", "no", "none", "nothing",
    "didn't", "don't", "wasn't", "weren't", "can't", "won't"
}

# Hesitation markers - words/phrases indicating hesitation and stalling
HESITATION_MARKERS = {
    "um", "uh", "er", "erm", "hmm", "uhh", "umm",
    "well", "so", "basically", "honestly", "frankly", "actually"
}

# Uncertainty markers - words/phrases indicating doubt and uncertainty
UNCERTAINTY_MARKERS = {
    "maybe", "probably", "might", "could", "seem", "seems",
    "appear", "appears", "possibly", "I think", "I believe", "I guess",
    "kind of", "sort of", "rather", "somewhat", "perhaps", "allegedly"
}

# Contradiction and negation markers
CONTRADICTION_MARKERS = {
    "but", "however", "yet", "although", "though", "meanwhile",
    "on the other hand", "conversely", "instead", "rather"
}

# Vague language
VAGUE_MARKERS = {
    "thing", "things", "stuff", "whatever", "something", "anything",
    "everything", "somewhere", "nowhere", "somehow", "anyway"
}

WEIGHTS = {
    "word_count": 0.15,
    "fillers": 0.25,
    "first_person": 0.15,
    "negative_words": 0.15,
    "repetition": 0.10,
    "hesitation": 0.10,
    "uncertainty": 0.10
}

# THRESHOLDS
LIE_THRESHOLD = 0.45
TRUTH_THRESHOLD = 0.25


# -------------------------------
# UTILITIES
# -------------------------------

def clean_text(text):
    text = text.lower()
    text = re.sub(r"[^a-z\s']", " ", text)
    return text


def tokenize(text):
    return text.split()


# Helper to find specific marker words in text
def find_markers(words, markers):
    """Find which marker words appear in the text"""
    found = []
    for i, word in enumerate(words):
        if word in markers:
            found.append(word)
    return list(set(found))  # Return unique markers


def analyze_hesitation_markers(text):
    """Detect hesitation patterns in text"""
    words = tokenize(clean_text(text))
    hesitation_words = find_markers(words, HESITATION_MARKERS)
    
    # Check for trailing patterns (ellipsis, multiple spaces)
    has_ellipsis = "..." in text
    short_answer = len(words) < 5
    
    analysis = {
        "markers_found": hesitation_words,
        "count": len(hesitation_words),
        "has_ellipsis": has_ellipsis,
        "short_answer": short_answer
    }
    
    return analysis


def analyze_uncertainty_markers(text):
    """Detect uncertainty patterns in text"""
    words = tokenize(clean_text(text))
    uncertainty_words = find_markers(words, UNCERTAINTY_MARKERS)
    vague_words = find_markers(words, VAGUE_MARKERS)
    
    analysis = {
        "uncertainty_markers": uncertainty_words,
        "vague_markers": vague_words,
        "total_markers": len(uncertainty_words) + len(vague_words)
    }
    
    return analysis


def analyze_contradiction_markers(text):
    """Detect contradiction patterns in text"""
    words = tokenize(clean_text(text))
    contradiction_words = find_markers(words, CONTRADICTION_MARKERS)
    
    # Check for self-contradictory patterns (positive followed by negation)
    has_negation_contradiction = False
    for i in range(len(words) - 1):
        if words[i] in NEGATIVE_WORDS and i > 0:
            has_negation_contradiction = True
            break
    
    analysis = {
        "markers_found": contradiction_words,
        "count": len(contradiction_words),
        "negation_pattern": has_negation_contradiction
    }
    
    return analysis


def analyze_contextual_response(question, answer):
    """Analyze answer in context of question - check if answer is relevant"""
    q_words = set(tokenize(clean_text(question)))
    a_words = set(tokenize(clean_text(answer)))
    
    # Calculate overlap between question and answer
    overlap = q_words.intersection(a_words)
    overlap_ratio = len(overlap) / len(q_words) if q_words else 0
    
    # Low overlap might indicate evasion
    is_evasive = overlap_ratio < 0.2
    
    return {
        "overlap_ratio": round(overlap_ratio, 2),
        "is_evasive": is_evasive,
        "common_words": list(overlap)
    }



# -------------------------------
# SCORING FUNCTIONS
# -------------------------------

def word_count_score(words):
    wc = len(words)

    if wc <= 5:
        return 1.0
    elif wc <= 10:
        return 0.7
    elif wc <= 25:
        return 0.4
    else:
        return 0.2


def filler_word_score(words):
    count = sum(1 for w in words if w in FILLER_WORDS)

    if count >= 3:
        return 1.0
    elif count == 2:
        return 0.7
    elif count == 1:
        return 0.4
    else:
        return 0.0


def first_person_score(words):
    count = sum(1 for w in words if w in FIRST_PERSON_PRONOUNS)
    ratio = count / len(words) if len(words) > 0 else 0

    if ratio > 0.20:
        return 1.0
    elif ratio > 0.10:
        return 0.6
    elif ratio > 0.05:
        return 0.3
    else:
        return 0.0


def negative_word_score(words):
    count = sum(1 for w in words if w in NEGATIVE_WORDS)

    if count >= 3:
        return 1.0
    elif count == 2:
        return 0.7
    elif count == 1:
        return 0.4
    else:
        return 0.0


def repetition_score(words):
    counts = Counter(words)
    repeated_words = [w for w, c in counts.items() if c > 1]

    if len(repeated_words) >= 4:
        return 1.0
    elif len(repeated_words) == 3:
        return 0.7
    elif len(repeated_words) == 2:
        return 0.4
    elif len(repeated_words) == 1:
        return 0.2
    else:
        return 0.0


def hesitation_score(text):
    """Score based on hesitation markers"""
    analysis = analyze_hesitation_markers(text)
    score = 0.0
    
    if analysis["count"] >= 3:
        score = 1.0
    elif analysis["count"] >= 2:
        score = 0.7
    elif analysis["count"] >= 1:
        score = 0.5
    
    if analysis["has_ellipsis"]:
        score += 0.2
    
    if analysis["short_answer"]:
        score += 0.3
    
    return min(score, 1.0)


def uncertainty_score(text):
    """Score based on uncertainty markers"""
    analysis = analyze_uncertainty_markers(text)
    total = analysis["total_markers"]
    
    if total >= 5:
        return 1.0
    elif total >= 3:
        return 0.7
    elif total >= 1:
        return 0.4
    else:
        return 0.0


# -------------------------------
# MAIN FUNCTION
# -------------------------------

def check_linguistic_test(text, question=None):
    """
    Analyze text for deception indicators
    
    Args:
        text: The transcript/answer text to analyze
        question: (Optional) The question asked - if provided, enables contextual analysis
    
    Returns:
        Dictionary with lie_score, classification, and detailed markers
    """
    words = tokenize(clean_text(text))

    if not words:
        return {
            "lie_score": 0.0,
            "classification": "NO_DATA",
            "error": "Invalid text"
        }

    # Calculate all scores
    scores = {
        "word_count": word_count_score(words),
        "fillers": filler_word_score(words),
        "first_person": first_person_score(words),
        "negative_words": negative_word_score(words),
        "repetition": repetition_score(words),
        "hesitation": hesitation_score(text),
        "uncertainty": uncertainty_score(text)
    }

    # Base lie score
    lie_score = sum(scores[k] * WEIGHTS[k] for k in scores)

    # BOOST: multiple deception signals
    strong_signals = sum(1 for v in scores.values() if v >= 0.6)
    if strong_signals >= 3:
        lie_score += 0.15

    lie_score = min(lie_score, 1.0)

    # Determine classification
    if lie_score >= LIE_THRESHOLD:
        label = "LIE"
    else:
        label = "TRUTH"

    # Detailed marker analysis
    hesitation_analysis = analyze_hesitation_markers(text)
    uncertainty_analysis = analyze_uncertainty_markers(text)
    contradiction_analysis = analyze_contradiction_markers(text)
    
    # Contextual analysis if question provided
    contextual_analysis = None
    if question:
        contextual_analysis = analyze_contextual_response(question, text)

    return {
        "lie_score": round(lie_score, 3),
        "classification": label,
        "word_count": len(words),
        "scores": scores,
        
        # Detailed patterns
        "hesitation": {
            "markers": hesitation_analysis["markers_found"],
            "count": hesitation_analysis["count"],
            "has_trailing": hesitation_analysis["has_ellipsis"],
            "is_short": hesitation_analysis["short_answer"]
        },
        "uncertainty": {
            "uncertainty_words": uncertainty_analysis["uncertainty_markers"],
            "vague_words": uncertainty_analysis["vague_markers"],
            "total_markers": uncertainty_analysis["total_markers"]
        },
        "contradiction": {
            "markers": contradiction_analysis["markers_found"],
            "has_negation_pattern": contradiction_analysis["negation_pattern"]
        },
        
        # Contextual info (if question provided)
        "contextual": contextual_analysis
    }


