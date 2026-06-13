from operator import index

from embedding_model import get_model
import faiss # for faster similarity search
import numpy as np

# ================ PRODUCT RECOMMEDATIONS ==================
# Data structure to hold product info
Product_Info = {
    # ==================== EXISTING PRODUCTS (KEPT) ====================
    "Salicylic Acid Cleanser": {
        "type": "cleanser",
        "skin_types_addressed": ["oily", "combination"],
        "concerns_addressed": ["acne", "brightening"],
        "goals_addressed": ["clear_skin"],
        "description": "Salicylic acid helps to deeply cleanse pores, reduce excess oil, and exfoliate dead skin cells, making it effective for treating acne and improving skin clarity for oily and combination skin types."
    },
    "Gel Moisturizer": {
        "type": "moisturizer",
        "skin_types_addressed": ["oily", "combination"],
        "concerns_addressed": ["hydration"],
        "goals_addressed": ["hydration"],
        "description": "Gel moisturizers provide hydration without adding excess oil, making them suitable for oily skin to maintain moisture balance without clogging pores."
    },
    "Rich Cream Moisturizer": {
        "type": "moisturizer",
        "skin_types_addressed": ["dry"],
        "concerns_addressed": ["hydration"],
        "goals_addressed": ["hydration"],
        "description": "Rich cream moisturizers are designed to provide intense hydration and nourishment, which is essential for dry skin that lacks moisture and may feel tight or flaky."
    },
    "Hydrating Serum": {
        "type": "serum",
        "skin_types_addressed": ["dry", "sensitive"],
        "concerns_addressed": ["hydration"],
        "goals_addressed": ["hydration"],
        "description": "Hydrating serums often contain ingredients like hyaluronic acid that can attract and retain moisture in the skin, making them beneficial for dry skin to boost hydration levels."
    },
    "Barrier Repair Moisturizer": {
        "type": "moisturizer",
        "skin_types_addressed": ["sensitive"],
        "concerns_addressed": ["sensitivity"],
        "goals_addressed": ["soothe"],
        "description": "Barrier repair moisturizers contain ingredients like ceramides, panthenol, and centella would help strengthen and restore the skin's natural barrier, which is crucial for sensitive skin that is prone to irritation and inflammation."
    },
    "Gentle Fragrance-Free Cleanser": {
        "type": "cleanser",
        "skin_types_addressed": ["sensitive"],
        "concerns_addressed": ["sensitivity"],
        "goals_addressed": ["soothe"],
        "description": "Gentle fragrance-free cleansers are formulated to cleanse the skin without stripping away natural oils or causing irritation, making them ideal for sensitive skin that can react to harsh ingredients."
    },
    "Lightweight Barrier-Supporting Moisturizer": {
        "type": "moisturizer",
        "skin_types_addressed": ["combination"],
        "concerns_addressed": ["sensitivity", "hydration"],
        "goals_addressed": ["soothe", "hydration"],
        "description": "Lightweight barrier-supporting moisturizers provide balanced hydration and help maintain the skin's natural barrier without being too heavy or greasy, making them suitable for combination skin that has both oily and dry areas."
    },
    "Broad-Spectrum Sunscreen": {
        "type": "sunscreen",
        "skin_types_addressed": ["oily", "dry", "combination", "sensitive", "normal"],
        "concerns_addressed": ["sun protection"],
        "goals_addressed": ["protection"],
        "description": "Broad-spectrum sunscreen SPF 30-50 is essential for protecting the skin from harmful UV rays and preventing sun damage, which is important for maintaining healthy skin regardless of skin type."
    },
    "Lightweight Moisturizer": {
        "type": "moisturizer",
        "skin_types_addressed": ["normal"],
        "concerns_addressed": ["hydration"],
        "goals_addressed": ["hydration"],
        "description": "Lightweight moisturizers provide hydration without being too heavy, making them suitable for normal skin to maintain a balanced and healthy complexion."
    },
    "Leave-On Salicylic Acid (BHA)": {
        "type": "treatment",
        "skin_types_addressed": ["oily", "combination"],
        "concerns_addressed": ["acne"],
        "goals_addressed": ["clear_skin"],
        "description": "Leave-on salicylic acid (BHA) products are effective for treating acne because they penetrate deep into the pores to exfoliate and clear out excess oil, dead skin cells, and impurities that can lead to breakouts."
    },
    "Lightweight Non-Comedogenic Moisturizer": {
        "type": "moisturizer",
        "skin_types_addressed": ["oily", "combination"],
        "concerns_addressed": ["acne", "hydration"],
        "goals_addressed": ["clear_skin", "hydration"],
        "description": "Lightweight non-comedogenic moisturizers provide necessary hydration without clogging pores, which is important for acne-prone skin to maintain moisture balance while preventing further breakouts."
    },
    "Retinoid Serum": {
        "type": "serum",
        "skin_types_addressed": ["oily", "dry", "combination", "sensitive", "normal"],
        "concerns_addressed": ["aging"],
        "goals_addressed": ["anti_aging"],
        "description": "Retinoid serums are highly effective for addressing signs of aging such as wrinkles and fine lines because they promote collagen production, increase cell turnover, and improve skin texture and firmness over time."
    },
    "Antioxidant Serum": {
        "type": "serum",
        "skin_types_addressed": ["oily", "dry", "combination", "sensitive", "normal"],
        "concerns_addressed": ["aging", "sun protection"],
        "goals_addressed": ["anti_aging", "protection"],
        "description": "Antioxidant serums containing ingredients like vitamin C, E, and ferulic acid can help to protect skin from environmental damage, reduce inflammation, and improve overall skin health by neutralizing free radicals."
    },
    "Vitamin C Serum": {
        "type": "serum",
        "skin_types_addressed": ["oily", "dry", "combination", "sensitive", "normal"],
        "concerns_addressed": ["brightening", "sun protection"],
        "goals_addressed": ["brighten", "protection"],
        "description": "Vitamin C serums are effective for brightening the skin and reducing the appearance of dark spots and hyperpigmentation by inhibiting melanin production and providing antioxidant protection."
    },
    
    # 1. ACNE - Second treatment (already have Salicylic Acid, now add Benzoyl Peroxide)
    "Benzoyl Peroxide Spot Treatment": {
        "type": "treatment",
        "skin_types_addressed": ["oily", "combination"],
        "concerns_addressed": ["acne"],
        "goals_addressed": ["clear_skin"],
        "description": "Benzoyl peroxide kills acne-causing bacteria (C. acnes) and helps to unclog pores. Use as a spot treatment for inflamed breakouts. Not for sensitive or dry skin types."
    },
    
    # 2. AGING - Add a peptide treatment (Retinoid already exists)
    "Peptide Firming Serum": {
        "type": "serum",
        "skin_types_addressed": ["dry", "normal", "combination", "sensitive"],
        "concerns_addressed": ["aging"],
        "goals_addressed": ["anti_aging"],
        "description": "Peptides signal the skin to produce more collagen and elastin, improving firmness and reducing fine lines without irritation, making them suitable for sensitive skin that cannot tolerate retinoids."
    },
    
    # 3. SENSITIVITY - Add a dedicated soothing treatment (existing products are cleanser/moisturizer)
    "Centella Asiatica Soothing Ampoule": {
        "type": "treatment",
        "skin_types_addressed": ["sensitive", "dry", "combination"],
        "concerns_addressed": ["sensitivity"],
        "goals_addressed": ["soothe"],
        "description": "A concentrated ampoule with centella asiatica (cica), madecassoside, and green tea extract to rapidly calm redness, stinging, and inflammation. Ideal for reactive or compromised skin barriers."
    },
    
    # 4. DEHYDRATION - MISSING CONCERN (dehydration is lack of water, not oil)
    "Hyaluronic Acid + B5 Hydration Treatment": {
        "type": "serum",
        "skin_types_addressed": ["oily", "dry", "combination", "sensitive", "normal"],
        "concerns_addressed": ["dehydration"],
        "goals_addressed": ["hydration"],
        "description": "A treatment serum with multiple weights of hyaluronic acid and vitamin B5 that draws water into the skin and holds it there. Crucial for dehydrated skin (which can be oily or dry)."
    },
    
    # 5. HYPERPIGMENTATION - MISSING CONCERN
    "Tranexamic Acid + Kojic Acid Dark Spot Corrector": {
        "type": "treatment",
        "skin_types_addressed": ["normal", "oily", "combination"],
        "concerns_addressed": ["hyperpigmentation"],
        "goals_addressed": ["brighten"],
        "description": "A targeted treatment combining tranexamic acid, kojic acid, and niacinamide to inhibit melanin production and fade post-inflammatory hyperpigmentation (PIH), melasma, and sun spots without irritation."
    },
    
    # 6. SUN_DAMAGE - Add a repair treatment (sunscreen prevents, this repairs)
    "Niacinamide + Licorice Root Repair Treatment": {
        "type": "serum",
        "skin_types_addressed": ["oily", "dry", "combination", "sensitive", "normal"],
        "concerns_addressed": ["sun_damage"],
        "goals_addressed": ["brighten", "protection"],
        "description": "Niacinamide (vitamin B3) helps repair UV-induced DNA damage, reduces sunburn cells, and improves barrier function. Licorice root extract fades existing sun spots and calms inflammation."
    }
}

# function to recommend products for a given product type category 
def recommend_for_product_type(category, context, faiss_scores, count = 1):
    
    normalized_faiss_scores = normalize_faiss_scores(faiss_scores)

    # Fill one product type at a time based on the routine blueprint and product rules
    candidates = []
    for product_name, product_details in Product_Info.items():
        if product_details["type"] == category:
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