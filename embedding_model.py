from sentence_transformers import SentenceTransformer, util

_model = None

def load_model():
    global _model
    
    # Load model only once and reuse across files
    if _model is None:
        print("Loading AI model...")
        _model = SentenceTransformer("all-MiniLM-L6-v2")
        print("Ready!\n")

    return _model

    
def get_model():
    if _model is None:
        raise RuntimeError("Model has not been loaded yet.")
    
    return _model
