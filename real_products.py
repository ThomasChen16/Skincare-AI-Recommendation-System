# Build the real-product FAISS index and the matching functions
import pandas as pd
import numpy as np
import faiss
from embedding_model import get_model
from product_recommendation import _matches_category, _canonical

_real_products = None
_real_product_embeddings = []
_real_product_metadata = []
_real_product_index = None


# ---------------------------------------------------------------------------
# Sunscreen special case: the real-product dataset has no "Sunscreen" category,
# so SPF products are filed under Moisturiser/Serum/Oil/etc. The strict category
# check (_matches_category) therefore rejects every candidate for the routine's
# "Sunscreen" slot. Detect sunscreens by SPF branding or UV-filter ingredients
# instead, and accept them for the Sunscreen category only.

# UV-filter actives that mark a product as a sunscreen.
SUNSCREEN_FILTERS = (
    'homosalate',
    'octocrylene',
    'ethylhexyl salicylate',          # octisalate
    'butyl methoxydibenzoylmethane',  # avobenzone
    'benzophenone',                   # oxybenzone family
    'phenylbenzimidazole sulfonic acid',
    'zinc oxide',                         # mineral filters
    'bis-ethylhexyloxyphenol methoxyphenyl triazine',      # Tinosorb S
    'methylene bis-benzotriazolyl tetramethylbutylphenol', # Tinosorb M
    'diethylhexyl butamido triazone',                      # Uvasorb HEB
)

# Dataset categories that legitimately carry face sunscreen products. Only these
# are accepted for ingredient-based detection, so body wash/bath salts/masks
# (which can contain trace pigments or filters) never appear in the Sunscreen tab.
FACE_SPF_CATEGORIES = {'Moisturiser', 'Moisturizer', 'Serum', 'Oil', 'Toner'}


def _is_sunscreen_product(candidate):
    # Strong signal: the product name advertises SPF protection.
    name = str(candidate.get('product') or '').lower()
    if 'no spf' in name or 'without spf' in name:
        return False
    if 'spf' in name or 'sunscreen' in name or 'sun screen' in name:
        return True

    # Otherwise require a UV-filter active AND a plausible face category.
    if candidate.get('category') not in FACE_SPF_CATEGORIES:
        return False
    ingredients = str(candidate.get('ingredients') or '').lower()
    return any(f in ingredients for f in SUNSCREEN_FILTERS)


# Category gate used in find_real_product_matches: strict category match first,
# then the sunscreen content-based fallback for the routine's Sunscreen slot.
def _is_sunscreen_match(rule_category, candidate):
    return _canonical(rule_category) == 'sunscreen' and _is_sunscreen_product(candidate)

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
        if _matches_category(category, candidate['category']) or _is_sunscreen_match(category, candidate):
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
    matched_terms = [c for c in context.get('concerns', []) if c.lower() in str(real_product['ingredients']).lower()]
    if matched_terms:
        return f"Ingredients relevant to: {', '.join(matched_terms)}"
    
    # No generic fallback needed - the frontend no longer shows this reason line.
    return None
    