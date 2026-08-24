# Build the real-product FAISS index and the matching functions
import pandas as pd
import numpy as np
import faiss
from embedding_model import get_model
from product_recommendation import _matches_category

_real_products = None
_real_product_embeddings = []
_real_product_metadata = []
_real_product_index = None

# load real products from CSV
def load_real_products(path="data/products_clean.csv"):
    global _real_products
    if _real_products is None:
        df = pd.read_csv(path)
        _real_products = []
        
        for _, row in df.iterrows():
            _real_products.append({
                'product': row['product'],
                'brand': row.get('brand_guess'),
                'category': row['category'], # necessary fields
                'ingredients': row['ingredients'],
                'price': row.get('price'), # optional fields
                'url': row.get('product_url')
            })
            
    return _real_products

# Load embeddings for all real products and build FAISS index for similarity search
def load_real_product_embeddings():
    global _real_product_embeddings, _real_product_metadata, _real_product_index
    
    if _real_product_index is None:
        print("Loading real product embeddings...")
        # Initialize the embedding model
        model = get_model()
        # Load real products from CSV
        products = load_real_products()
        
        # Generate embeddings for each product
        for product in products:
            # Combine category and ingredients into a single text for embedding
            text = f"{product['category']}. Ingredients: {product['ingredients']}"
            # Encode the text using the embedding model
            emb = model.encode(text)
            # Store the embedding vector
            _real_product_embeddings.append(emb)
            # Store the product metadata for later retrieval
            _real_product_metadata.append(product)
            
        # Convert embeddings list to numpy array with float32 dtype
        xb = np.array(_real_product_embeddings).astype('float32')
        # Normalize embeddings to unit length (L2 normalization)
        faiss.normalize_L2(xb)
        # Create a FAISS index with Flat distance metric
        _real_product_index = faiss.IndexFlatL2(xb.shape[1])
        # Add all embeddings to the index
        _real_product_index.add(xb)
        
        print("Real product embeddings loaded!\n")
        
    # Return the built FAISS index
    return _real_product_index

# find product matches between product and real products
def find_real_product_matches(placeholder_product_info, category, context, top_n=20):
    index = load_real_product_embeddings()
    model = get_model()
    
    # search query is the information you provide to a search system so it knows what you are looking for
    category_label = category or placeholder_product_info.get('type', '')
    description = placeholder_product_info.get('description', '')
    query_text = f"{category_label}. {description}".strip()
    
    # converts the text obtain from the query into embeddings
    emb = model.encode(query_text)
    emb = np.array([emb]).astype('float32')
    faiss.normalize_L2(emb)
    
    scores, indices = index.search(emb, len(_real_product_metadata))
    
    # compare the embeddings created from products in products.clean.csv
    matches = []
    for score, idx in zip(scores[0], indices[0]):
        candidate = _real_product_metadata[idx]
        if _matches_category(category, candidate['category']):
            matches.append({
                'product': candidate['product'],
                'brand': candidate['brand'],
                'category': candidate['category'],
                'ingredients': candidate['ingredients'],
                'price': candidate['price'],
                'url': candidate['url'],
                'score': float(score),
                'reason': explain_match(candidate, context)
            })
        
        if len(matches) >= top_n:
            break
        
    
    return matches

# Explain why a real product was selected as a match.
def explain_match(real_product, context):
    # Check whether any user concerns appear in the product ingredients.
    matched_terms = [c for c in context['concerns'] if c.lower() in real_product['ingredients'].lower()]
    if matched_terms:
        return f"Ingredients relevant to: {', '.join(matched_terms)}"
    
    # Use a general explanation when no concern-specific ingredient matches.
    return "Matched based on overall similarity to the recommended products"
    