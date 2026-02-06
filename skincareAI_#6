# LESSON 3: Text Preprocessing
# This is the foundation of NLP - cleaning and standardizing text

import re # regular expressions for text cleaning
from collections import Counter

from sentence_transformers import SentenceTransformer, util
model = SentenceTransformer('all-MiniLM-L6-v2')

from collections import defaultdict # for product score and reasons (less if statements as keys are created on the go)

# User Profile Class to store user info
class UserProfile:
    def __init__(self):
        self.skin_type = None
        self.concerns = []
        self.goals = []
        
        self.confidence = {}
        
    def add_skin_type(self, skin_type):
        self.skin_type = skin_type
    
    def add_concern(self, concern):
        if concern not in self.concerns:
            self.concerns.append(concern)
                
    def add_goal(self, goal):
        if goal not in self.goals:
            self.goals.append(goal)
    
    def add_confidence(self, label, score):
        if label not in self.confidence:
            self.confidence[label] = min(score, 0.85) # cap confidence to 0.85 to avoid overconfidence
        else:
            self.confidence[label] = max(self.confidence[label], min(score, 0.85))  

# Function to determine what to ask next based on missing info one at a time in user profile
def what_to_ask_next(question_number):
    if question_number == 1:
        return "Tell me about your skin type. How would you describe it? "
    elif question_number == 2:
        return "What concerns do you have about your skin? "
    elif question_number == 3:
        return "What are your skincare goals? "
    else:
        return "Thanks for sharing!\n"


# Function to generate follow-up question based on missing info
def generate_followup_questions(missing_info):
    if missing_info == "skin_type":
        return "Can you tell me more about your skin? For example, is it oily, dry, or a mix of both? "
    elif missing_info == "concerns":
        return "Can you tell me more about specific skin concerns are you hoping to address? For example, would it be acne, aging, sensitivity, or something else? "
    elif missing_info == "goals":
        return "Can you tell me more about your main skincare goals? Do you hope to improve hydration, reduce wrinkles, or something else? "
    
    
# Function to check if there is missing info after extracting from user input if so we call generate_followup_questions
def check_missing_info_and_ask(user_profile):
    attempt = 0
    while True:
        if not user_profile.skin_type:
            missing = "skin_type"
        elif not user_profile.concerns:
            missing = "concerns"
        elif not user_profile.goals:
            missing = "goals"
        else:
            break
        
        question = generate_followup_questions(missing)
        
        print(f"Bot: {question}")
        user_input = input("You: ")
        print()
        
        if missing == "skin_type":
            skin_types = extract_all_skin_type_semantics(user_input)
            for item in skin_types:
                user_profile.add_skin_type(item["label"])
                user_profile.add_confidence(item["label"], item["score"])
        elif missing == "concerns":
            concerns = extract_all_concerns_semantics(user_input)
            for item in concerns:
                user_profile.add_concern(item["label"])
                user_profile.add_confidence(item["label"], item["score"])
        elif missing == "goals":
            goals = extract_all_goals_semantics(user_input)
            for item in goals:
                user_profile.add_goal(item["label"])
                user_profile.add_confidence(item["label"], item["score"])

        attempt += 1
        if attempt >= 3: # if after 3 attempts we still have missing info we break and move on
            print("Bot: No worries, we can move on with the information we have and adjust later if needed.")
            if not user_profile.skin_type:
                user_profile.add_skin_type("general") # default
            if not user_profile.concerns:
                user_profile.add_concern("general")
            if not user_profile.goals:
                user_profile.add_goal("general") 
            break

        
# ==================== ML Semantics ====================

def extract_all_skin_type_semantics(text, min_similarity=0.35):
        
    # embed user text
    user_emb = model.encode(text)
    
    references = {
        "oily": (
            "oily and greasy skin with excess sebum production, skin that becomes shiny quickly, "
            "especially in the t zone, enlarged or visible pores, prone to acne, blackheads, "
            "whiteheads, and frequent breakouts due to excess oil"
        ),

        "dry": (
            "dry and dehydrated skin lacking moisture, tight or uncomfortable feeling, "
            "flaky or rough texture, peeling skin, dull appearance, and skin that may feel "
            "itchy or sensitive due to moisture loss"
        ),

        "combination": (
            "combination skin with both oily and dry areas, oily or shiny t zone such as the "
            "forehead nose and chin, while cheeks or other areas feel dry or normal, "
            "mixed skin concerns that vary across different parts of the face"
        ),

        "sensitive": (
            "sensitive and reactive skin that becomes red easily, prone to irritation, "
            "burning or stinging sensations, inflammation, itching, and discomfort after "
            "using skincare products or exposure to environmental triggers"
        ),

        "normal": (
            "normal and balanced skin that is neither oily nor dry, healthy skin with "
            "even texture, minimal sensitivity, small pores, clear appearance, and "
            "generally comfortable skin without frequent breakouts or dryness"
        )
    }

    
    # detected_types
    scores = []
    
    for label, references_text in references.items():
        # embed reference text
        ref_emb = model.encode(references_text)
        similarity = util.cos_sim(user_emb, ref_emb).item()
        scores.append((label, similarity))
    
    # sort scores by similarity (1.0 is most similar, )
    scores.sort(key=lambda x: x[1], reverse=True)
    
    best_score = scores[0][1]
    
    if best_score < min_similarity:
        return []
    else: 
        return [
            {"label": scores[0][0], "score": round(best_score, 3)}
        ]

def extract_all_concerns_semantics(text, min_similarity=0.35, margin=0.08):
    user_emb = model.encode(text)
    
    references = {
        "acne": (
            "acne prone skin with frequent pimples, breakouts, whiteheads, blackheads, "
            "cystic acne, hormonal acne, clogged pores, excess oil production, "
            "inflamed blemishes, painful spots, and recurring breakouts on the face or body"
        ),

        "aging": (
            "signs of skin aging such as wrinkles, fine lines, crow's feet, "
            "sagging skin, loss of firmness, reduced elasticity, dull appearance, "
            "uneven texture, mature skin concerns, and age related skin changes"
        ),

        "sensitivity": (
            "sensitive and reactive skin that becomes red easily, irritated, itchy, "
            "burning or stinging sensations, inflammation, discomfort after skincare products, "
            "skin barrier damage, rosacea prone or easily inflamed skin"
        ),

        "sun protection": (
            "concern about sun exposure and uv damage, need for sunscreen or spf, "
            "preventing sunburn, protecting skin from uv rays, photoaging, "
            "hyperpigmentation from sun exposure, and daily sun protection habits"
        ),
        
        "hydration": (
            "concern about dry and dehydrated skin, need for deep hydration and moisture, "
            "relieving tightness or flakiness, improving skin barrier function, achieving plump, "
            "and dewy skin, and maintaining long term skin hydration"
        ),
        
        "brightening": (
            "concern about dull skin and uneven skin tone, need for brightening and radiance, "
            "improving skin glow, reducing dark spots or hyperpigmentation, and achieving a more even skin tone"
            "post-inflammatory hyperpigmentation from acne, sun spots, melasma, discoloration"
        )
    }
    
    raw_scores = {}
    scores = []
    
    # calculate similarity score between reference text and user text
    for label, references_text in references.items():
        ref_emb = model.encode(references_text)
        raw_scores[label] = util.cos_sim(user_emb, ref_emb).item()
        
    # holds best score
    best_score = max(raw_scores.values())
    
    detected = {}
    for label, score in raw_scores.items():
        # keep labels that are:
        # 1. reasonably similar (min similarity)
        # 2. close to the best score (margin)
        # purpose: Find other labels that are also good matches (multi answers)
        # raw_score: similarity score
        # relative_score: score compared to best score (0.0 to 1.0)
        if score >= min_similarity and (best_score - score) <= margin:
            detected[label] = {
                "raw_score": score,
                "relative_score": score / best_score if best_score > 0 else 0
            }
    
    # what is weight I am not sure
    if not detected:
        return {"detected": {}, "weights": {}}
    
    # Create normalized weight (only for distribution within category)
    # Come back later as unsure what I am doing actually
    
    return [
        {"label": label, "score": round(score, 3)}
        for label, score in detected
    ]
        
       
    
def extract_all_goals_semantics(text, min_similarity=0.35, margin=0.08):
    user_emb = model.encode(text)
    
    references = {
        "clear_skin": (
            "goal of achieving clear and smooth skin, reducing acne, breakouts, "
            "blemishes, dark spots, and uneven texture, wanting clean looking skin "
            "with fewer imperfections and a more refined appearance"
        ),

        "anti_aging": (
            "goal of preventing or reducing signs of aging such as wrinkles, fine lines, "
            "loss of firmness, sagging skin, and dullness, aiming for youthful, "
            "plump, and healthy looking skin over time"
        ),

        "hydration": (
            "goal of deeply hydrating and moisturizing the skin, improving skin moisture "
            "levels, achieving plump, soft, dewy skin, relieving dryness or tightness, "
            "and maintaining a healthy skin barrier"
        ),

        "protection": (
            "goal of protecting the skin from environmental damage such as sun exposure, "
            "uv rays, pollution, and free radicals, preventing sunburn, premature aging, "
            "and long term skin damage through daily protection"
        ),

        "soothe": (
            "goal of soothing and calming irritated or sensitive skin, reducing redness, "
            "inflammation, itching, or discomfort, and restoring comfort to stressed or "
            "reactive skin"
        ),
        
        "brighten": (
            "goal of achieving brighter, more radiant skin, reducing dullness, uneven skin tone, "
            "dark spots, and hyperpigmentation, aiming for luminous, glowing complexion "
            "with improved clarity and even-toned appearance"
        )
    }
    scores = []
    
    for label, references_text in references.items():
        ref_emb = model.encode(references_text)
        similarity = util.cos_sim(user_emb, ref_emb).item()
        scores.append((label, similarity))
            
        
    scores.sort(key=lambda x: x[1], reverse=True)
    
    best_score = scores[0][1]
    detected = []
    
    for label, score in scores:
        if score >= min_similarity and (best_score - score) <= margin:
            detected.append((label, score))

    if not detected:
        return []
    else:        
        return [
            {"label": label, "score": round(score, 3)}
            for label, score in detected
        ]


# ==================== ML Semantics END ====================

# ======================== PLANING =========================
# routine building before product recommendations
# cleanser
# moisturizer
# sunscreen
# treatment/serum
Product_Rules = {
    "cleanser": {
        "essential": True,
        "max": 1,
        "order": 1
    },
    "toner": {
        "essential": False,
        "max": 1,
        "order": 2
    },
    "treatment": {
        "essential": False,
        "max": 3,
        "order": 3,
        "subcategories": {
            "active_serum": {
                "max": 2,
                "requires_concern": []
            },
            "hydrating_serum": {
                "max": 2,
            },
            "targeted_treatment": {
                "max": 1,
                "requires_concern": ["acne", "brightening"]
            }
        }
    },
    "moisturizer": {
        "essential": True,
        "max": 1,
        "order": 4
    },
    "facial_oil": {
        "essential": False,
        "max": 1,
        "order": 5
    },
    "sunscreen": {
        "essential": True,
        "max": 1,
        "order": 6,
        "require_am": True        
    },
}

Product_Knowledge = {
    "active_serum": {
        "conflicts": ["exfoliating_toner"],
        "frequency": "1x daily max",
        "notes": "Alternate strong actives",
    }
}


# now i made the product_rules but am not sure how to use it yet
# product_rules should be used for building the routine with the recommended products
# product_rule is not done yet as i did not take into account the user profile when building the routine
# use rule base system to build routine based on user profile 

# role activation logic
def build_routine(context):
    plan = []
    
    for product_type, rules in Product_Rules.items():
        if rules.get("require_am") and context["time"] != "a.m":
            continue
        if rules.get("requires_concern") and context["concerns"] == ["general"]:
            continue
        
        # determine number of products based of if essential
        if rules["essential"]:
            count = 1
        else:
            count = rules["max_optional"]
        
        plan.append({
            "category": product_type,
            "count": count,
            "order": rules.get("order", 999) # default order is 999 if not specified
        })
        
        
    
    
        
    
        
        
    
    

# =================== PLANING END ==========================


# ================ PRODUCT RECOMMEDATIONS ==================
# Data structure to hold product info
Product_Info = {
    "Salicylic Acid Cleanser": {
        "type": "Cleanser",
        "description": "Salicylic acid helps to exfoliate and clear out clogged pores, which is beneficial for oily skin prone to acne and breakouts."
    },
    "Gel Moisturizer": {
        "type": "Moisturizer",
        "description": "Gel moisturizers provide hydration without adding excess oil, making them suitable for oily skin to maintain moisture balance without clogging pores."
    },
    "Rich Cream Moisturizer": {
        "type": "Moisturizer",
        "description": "Rich cream moisturizers are designed to provide intense hydration and nourishment, which is essential for dry skin that lacks moisture and may feel tight or flaky."
    },
    "Hydrating Serum": {
        "type": "Serum",
        "description": "Hydrating serums often contain ingredients like hyaluronic acid that can attract and retain moisture in the skin, making them beneficial for dry skin to boost hydration levels."
    },
    "Barrier Repair Moisturizer": {
        "type": "Moisturizer",
        "description": "Barrier repair moisturizers contain ingredients like ceramides, panthenol, and centella would help strengthen and restore the skin's natural barrier, which is crucial for sensitive skin that is prone to irritation and inflammation."
    },
    "Gentle Fragence-Free Cleanser": {
        "type": "Cleanser",
        "description": "Gentle fragrance-free cleansers are formulated to cleanse the skin without stripping away natural oils or causing irritation, making them ideal for sensitive skin that can react to harsh ingredients."
    },
    "Lightweight Barrier-Supporting Moisturizer": {
        "type": "Moisturizer",
        "description": "Lightweight barrier-supporting moisturizers provide balanced hydration and help maintain the skin's natural barrier without being too heavy or greasy, making them suitable for combination skin that has both oily and dry areas."
    },
    "Broad-Spectrum Sunscreen": {
        "type": "Sunscreen",
        "description": "Broad-spectrum sunscreen SPF 30-50 is essential for protecting the skin from harmful UV rays and preventing sun damage, which is important for maintaining healthy skin regardless of skin type."
    },
    "Lightweight Moisturizer": {
        "type": "Moisturizer",
        "description": "Lightweight moisturizers provide hydration without being too heavy, making them suitable for normal skin to maintain a balanced and healthy complexion."
    },
    "Leave-On Salicylic Acid (BHA)": {
        "type": "Treatment",
        "description": "Leave-on salicylic acid (BHA) products are effective for treating acne because they penetrate deep into the pores to exfoliate and clear out excess oil, dead skin cells, and impurities that can lead to breakouts."
    },
    "Lightweight Non-Comedogenic Moisturizer": {
        "type": "Moisturizer",
        "description": "Lightweight non-comedogenic moisturizers provide necessary hydration without clogging pores, which is important for acne-prone skin to maintain moisture balance while preventing further breakouts."
    },
    "Retinoid Serum": {
        "type": "Serum",
        "description": "Retinoid serums are highly effective for addressing signs of aging such as wrinkles and fine lines because they promote collagen production, increase cell turnover, and improve skin texture and firmness over time."
    },
    "Antioxidant Serum": {
        "type": "Serum",
        "description": "Antioxidant serums containing ingredients like vitamin C, E, and ferulic acid can help to protect skin from environmental damage, reduce inflammation, and improve overall skin health by neutralizing free radicals."
    },
    "Vitamin C Serum": {
        "type": "Serum",
        "description": "Vitamin C serums are effective for brightening the skin and reducing the appearance of dark spots and hyperpigmentation by inhibiting melanin production and providing antioxidant protection."
    }
}

def recommend_products(user_profile):
    # Main recommendation functions
    # Returns ranked list of products, score, reasons
    
    # product -> score
    product_scores = defaultdict(float)
    
    # product -> reason for score
    product_reasons = defaultdict(list)
    
    # +3 means essential for solving the primary problem
    # +2 means very helpful in addressing the key aspects of the problem
    # +1 means somewhat helpful or a nice to have for the problem (optional)
    # ------- Skin Type-------------------------
    for skin_type in user_profile.skin_type:
        # confidence is the score rating from the semantic extraction functions before (0.0 default value incase of future errors)
        confidence = user_profile.confidence.get(skin_type, 0.0) 

        if skin_type == "oily":
            product_scores["Salicylic Acid Cleanser"] += 3 * confidence
            if product_reasons["Salicylic Acid Cleanser"] == []:
                product_reasons["Salicylic Acid Cleanser"].append(Product_Info["Salicylic Acid Cleanser"]["description"])
            
            product_scores["Gel Moisturizer"] += 2 * confidence
            if product_reasons["Gel Moisturizer"] == []:
                product_reasons["Gel Moisturizer"].append(Product_Info["Gel Moisturizer"]["description"])
            
        elif skin_type == "dry":
            product_scores["Rich Cream Moisturizer"] += 3 * confidence
            if product_reasons["Rich Cream Moisturizer"] == []:
                product_reasons["Rich Cream Moisturizer"].append(Product_Info["Rich Cream Moisturizer"]["description"])
            
            product_scores["Hydrating Serum"] += 2 * confidence
            if product_reasons["Hydrating Serum"] == []:
                product_reasons["Hydrating Serum"].append(Product_Info["Hydrating Serum"]["description"])

        elif skin_type == "sensitive":
            product_scores["Barrier Repair Moisturizer"] += 3 * confidence
            if product_reasons["Barrier Repair Moisturizer"] == []:
                product_reasons["Barrier Repair Moisturizer"].append(Product_Info["Barrier Repair Moisturizer"]["description"])
            
            product_scores["Gentle Fragence-Free Cleanser"] += 2 * confidence
            if product_reasons["Gentle Fragence-Free Cleanser"] == []:
                product_reasons["Gentle Fragence-Free Cleanser"].append(Product_Info["Gentle Fragence-Free Cleanser"]["description"])
        elif skin_type == "combination":
            product_scores["Lightweight Barrier-Supporting Moisturizer"] += 3 * confidence
            if product_reasons["Lightweight Barrier-Supporting Moisturizer"] == []:
                product_reasons["Lightweight Barrier-Supporting Moisturizer"].append(Product_Info["Lightweight Barrier-Supporting Moisturizer"]["description"])
            
            product_scores["Salicylic Acid Cleanser"] += 2 * confidence
            if product_reasons["Salicylic Acid Cleanser"] == []:
                product_reasons["Salicylic Acid Cleanser"].append(Product_Info["Salicylic Acid Cleanser"]["description"])   
        elif skin_type == "normal":
            product_scores["Broad-Spectrum Sunscreen"] += 3 * confidence
            if product_reasons["Broad-Spectrum Sunscreen"] == []:
                product_reasons["Broad-Spectrum Sunscreen"].append(Product_Info["Broad-Spectrum Sunscreen"]["description"])
            
            product_scores["Lightweight Moisturizer"] += 2 * confidence
            if product_reasons["Lightweight Moisturizer"] == []:
                product_reasons["Lightweight Moisturizer"].append(Product_Info["Lightweight Moisturizer"]["description"])
            
    
    # ------ Concerns -------------------------
    for concern in user_profile.concerns:
        confidence = user_profile.confidence.get(concern, 0.0)
        if concern == "acne":
            product_scores["Leave-On Salicylic Acid (BHA)"] += 3 * confidence
            if product_reasons["Leave-On Salicylic Acid (BHA)"] == []:
                product_reasons["Leave-On Salicylic Acid (BHA)"].append(Product_Info["Leave-On Salicylic Acid (BHA)"]["description"])
            
            product_scores["Lightweight Non-Comedogenic Moisturizer"] += 2 * confidence
            if product_reasons["Lightweight Non-Comedogenic Moisturizer"] == []:
                product_reasons["Lightweight Non-Comedogenic Moisturizer"].append(Product_Info["Lightweight Non-Comedogenic Moisturizer"]["description"])
        elif concern == "aging":
            product_scores["Retinoid Serum"] += 3 * confidence
            if product_reasons["Retinoid Serum"] == []:
                product_reasons["Retinoid Serum"].append(Product_Info["Retinoid Serum"]["description"])
            
            product_scores["Barrier Repair Moisturizer"] += 2 * confidence
            if product_reasons["Barrier Repair Moisturizer"] == []:
                product_reasons["Barrier Repair Moisturizer"].append(Product_Info["Barrier Repair Moisturizer"]["description"])        
        elif concern == "sensitivity":
            product_scores["Barrier Repair Moisturizer"] += 3 * confidence
            if product_reasons["Barrier Repair Moisturizer"] == []:
                product_reasons["Barrier Repair Moisturizer"].append(Product_Info["Barrier Repair Moisturizer"]["description"])
            
            product_scores["Gentle Fragence-Free Cleanser"] += 2 * confidence
            if product_reasons["Gentle Fragence-Free Cleanser"] == []:
                product_reasons["Gentle Fragence-Free Cleanser"].append(Product_Info["Gentle Fragence-Free Cleanser"]["description"])
        elif concern == "sun protection":
            product_scores["Broad-Spectrum Sunscreen"] += 3 * confidence
            if product_reasons["Broad-Spectrum Sunscreen"] == []:
                product_reasons["Broad-Spectrum Sunscreen"].append(Product_Info["Broad-Spectrum Sunscreen"]["description"])

            product_scores["Antioxidant Serum"] += 2 * confidence
            if product_reasons["Antioxidant Serum"] == []:
                product_reasons["Antioxidant Serum"].append(Product_Info["Antioxidant Serum"]["description"])
                
        elif concern == "hydration":
            product_scores["Rich Cream Moisturizer"] += 3 * confidence
            if product_reasons["Rich Cream Moisturizer"] == []:
                product_reasons["Rich Cream Moisturizer"].append(Product_Info["Rich Cream Moisturizer"]["description"])

            product_scores["Hydrating Serum"] += 2 * confidence
            if product_reasons["Hydrating Serum"] == []:
                product_reasons["Hydrating Serum"].append(Product_Info["Hydrating Serum"]["description"])
        elif concern == "brightening":
            product_scores["Vitamin C Serum"] += 3 * confidence
            if product_reasons["Vitamin C Serum"] == []:
                product_reasons["Vitamin C Serum"].append(Product_Info["Vitamin C Serum"]["description"])
            
            product_scores["Antioxidant Serum"] += 2 * confidence
            if product_reasons["Antioxidant Serum"] == []:
                product_reasons["Antioxidant Serum"].append(Product_Info["Antioxidant Serum"]["description"])

    # ------- Goals -------------------------
    for goal in user_profile.goals:
        confidence = user_profile.confidence.get(goal, 0.0)
        if goal == "clear_skin":
            product_scores["Leave-On Salicylic Acid (BHA)"] += 3 * confidence
            if product_reasons["Leave-On Salicylic Acid (BHA)"] == []:
                product_reasons["Leave-On Salicylic Acid (BHA)"].append(Product_Info["Leave-On Salicylic Acid (BHA)"]["description"])
            
            product_scores["Lightweight Non-Comedogenic Moisturizer"] += 2 * confidence
            if product_reasons["Lightweight Non-Comedogenic Moisturizer"] == []:
                product_reasons["Lightweight Non-Comedogenic Moisturizer"].append(Product_Info["Lightweight Non-Comedogenic Moisturizer"]["description"])
                
        elif goal == "anti_aging":
            product_scores["Retinoid Serum"] += 3 * confidence
            if product_reasons["Retinoid Serum"] == []:
                product_reasons["Retinoid Serum"].append(Product_Info["Retinoid Serum"]["description"])
            
            product_scores["Barrier Repair Moisturizer"] += 2 * confidence
            if product_reasons["Barrier Repair Moisturizer"] == []:
                product_reasons["Barrier Repair Moisturizer"].append(Product_Info["Barrier Repair Moisturizer"]["description"])
                
        elif goal == "hydration":
            product_scores["Rich Cream Moisturizer"] += 3 * confidence
            if product_reasons["Rich Cream Moisturizer"] == []:
                product_reasons["Rich Cream Moisturizer"].append(Product_Info["Rich Cream Moisturizer"]["description"])
            
            product_scores["Hydrating Serum"] += 2 * confidence
            if product_reasons["Hydrating Serum"] == []:
                product_reasons["Hydrating Serum"].append(Product_Info["Hydrating Serum"]["description"])
        elif goal == "protection":
            product_scores["Broad-Spectrum Sunscreen"] += 3 * confidence
            if product_reasons["Broad-Spectrum Sunscreen"] == []:
                product_reasons["Broad-Spectrum Sunscreen"].append(Product_Info["Broad-Spectrum Sunscreen"]["description"])

            product_scores["Antioxidant Serum"] += 2 * confidence
            if product_reasons["Antioxidant Serum"] == []:
                product_reasons["Antioxidant Serum"].append(Product_Info["Antioxidant Serum"]["description"])
                
        elif goal == "soothe":
            product_scores["Barrier Repair Moisturizer"] += 3 * confidence
            if product_reasons["Barrier Repair Moisturizer"] == []:
                product_reasons["Barrier Repair Moisturizer"].append(Product_Info["Barrier Repair Moisturizer"]["description"])

            product_scores["Gentle Fragence-Free Cleanser"] += 2 * confidence
            if product_reasons["Gentle Fragence-Free Cleanser"] == []:
                product_reasons["Gentle Fragence-Free Cleanser"].append(Product_Info["Gentle Fragence-Free Cleanser"]["description"])
        
        elif goal == "brighten":
            product_scores["Vitamin C Serum"] += 3 * confidence
            if product_reasons["Vitamin C Serum"] == []:
                product_reasons["Vitamin C Serum"].append(Product_Info["Vitamin C Serum"]["description"])
            
            product_scores["Antioxidant Serum"] += 2 * confidence
            if product_reasons["Antioxidant Serum"] == []:
                product_reasons["Antioxidant Serum"].append(Product_Info["Antioxidant Serum"]["description"])
    
    results = []
    # sort products by score highest to lowest
    sorted_products = sorted(product_scores.items(), key=lambda x: x[1], reverse=True)
    
    # return the top 3 products with their scores and reasons
    # make sure to only return one moisturizer and cleanser product, duplicate product types are fine for the rest
    # to check for duplicate product types we can create a set to track the types of products we have already included in the results and skip any products that are of the same type as one already included
    
    # rather than using set, I would use Product_Info to check the type of product and only include one moisturizer and cleanser in the results
    # we can do this by checking the type of each product as we iterate through sorted_products and only add if the type is not already included
    for product, score in sorted_products:
        if len(results) >= 3:
            break
        
        product_type = Product_Info[product]["type"]
        # p["product"] return the key use to access Product_Info
        
        if product_type == "Moisturizer":
            if any(Product_Info[p["product"]]["type"] == "Moisturizer" for p in results):
                continue
        elif product_type == "Cleanser":
            if any(Product_Info[p["product"]]["type"] == "Cleanser" for p in results):
                continue
        results.append({
            "product": product,
            "score": round(score, 3),
            "reasons": product_reasons[product]
        })

    return results


# ================= PRODUCT RECOMMENDATIONS END =================
# clean up text
def clean_text(text):
    # clean user text
    text = text.lower() 
    text = re.sub(r'[^a-z0-9\s]', '', text)  # Remove punctuation
    text = re.sub(r'\s+', ' ', text).strip()  # Remove extra spaces
    
    return text

# Main Conservation Function Loop
def have_conversation():
    print("Welcome to the Skincare AI Consultant!\n")
    
    # Create user profile
    user_profile = UserProfile()
    number = 1
        
    # Main Conversation Loop
    while True:
        # Determine what to ask next
        question = what_to_ask_next(number)
        if number <= 3:
            number += 1
        
        # Print question
        print(f"Bot: {question}")
         
        # Get user input
        user_input = input("You: ")
        print() # new line for readability
            
        # Extract information based on the question asked and update user profile
        if question.startswith("Tell me about your skin type"):
            skin_types = extract_all_skin_type_semantics(user_input)
            for item in skin_types:
                user_profile.add_skin_type(item["label"])
                user_profile.add_confidence(item["label"], item["score"])
        elif question.startswith("What concerns do you have about your skin"):
            concerns = extract_all_concerns_semantics(user_input)
            for item in concerns:
                user_profile.add_concern(item["label"])
                user_profile.add_confidence(item["label"], item["score"])
        elif question.startswith("What are your skincare goals"):
            goals = extract_all_goals_semantics(user_input)
            for item in goals:
                user_profile.add_goal(item["label"])
                user_profile.add_confidence(item["label"], item["score"])
        
        
        # Check if any information is missing and update profile
        # Not a very clean way to do this as its a string check - fix later
        elif question.startswith("Thanks for sharing!"): 
            check_missing_info_and_ask(user_profile)
        
            print("Bot: Here is what I gathered:\n")
            print(f"  . Detected Skin Type: {user_profile.skin_type if user_profile.skin_type else 'Not detected'}")
            print(f"  . Detected Concerns: {user_profile.concerns if user_profile.concerns else 'None detected'}")
            print(f"  . Detected Goals: {user_profile.goals if user_profile.goals else 'No goals specified'}")
            
            print("\nWould you like to:")
            print("1. Satifisited with skincare information and move on to the routine")
            print("2. Adjust detected skin type")
            print("3. Adjust detected skin concerns")
            print("4. Adjust detected skin goals")
            user_done = input("Enter 1-4\nYou: ").lower()
            
            if user_done in ["1", "2", "3", "4", "one", "two", "three", "four"]:
                break
            else:
                print("Please choose and answer with one of the number options listed.")
    
    routine_time = ""
    if user_done in ["1", "one"]:
        print("What routine would you like to generate first:\n")
        print("1: Morning a.m routine")
        print("2. Night p.m routine")
        routine_input = input("Enter 1-2\nYou: ").lower()
        
        if routine_input == "1" or "one":
            routine_time = "a.m"
        elif routine_input == "2" or "two":
            routine_time = "p.m"
        
        context = {
            "time": routine_time,
            "skin_type": user_profile.skin_type,
            "concerns": user_profile.concerns,
            "goals": user_profile.goals,
            "max_optional": 1
        }
        
        routine_rule = build_routine(context)

        
    elif user_done in ["2", "two"]:
        # adjust user skin type
        pass
    elif user_done in ["3", "three"]:
        # adjust user skin concern
        pass
    elif user_done in ["4", "four"]:
        # adjust user skin goal
        pass
    

    recommended_products = recommend_products(user_profile)
    
    for product in recommended_products:
        print(f"  . Product: {product['product']}")
        print(f"  . Reasons: {product['reasons']}\n")
        


    
if __name__ == "__main__":
    have_conversation()
    
    
# sematic verbosity 
# EX: I have oily skin
# User 1: My skin get extremely oily throughout the day around my nose and forehead and I constantly feel greasy
# User 2: Both user inputs means the same but due to second input having more descriptive languaage it will have higher semantics scoring.