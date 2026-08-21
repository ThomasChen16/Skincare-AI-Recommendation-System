from operator import index

from embedding_model import get_model
import faiss # for faster similarity search
import numpy as np
import json # get product_info data from json

# ================ PRODUCT RECOMMEDATIONS ==================
# Data structure to hold product info
# open product json file and load product info data
with open("data/product.json", "r") as f:
    Product_Info = json.load(f)

# ============ CATEGORY MAPPING ============
# Bridge between two product "vocabularies":
#   - the routine category keys produced by build_routine() (e.g. "Cleanser")
#   - the "type"/"category" values stored in the product data source.
#
# The live source (data/product.json) already uses canonical lowercase types
# (cleanser, toner, treatment, moisturizer, facial_oil, sunscreen). When the
# app is switched over to the real dataset (data/products_clean.csv), its
# categories are capitalized and differently spelled ("Moisturiser", "Oil",
# "Serum", ...) and MUST go through this map.
DATASET_TO_RULE = {
    # products_clean.csv category -> canonical routine key
    "Cleanser":     "cleanser",
    "Toner":        "toner",
    "Serum":        "treatment",     # dataset lumps all serums under one name
    "Moisturiser":  "moisturizer",   # note British spelling (s, not z)
    "Moisturizer":  "moisturizer",
    "Oil":          "facial_oil",
}

# Routine rule/display names -> canonical key, so the renamed Product_Rules
# keys in routine.py ("Cleanser", "Oil / Facial Oil", ...) all resolve to the
# same canonical token as the dataset mapping above.
RULE_ALIASES = {
    "cleanser":        "cleanser",
    "toner":           "toner",
    "treatment":       "treatment",
    "moisturizer":     "moisturizer",
    "facial_oil":      "facial_oil",
    "facial oil":      "facial_oil",
    "oil":             "facial_oil",
    "oil / facial oil": "facial_oil",
    "oil facial oil":  "facial_oil",
    "sunscreen":       "sunscreen",
}

# Converts a category name to its canonical key for consistent comparisons.
def _canonical(category):
    # Lowercase a category and normalize "Oil / Facial Oil" -> "oil facial oil"
    # so both dataset and routine names can be compared on a shared token.
    value = str(category).strip().lower()
    normalized = " ".join(value.replace("/", " ").replace("&", " ").split())
    return RULE_ALIASES.get(value) or RULE_ALIASES.get(normalized) or normalized

def _matches_category(rule_category, product_type):
    # Translate the data source's category to a canonical routine key
    # (e.g. CSV "Oil" -> "facial_oil"), then compare case-insensitively
    # against the routine's category key.
    data_canonical = DATASET_TO_RULE.get(str(product_type).strip(), str(product_type).strip())
    return _canonical(rule_category) == _canonical(data_canonical)


# function to recommend products for a given product type category 
# Checks whether a product's dataset type matches the requested routine category
# by converting both values to their canonical category keys.
def recommend_for_product_type(category, context, faiss_scores, count = 1):
    
    normalized_faiss_scores = normalize_faiss_scores(faiss_scores)

    # Fill one product type at a time based on the routine blueprint and product rules
    candidates = []
    for product_name, product_details in Product_Info.items():
        if _matches_category(category, product_details["type"]):
            candidates.append((product_name, product_details))
    
    # calculate coverage score for each candidate product based on how well it addresses the user's skin type, concerns, and goals
    scored_candidates = []
    for category_product_name, category_product_details in candidates:
        # rule score on how many categories the product cover
        rule_score = calculate_coverage(category_product_details, context)
        
        # get normalized FAISS similarity score (default 0 if missing)
        semantic_score = normalized_faiss_scores.get(category_product_name, 0)
        
        # combine both
        final_score = (rule_score * 0.7) + (semantic_score * 0.3)
        
        scored_candidates.append({
            "product": category_product_name,
            "info": category_product_details,
            "score": final_score
        })
    
    
    # covert scores to normalization (0.0 - 1.0)
    scored_candidates = normalize_scores(scored_candidates)
    
    # sort candidates with new normalize score
    scored_candidates.sort(key=lambda x: x["normalized_score"], reverse=True)
    
    results = []
    # [:count] to get top products based on count specified in Build Routine
    for product in scored_candidates[:count]:
        results.append({
            "product": product["product"],
            "type": product["info"]["type"],
            "raw_score": product["score"],
            "score": product["normalized_score"],
            "reason": generate_reasoning(product["info"], context)
        })
        print(product["product"], product["score"], product["normalized_score"])
        
    return results

# Configuration based weight scores
WEIGHTS = {
    "skin_type": 3.0,
    "concerns": 2.0,
    "goals": 1.0
}

_product_embeddings = []
_product_metadata = []
_product_index = None

def load_product_embeddings():
    global _product_embeddings, _product_metadata, _product_index
    
    if _product_index is None:
        print("Loading product embeddings...")
        
        model = get_model() # get loaded model
        
        # create product and metadata embeddings for product item info
        # loop through name and info for each product 
        for name, info in Product_Info.items():
            # holds text info
            # add more text to increase text/sentence quality before embedding
            text = f"""
                {info['description']}
                Suitable for {', '.join(info['skin_types_addressed'])} skin.
                Helps with {', '.join(info['concerns_addressed'])}.
                Support goals like {', '.join(info['goals_addressed'])}.
            """
            
            # embed text description
            emb = model.encode(text)
            
            # add embedding to product_embedding
            _product_embeddings.append(emb)
            # add product name
            _product_metadata.append(name)

        # build index
        xb = np.array(_product_embeddings).astype("float32")
        # normalize for cosine similarity
        faiss.normalize_L2(xb)

        # build the FAISS index and add the embeddings
        _product_index = faiss.IndexFlatIP(xb.shape[1])
        _product_index.add(xb)
        
        print("Product embeddings loaded!\n")
    
    return _product_index

def get_faiss_scores(context):
    query = f"""
        My skin type is {context['skin_type']}.
        My skincare concerns include: {', '.join(context['concerns'])}.
        My skincare goals include: {', '.join(context['goals'])}.
        """
        
    model = get_model() # get loaded model 
    emb = model.encode(query)
    emb = np.array([emb]).astype("float32")
    faiss.normalize_L2(emb)
    
    index = load_product_embeddings()
    scores, indices = index.search(emb, len(_product_metadata))
    
    result = {}
    for score, idx, in zip(scores[0], indices[0]):
        result[_product_metadata[idx]] = float(score)
        
    return result

# function to calculate coverage score for how well a product addresss the user's skin type, concerns, and goals based on Product_Info and user profile
def calculate_coverage(product, context):
    score = 0
    # skin type match is most important 
    if context["skin_type"] in product["skin_types_addressed"]:
        score += WEIGHTS["skin_type"]
    else:
        score -= WEIGHTS["skin_type"] * 0.5 # penalize if skin type not address but still effective
    
    product_concerns = set(product["concerns_addressed"])
    user_concerns = set(context["concerns"])
    # intersection
    concern_matches = product_concerns & user_concerns
    score += len(concern_matches) * WEIGHTS["concerns"]
    
    # find how many goals the product addressed that the user has
    product_goals = set(product["goals_addressed"])
    user_goals = set(context["goals"])
    
    goal_matches = product_goals & user_goals
    # * 1 because goal match is less important than concern and skin type match
    score += len(goal_matches) * WEIGHTS["goals"]
    
    return score

# Converts raw scores to min-max normalization score (0.0 - 1.0)
def normalize_scores(products):
    # prevent empty product error
    if not products:
        return products
    
    # holds all scores
    scores = [p["score"] for p in products]
    
    # grab min and max
    max_score = max(scores)
    min_score = min(scores)
    
    # if only 1 product, set its normalized score to its raw score
    if len(products) == 1:
        products[0]["normalized_score"] = products[0]["score"]
        return products
    
    for p in products:
        # if only 1 score set it as 1.0
        if max_score == min_score:
            p["normalized_score"] = 1.0
        else:
            # (current - min) / (max - min)
            # help determine its overall order in the list of scores
            p["normalized_score"] = (p["score"] - min_score) / (max_score - min_score)
    
    return products

# Convert faiss score to min-max normalized score (0.0 - 1.0)
def normalize_faiss_scores(scores_dict):
    # prevent empty scores_dict error
    if not scores_dict:
        return scores_dict
    
    # hold all values
    values = list(scores_dict.values())
    
    # grab min and max
    max_value = max(values)
    min_value = min(values)
    
    norm = {}
    for key, value in scores_dict.items():
        # if only 1 value set it as 1.0
        if max_value == min_value:
            norm[key] = 1.0
        else:
            # (current - min) / (max - min)
            # help determine its overall order in the list of scores
            norm[key] = (value - min_value) / (max_value - min_value)
    
    return norm

def generate_reasoning(info, context):
    # Generate reasoning for why a product is recommended based on how it addresses the user's skin type, concerns, and goals
    reasoning = []
    if context["skin_type"] in info["skin_types_addressed"]:
        reasoning.append(f"Addresses your skin type ({context['skin_type']}).")
    else:
        reasoning.append(f"Not ideal for your skin type: {context['skin_type']}, but may still provide some benefits.")
    
    concern_matches = set(info["concerns_addressed"]) & set(context["concerns"])
    if concern_matches:
        reasoning.append(f"Targets your skin concerns: {', '.join(concern_matches)}.")
        reasoning.append(f"Specifically, {info['description']}")
    else:
        reasoning.append(f"Does not directly target your specific concerns: {', '.join(context['concerns'])}, but may still offer general skincare benefits.")
    
    goal_matches = set(info["goals_addressed"]) & set(context["goals"])
    if goal_matches:
        reasoning.append(f"Helps you work towards your skincare goals: {', '.join(goal_matches)}.")
    else:
        reasoning.append(f"May not directly align with your specific goals: {', '.join(context['goals'])} but could still contribute to overall skin health.")
    
    return " ".join(reasoning)
    

# ================= PRODUCT RECOMMENDATIONS END =================