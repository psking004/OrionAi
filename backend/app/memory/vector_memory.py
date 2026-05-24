import math
import re
from typing import List, Dict, Tuple


def tokenize(text: str) -> List[str]:
    text = text.lower()
    text = re.sub(r"[^a-z0-9\s]", " ", text)
    return [t for t in text.split() if len(t) > 2]


def tf_idf_vector(tokens: List[str], vocabulary: List[str]) -> List[float]:
    freq: Dict[str, int] = {}
    for t in tokens:
        freq[t] = freq.get(t, 0) + 1

    vec = []
    total = len(tokens) or 1
    for word in vocabulary:
        tf = freq.get(word, 0) / total
        vec.append(tf)
    return vec


def cosine_similarity(a: List[float], b: List[float]) -> float:
    if len(a) != len(b):
        return 0.0
    dot = sum(x * y for x, y in zip(a, b))
    mag_a = math.sqrt(sum(x * x for x in a))
    mag_b = math.sqrt(sum(y * y for y in b))
    if mag_a == 0 or mag_b == 0:
        return 0.0
    return dot / (mag_a * mag_b)


def find_similar(
    query: str,
    documents: List[Dict],
    text_key: str = "content",
    top_k: int = 5,
    threshold: float = 0.1,
) -> List[Dict]:
    if not documents:
        return []

    query_tokens = tokenize(query)
    doc_tokens = [tokenize(doc.get(text_key, "")) for doc in documents]

    vocabulary = list(set(query_tokens + [t for tokens in doc_tokens for t in tokens]))
    if not vocabulary:
        return documents[:top_k]

    query_vec = tf_idf_vector(query_tokens, vocabulary)
    scored = []
    for i, (doc, tokens) in enumerate(zip(documents, doc_tokens)):
        doc_vec = tf_idf_vector(tokens, vocabulary)
        score = cosine_similarity(query_vec, doc_vec)
        if score >= threshold:
            scored.append((score, i, doc))

    scored.sort(key=lambda x: x[0], reverse=True)
    return [doc for _, _, doc in scored[:top_k]]


def extract_key_concepts(text: str, top_n: int = 10) -> List[str]:
    tokens = tokenize(text)
    stopwords = {
        "the", "and", "for", "are", "was", "were", "this", "that", "have",
        "had", "not", "but", "can", "will", "with", "from", "they", "their",
        "what", "when", "which", "who", "how", "all", "any", "each", "into",
        "its", "more", "been", "also", "just", "than", "then", "there", "out",
    }
    freq: Dict[str, int] = {}
    for t in tokens:
        if t not in stopwords and len(t) > 3:
            freq[t] = freq.get(t, 0) + 1

    sorted_words = sorted(freq.keys(), key=lambda w: freq[w], reverse=True)
    return sorted_words[:top_n]
