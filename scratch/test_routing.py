"""Consolidated router diagnostic and evaluation utility.

Combines functionality from:
- test_router.py
- test_10_faqs.py
- test_new_faqs.py
- test_scores.py
- test_max_agg.py
- test_inspect.py
- inspect_router_config.py
- inspect_scores_internal.py
- calculate_similarities.py
"""

import sys
import numpy as np
from pathlib import Path

# Add project root directory to Python path
sys.path.append(str(Path(__file__).parent.parent / "app"))
from router import router, encoder

def run_config_inspection():
    print("=" * 60)
    print("ROUTER CONFIGURATION INSPECTION")
    print("=" * 60)
    print("top_k:", router.top_k)
    print("score_threshold:", router.score_threshold)
    print("Number of routes:", len(router.routes))
    for r in router.routes:
        print(f"  Route: {r.name}, Utterances: {len(r.utterances)}")
    
    if router.index is not None:
        index = router.index
        print("Index type:", type(index))
        if hasattr(index, "index") and index.index is not None:
            print("Index embeddings shape:", index.index.shape)
            print("Index routes length:", len(index.routes))
            print("Index utterances length:", len(index.utterances))
    print()

def test_basic_routing():
    print("=" * 60)
    print("BASIC ROUTING TEST")
    print("=" * 60)
    queries = [
        "tell me about return policy",
        "tell me about refund policy",
        "general refund policy",
        "Do I get discount with the HDFC credit card?",
    ]
    for query in queries:
        res = router(query)
        print(f"Query: '{query}' -> Route: {res.name} (Score: {res.score if hasattr(res, 'score') else 'N/A'})")
    print()

def test_10_faqs():
    print("=" * 60)
    print("10 FAQ ROUTING TEST")
    print("=" * 60)
    original_top_k = router.top_k
    router.top_k = 1
    
    queries = [
        "How can I create an account?",
        "What payment methods do you accept?",
        "How can I track my order?",
        "Can I cancel my order?",
        "How long does shipping take?",
        "Do you offer international shipping?",
        "What should I do if my package is lost or damaged?",
        "Can I change my shipping address after placing an order?",
        "How can I contact customer support?",
        "Do you offer gift wrapping services?"
    ]
    for query in queries:
        res = router(query)
        print(f"Query: '{query}' -> Route: {res.name}")
        
    router.top_k = original_top_k
    print()

def test_new_faqs():
    print("=" * 60)
    print("5 NEW FAQ ROUTING TEST")
    print("=" * 60)
    original_top_k = router.top_k
    router.top_k = 1
    
    queries = [
        "What is your price matching policy?",
        "Can I order without creating an account?",
        "Do you have a loyalty program?",
        "Can I return a product if it was purchased with a gift card?",
        "Can we make payment in Cash after delivery?"
    ]
    for query in queries:
        res = router(query)
        print(f"Query: '{query}' -> Route: {res.name}")
        
    router.top_k = original_top_k
    print()

def cosine_similarity(v1, v2):
    dot_prod = np.dot(v1, v2)
    norm_v1 = np.linalg.norm(v1)
    norm_v2 = np.linalg.norm(v2)
    return dot_prod / (norm_v1 * norm_v2)

def calculate_similarities():
    print("=" * 60)
    print("COSINE SIMILARITY ANALYSIS WITH INDEX UTTERANCES")
    print("=" * 60)
    if router.index is None or not hasattr(router.index, "index") or router.index.index is None:
        print("No index available for similarity calculation.")
        return
        
    index_embeddings = router.index.index
    index_routes = router.index.routes
    index_utterances = router.index.utterances
    
    queries = [
        "tell me about return policy",
        "tell me about refund policy",
        "general refund policy",
        "Do I get discount with the HDFC credit card?",
    ]
    
    for query in queries:
        print(f"Query: '{query}'")
        query_emb = np.array(encoder([query])[0])
        
        similarities = []
        for emb, route, utterance in zip(index_embeddings, index_routes, index_utterances):
            sim = cosine_similarity(query_emb, emb)
            similarities.append((sim, route, utterance))
        
        similarities.sort(key=lambda x: x[0], reverse=True)
        print("  Top 3 matches:")
        for sim, route, utterance in similarities[:3]:
            print(f"    Similarity: {sim:.4f} -> Route: {route} | Utterance: '{utterance}'")
    print()

def inspect_scores_internal():
    print("=" * 60)
    print("INTERNAL ROUTER SCORES")
    print("=" * 60)
    queries = [
        "tell me about return policy",
        "tell me about refund policy",
        "general refund policy",
        "Do I get discount with the HDFC credit card?",
    ]
    
    for query in queries:
        print(f"Query: {query}")
        try:
            vector = encoder([query])[0]
            scores, routes = router.index.query(vector, top_k=5)
            print("  Index query result:")
            for score, route in zip(scores, routes):
                print(f"    Route: {route}, Score: {score}")
        except Exception as e:
            print("  Error running index.query:", e)
            
        if hasattr(router, "_score_routes"):
            try:
                scores = router._score_routes([vector])
                print("  _score_routes result:", scores)
            except Exception as e:
                print("  Error running _score_routes:", e)
    print()

if __name__ == "__main__":
    run_config_inspection()
    test_basic_routing()
    test_10_faqs()
    test_new_faqs()
    if len(sys.argv) > 1 and sys.argv[1] == "--diagnostics":
        calculate_similarities()
        inspect_scores_internal()
