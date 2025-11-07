from rapidfuzz import fuzz
import unicodedata
import re

def normalize(text):
    """Nettoie une chaîne pour comparaison floue"""
    text = text.lower()
    text = unicodedata.normalize("NFKD", text)
    text = "".join(c for c in text if not unicodedata.combining(c))
    text = re.sub(r"[^a-z0-9]+", " ", text)
    return text.strip()

def fuzzy_score(query, candidate):
    """Score 0-100 basé sur RapidFuzz (plus précis que le mot commun)"""
    norm_query = normalize(query)
    norm_candidate = normalize(candidate)
    score = fuzz.ratio(norm_query, norm_candidate)
    return score
