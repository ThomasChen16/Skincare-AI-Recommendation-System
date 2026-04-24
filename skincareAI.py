from collections import Counter
from shlex import join
import random # random number generator
import json # for saving userProfile data
import faiss # for faster similarity search
import numpy as np

# read json file
#with open("profile.json", "r") as f:
#    data = json.load(f)
    
# modify json file
#data["users"]["1003"] = {"name": "Charile", "age": 30}

# write back json file
#with open("profile.json", "w") as f:
#    json.dump(data, f, index=4)

# exit virtual environment: deactivate
# re-enter virtual environment: venv\Scripts\activate
# check to see if you are in the right environment: python -c "import sys; print(sys.executable)"

from sentence_transformers import SentenceTransformer, util
print("Loading AI model...")
model = SentenceTransformer('all-MiniLM-L6-v2')
print("Ready!\n")


from collections import defaultdict # for product score and reasons (less if statements as keys are created on the go)

# User Profile Class to store user info
class UserProfile:
    def __init__(self):
        self.unique_id = 0
        self.name = None
        self.skin_type = []
        self.concerns = []
        self.goals = []
        self.am_routine = []
        self.pm_routine = []
    
    
    def add_skin_type(self, skin_type, update=False):
        # update unused for now, just to prevent TypeError
        self.skin_type = skin_type
    
    def add_concern(self, concern, update=False):
        # if update is true we override previous concerns with new concern else we append to concerns list
        if update:
            self.concerns = [concern]
        elif concern not in self.concerns:
            self.concerns.append(concern)
                
    def add_goal(self, goal, update=False):
        if update:
            self.goals = [goal]
        elif goal not in self.goals:
            self.goals.append(goal)
    
    def add_routine(self, routine, time):
        if time == "a.m":
           self.am_routine = routine
        elif time == "p.m":
            self.pm_routine = routine
        

# Function to determine what to ask next based on missing info one at a time in user profile
def what_to_ask_next(user_profile):
    if not user_profile.skin_type:
        return ("Tell me about your skin type. How would you describe it? ", "skin_type")
    elif not user_profile.concerns:
        return ("What concerns do you have about your skin? ", "concerns")
    elif not user_profile.goals:
        return ("What are your skincare goals? ", "goals")
    else:
        return None

def adjust_user_profile(user_profile, aspect):
    # update user profile based on aspect (skin type, concerns, goals) and new user input
    print(f"Bot: Let's adjust your {aspect}. Please provide the updated information.")
    user_input = input("You: ")
    print(f"DEBUG: Raw input = '{user_input}'")
    print()

    # skintype easily updated as its one label
    if aspect == "skin_type":
        user_profile.add_skin_type(extract_semantics(user_input, "skin_type", debug=True))
        
        # follow up questions if user input doesn't give enough info
        retry_extract(user_profile, "skin_type", "I couldn't quite detect your skin type from that. Can you tell me more about your skin? For example, is it oily, dry, or a mix of both?", user_profile.add_skin_type)
    # update = True to handle new user input as override of previous info instead of appending to it
    elif aspect == "concerns":
        concerns = extract_semantics(user_input, "concerns")
        for item in concerns:
            user_profile.add_concern(item, update=True)
        
        
        # follow up questions if user input doesn't give enough info
        retry_extract(user_profile, "concerns", "Can you tell me more about specific skin concerns are you hoping to address? For example, would it be acne, aging, sensitivity, or something else?", user_profile.add_concern, update=True)
    elif aspect == "goals":
        goals = extract_semantics(user_input, "goals")
        for item in goals:
            user_profile.add_goal(item, update=True)
        
        # follow up questions if user input doesn't give enough info
        retry_extract(user_profile, "goals", "Can you tell me more about your main skincare goals? Do you hope to improve hydration, reduce wrinkles, or something else?", user_profile.add_goal, update=True)

# ==================== ML Semantics ====================

# Refernces description for each skin type, concern, and goal to compare user input to for semantic similarity
references_groups = {
    "skin_type": {
        "oily": [
            "My skin gets very oily and shiny throughout the day",
            "I have greasy skin with visible large pores",
            "My face produces excess oil especially in the T-zone",
            "My skin feels slick and oily a few hours after washing",
            "I struggle with oil buildup and shine on my face"
        ],

        "dry": [
            "My skin feels dry, tight, and flaky",
            "I have rough skin that lacks moisture",
            "My face feels tight after washing and gets flaky",
            "My skin is dehydrated and uncomfortable",
            "I deal with dryness and peeling skin"
        ],

        "combination": [
            "My T-zone is oily but my cheeks are dry",
            "I have combination skin with both oily and dry areas",
            "My forehead and nose get shiny but cheeks feel tight",
            "My skin has uneven oil distribution depending on area",
            "Some parts of my face are oily while others are dry"
        ],

        "sensitive": [
            "My skin is very sensitive and reacts easily",
            "I get redness and irritation from products",
            "My skin burns, stings, or becomes inflamed easily",
            "I have reactive skin that gets irritated quickly",
            "My skin is prone to redness and discomfort"
        ],

        "normal": [
            "My skin is stable without major issues",
            "I don’t experience much oiliness or dryness",
            "My skin feels comfortable most of the time",
            "I rarely have breakouts or irritation",
            "My skin is generally consistent and balanced"
        ]
    },

    "concerns": {
        "acne": [
            "I have acne and frequent breakouts",
            "My skin gets pimples and clogged pores",
            "I struggle with blackheads and whiteheads",
            "I get recurring breakouts and blemishes",
            "My pores get clogged and cause acne"
        ],

        "aging": [
            "I am concerned about aging and wrinkles",
            "I have fine lines and loss of firmness",
            "My skin is starting to sag and lose elasticity",
            "I want to reduce wrinkles and signs of aging",
            "My skin looks older with visible lines"
        ],

        "sensitivity": [
            "My skin gets red and irritated easily",
            "I experience inflammation and skin reactions",
            "My skin is easily triggered by products or weather",
            "I deal with redness and skin irritation often",
            "My skin feels inflamed and reactive"
        ],

        "dehydration": [
            "My skin feels dehydrated and tight",
            "I lack moisture and my skin looks dull",
            "My skin feels dry even when it produces oil",
            "I have water loss and my skin lacks hydration",
            "My skin looks dull and feels tight from dehydration"
        ],

        "hyperpigmentation": [
            "I have dark spots and uneven skin tone",
            "My skin has discoloration and pigmentation",
            "I want to reduce dark marks and patches",
            "I deal with melasma or post-acne marks",
            "My skin tone is uneven with visible spots"
        ],

        "sun_damage": [
            "I am worried about sun damage and UV exposure",
            "My skin gets sunburned easily",
            "I want to prevent photoaging from the sun",
            "My skin shows signs of sun damage",
            "I need protection from UV rays"
        ]
    },

    "goals": {
        "clear_skin": [
            "I want clear skin without breakouts",
            "My goal is to reduce acne and blemishes",
            "I want smoother skin with fewer pimples",
            "I want to prevent clogged pores and breakouts",
            "I want clean and acne-free skin"
        ],

        "anti_aging": [
            "I want to reduce wrinkles and fine lines",
            "My goal is firmer and more youthful skin",
            "I want to improve elasticity and firmness",
            "I want to slow down signs of aging",
            "I want smoother skin with fewer lines"
            "I want my skin to look young again"
        ],

        "hydration": [
            "I want hydrated and moisturized skin",
            "My goal is soft, plump, and dewy skin",
            "I want to improve my skin’s moisture levels",
            "I want to fix dryness and dehydration",
            "I want my skin to feel soft and hydrated"
        ],

        "protection": [
            "I want to protect my skin from damage",
            "My goal is to prevent sun and environmental damage",
            "I want to shield my skin from UV rays",
            "I want to strengthen my skin barrier",
            "I want long-term skin protection"
        ],

        "soothe": [
            "I want to calm my skin and reduce irritation",
            "My goal is to reduce redness and inflammation",
            "I want to soothe sensitive and reactive skin",
            "I want my skin to feel less irritated",
            "I want to reduce discomfort and redness"
        ],

        "brighten": [
            "I want brighter and more radiant skin",
            "My goal is to even out my skin tone",
            "I want to reduce dullness and improve glow",
            "I want to fade dark spots and discoloration",
            "I want glowing and luminous skin"
        ]
    }
}

reference_embeddings = {}

# create reference embedding for each skin type, concern, and goal by averaging the embeddings of the reference descriptions for each label in the category
for group, labels in references_groups.items():
    # create empty dictionary for each group
    reference_embeddings[group] = {}
    
    # loop through each label and reference text in the group and create embedding for the reference text and store in reference_embedding dictionary
    for label, ref_text in labels.items():
        # if ref_text is a list we take the average of the embeddings for the list of reference text to get one embedding for the label
        if isinstance(ref_text, list):
            embeddings = model.encode(ref_text)
            reference_embeddings[group][label] = embeddings.mean(axis=0)
        # already one embedding
        else:
            reference_embeddings[group][label] = model.encode(ref_text)

all_embeddings = []
metadata = []

# 1 embedding for each reference text
# create metadata embeddings list to store the category and label for each embedding
for category, labels in references_groups.items():
    # loop through each label and text in the category and create embedding for the text
    for label, texts in labels.items():
        embs = model.encode(texts, convert_to_tensor=True)
        # store each embedding in all_embeddings list and store its category and label in metadata
        for emb in embs:
            all_embeddings.append(emb.cpu().numpy())
            metadata.append((category, label))
    
        
xb = np.array(all_embeddings).astype("float32")

# normalize for cosine similarity
faiss.normalize_L2(xb)

dim = xb.shape[1]

# build the FAISS index and add the embeddings
index = faiss.IndexFlatIP(dim)
index.add(xb)


configuration = {
    "skin_type": {"min_similarity": 0.6, "top_k": 1},
    "concerns": {"min_similarity": 0.5, "top_k": 3},
    "goals": {"min_similarity": 0.4,"top_k": 3}
}

# function to perform FAISS search for similar reference text to user input and return the scores and labels of the matches
def faiss_search(text, top_k=20):
    # embed the input text
    user_emb = model.encode(text)
    user_emb = np.array([user_emb]).astype("float32")
    
    # normalize the user embedding for cosine similarity
    faiss.normalize_L2(user_emb)
    
    # search the index for the top_k most similar embeddings and return the scores and indices of the matches
    scores, indices = index.search(user_emb, top_k)

    # return the scores and indices of the matches
    return scores[0], indices[0]    

# normalize text 
def normalize(text):
    # undercase and remove whitespaces in front and back
    return text.lower().strip()

# Make user input longer when input is short
def enrich_input(text, category):
    if len(text.split()) <= 2:
        if category == "skin_type":
            return f"My skin type is {text}"
    return text

# Filter skin type labels
def decide_skin_type(sorted_labels, config):
    top_label, top_score = sorted_labels[0][0], sorted_labels[0][1] 
    second_score = sorted_labels[1][1] if len(sorted_labels) > 1 else 0
    
    # gap between the top and second score
    confidence_gap = top_score - second_score
    
    # if top score is below threshold return empty, if top score above 0.75 return top label, if confidence gap above 0.05 return top label else return empty
    if top_score < config["min_similarity"]:
        return ""
    elif top_score >= 0.75:
        return top_label
    elif confidence_gap >= 0.05:
        return top_label
    
    return ""

# Filter concerns and goals labels
def decide_multi(sorted_labels, config):
    top_score = sorted_labels[0][1]
    results = []
    
    # for label and score in sorted labels if score above threshold and score to top score ratio is not too low then add to results
    for label, score in sorted_labels:
        if score < config["min_similarity"]:
            continue
        # if score and top_score ratio too big do not add
        if score / top_score < 0.6:
            break
        
        results.append(label)
        
    return results[:config["top_k"]]

# split text by separators and return list of stripped parts
def split_input(text):
    separators = [",", "and", "&"]
    
    parts = [text]
    
    for sep in separators:
        new_parts = []
        for p in parts:
            new_parts.extend(p.split(sep))
        parts = new_parts
        
    return [p.strip() for p in parts if p.strip()]

# function to handle multi input extraction
def extract_multi_input(text, category, debug):
    # split text
    parts = split_input(text)
    
    label_scores = defaultdict(list)
    
    # for each part extract semanatics and extend results to all_result
    for part in parts:
        results = retrieve_candidates(part, category, debug=debug)
        
        for label, score in results:
            label_scores[label].append(score)
    
    # aggregate holds the final score for each label
    aggregated = {}
    # for each label take the max score across the different parts as the final score for that label and append to aggregated
    for label, scores in label_scores.items():
        aggregated[label] = max(scores)
        
    # sort by score
    aggregated = sorted(aggregated.items(), key=lambda x: x[1], reverse=True)
        
    return aggregated
    

# function to determine which extraction method to use and then call deciding function to filter result based on category
def extract_semantics(text, category, debug=False):
    config = configuration[category]
    
    # multi label input if separator and category is concerns or goals
    if any(sep in text for sep in [",", "and", "&"]) and category in ["concerns", "goals"]:
        sorted_labels =  extract_multi_input(text, category, debug=debug)
    else:
    # single label input
        sorted_labels = retrieve_candidates(text, category, debug=debug)
    
    if category == "skin_type":
        return decide_skin_type(sorted_labels, config)
    else:
        return decide_multi(sorted_labels, config)
    

    
# function to retrive embeddings for user input and reference text and calculate similarity score to determine label candidates
def retrieve_candidates(text, category, debug=False):
    # clean text
    text = normalize(text)
    
    # enrich short text
    text = enrich_input(text, category)
    
    # retrieve score and indices of similar reference text using FAISS serach
    scores, indices = faiss_search(text, top_k=30)
    
    # detected labels candidates
    label_scores = {}
    
    # loop through scores and indices and get the category and label for each match from metadata
    for scores, idx in zip(scores, indices):
        group, label = metadata[idx]
        
        if group != category:
            continue
        
        # take max score per label
        if label not in label_scores:
            label_scores[label] = scores
        else:
            label_scores[label] = max(label_scores[label], scores)
    
    # sort labels by scores in descending order  
    sorted_labels = sorted(label_scores.items(), key=lambda x: x[1], reverse=True)
    
    # determine category contiguration
    config = configuration[category]

    
    # debuging to see rank, label, similarity score, and if passed threshold
    if debug:
        print(f"\n === Debug: {category} ===")
        for rank, (label, score) in enumerate(sorted_labels, start=1):
            print(f"Rank: {rank}, Label: {label}, Similarity Score: {score}, Passed Threshold: {score >= config['min_similarity']}")
    
    # return [(label, score)]
    return sorted_labels
    
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
                "requires_concern": ["acne", "aging", "sensitivity", "sun protection"]
            },
            "hydrating_serum": {
                "max": 2,
                "requires_concern": ["hydration", "sensitivity"]
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



# role activation logic
# blueprint routine based of product rules
def build_routine(context):
    plan = []
    
    for product_type, rules in Product_Rules.items():
        if rules.get("require_am") and context["time"] != "a.m":  
            continue
        if rules.get("requires_concern") and context["concerns"] == ["general"]:
            continue
        
        # determine number of products based of if essential
        if rules["essential"]:
            # count is how many products of that type we want to recommend
            count = 1
        else:
            if product_type == "treatment":
                # acne and brightening are the only concerns that would require more than 1 treatment product
                if "acne" in context["concerns"] or "brightening" in context["concerns"]:
                    count = 2
                else:
                    count = 1
            else:
                count = 0
        
        plan.append({
            "category": product_type,
            "count": count,
            "order": rules.get("order", 999) # default order is 999 if not specified
        })

    # sort plan by order
    plan.sort(key=lambda x: x["order"])
    
    return plan
# =================== PLANING END ==========================


# ================ PRODUCT RECOMMEDATIONS ==================
# Data structure to hold product info
Product_Info = {
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
    "Gentle Fragence-Free Cleanser": {
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
    }
}

# function to recommend products for a given product type category 
def recommend_for_product_type(category, context, count = 1):
    # Fill one product type at a time based on the routine blueprint and product rules
    candidates = []
    for product_name, product_details in Product_Info.items():
        if product_details["type"] == category:
            candidates.append((product_name, product_details))
    
    # calculate coverage score for each candidate product based on how well it addresses the user's skin type, concerns, and goals
    scored_candidates = []
    for category_product_name, category_product_details in candidates:
        score = calculate_coverage(category_product_details, context)
        scored_candidates.append({
            "product": category_product_name,
            "info": category_product_details,
            "score": score
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

product_embeddings = []
product_metadata = []

# create product and metadata embeddings for product item info
# loop through name and info for each product 
for name, info in Product_Info.items():
    # holds text info
    text = info["description"]
    # embed text description
    emb = model.encode(text)
    # add embedding to product_embedding
    product_embeddings.append(emb)
    # add product name
    product_metadata.append(name)

# build index
xb = np.array(product_embeddings).astype("float32")
# normalize for cosine similarity
faiss.normalize_L2(xb)

# build the FAISS index and add the embeddings
product_index = faiss.IndexFlatIP(xb.shape[1])
product_index.add(xb)

def get_faiss_scores(context):
    result = {}
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
    
    for p in products:
        # if only 1 score set it as 1.0
        if max_score == min_score:
            p["normalized_score"] = 1.0
        else:
            # (current - min) / (max - min)
            # help determine its overall order in the list of scores
            p["normalized_score"] = (p["score"] - min_score) / (max_score - min_score)
    
    return products

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
# ============ CONVERSATION AND PROFILE MANAGEMENT ===============

# Retry function for followup question if couldn't detect skin type, concern, or goal
def retry_extract(user_profile, category, followup_message, add_function, update=False):
    # attempt counter for missing info to determine how many times we ask follow up questions
    # 3 attempts
    missing_info_attempts = 1
    
    # while attribute is empty
    while not getattr(user_profile, category):
        print(followup_message)
        user_input = input("You: ")
        print()
        
        labels = extract_semantics(user_input, category, debug=True)
        
        # if category is skin type no need to loop and add directly
        if category == "skin_type":
            add_function(labels)
        for label in labels:
            add_function(label, update)
        # if the user followup input is still doesn't provide necessary data we count that another re-attempt and try again
        if not getattr(user_profile, category):
            missing_info_attempts += 1
        if missing_info_attempts >= 3:
            print("Bot: No worries, we can move on with the information we have and adjust later if needed.")
            # default value
            add_function("general", update)
            break
    

# Main Conservation Function Loop
def have_conversation():
    print("Welcome to the Skincare AI Consultant!\n")
    print("Do you have an existing profile? (yes/no)")
    
    
    # open profile.json file and load exisiting data if any
    # edge case: if file does not exist create it with empty user data
    # edge case: if file is empty we should also handle that and create empty user data
    try:
        with open("profile.json", "r") as f:
            existing_data = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        existing_data = {"users": {}}
    login_status = False    
    while not login_status:
        existing_profile = input("You: ").lower()
        if existing_profile.startswith("yes") or existing_profile == "y":
            unique_id_attempts = 0
            # while loop to allow user 3 attempts to enter correct unique ID
            while unique_id_attempts < 3:
                unique_id_input = input("Enter your unique ID: ")
        
                # Add users data back into the UserProfile class and continue conversation
                if unique_id_input in existing_data["users"]:
                    user_data = existing_data["users"][unique_id_input]
                    user_profile = UserProfile()
                    user_profile.unique_id = unique_id_input
                    user_profile.name = user_data.get("name")
                    user_profile.add_skin_type(user_data.get("skin_type"))
                    for concern in user_data.get("concerns", []):
                        user_profile.add_concern(concern)
                    for goal in user_data.get("goals", []):
                        user_profile.add_goal(goal)
                    user_profile.am_routine = user_data.get("am_routine", [])
                    user_profile.pm_routine = user_data.get("pm_routine", [])
                    user_profile.add_routine(user_profile.am_routine, "a.m")
                    user_profile.add_routine(user_profile.pm_routine, "p.m")
                    print(f"Welcome back {user_profile.name}! I have loaded your profile. Let's review and adjust if needed before we move on.")
                    print(f"  . Detected Skin Type: {user_profile.skin_type if user_profile.skin_type else 'Not detected'}")
                    print(f"  . Detected Concerns: {user_profile.concerns if user_profile.concerns else 'None detected'}")
                    print(f"  . Detected Goals: {user_profile.goals if user_profile.goals else 'No goals specified'}")
                    print(f"  . Detected Morning Routine: {user_profile.am_routine if user_profile.am_routine else 'No routine detected'}")
                    print(f"  . Detected Night Routine: {user_profile.pm_routine if user_profile.pm_routine else 'No routine detected'}")
                    login_status = True
                    break
                else:
                    print("Sorry, I couldn't find a profile with that ID.")
                    unique_id_attempts += 1
                    
                if unique_id_attempts >= 3:
                        print("Let's create a new profile instead.\n")
                        # edit correct answer to existing_profile to enter correct conversation flow
                        existing_profile = "no" 
                        login_status = True
                        # create user profile
                        user_profile = UserProfile()
                        break
                
            
        elif existing_profile.startswith("no") or existing_profile == "n":
            print("No problem! Let's create a new profile for you.\n")
            login_status = True
            # create user profile
            user_profile = UserProfile()
        else:
            print("Please answer with yes or no.")
    
    user_done = ""
    
    if existing_profile.startswith("no") or existing_profile == "n":
        print("Bot: What is your name?")
        name_input = input("You: ")
        print()
        
        # generate unique_id that is unique per user    
        unique_id = 0
        while True:
            unique_id = random.randint(1000, 9999)
            if unique_id not in existing_data["users"]:
                user_profile.unique_id = unique_id
                break 
            
        print(f"Nice to meet you {name_input}. Here is your unique ID to receive your profile: {unique_id}")
        user_profile.name = name_input
    
        
    # Main Conversation Loop - gather user info and update profile
    while True:
        # Determine what to ask next
        question = what_to_ask_next(user_profile)
        
        # Check if any information is missing and update profile
        if question is None:
            print("Thanks for sharing all that information! I have what I need to recommend a skincare routine for you. If you want to adjust any of the detected information we can do that in the next steps.")
        
            print("Bot: Here is what I gathered:")
            print(f"  . Detected Skin Type: {user_profile.skin_type if user_profile.skin_type else 'Not detected'}")
            print(f"  . Detected Concerns: {user_profile.concerns if user_profile.concerns else 'None detected'}")
            print(f"  . Detected Goals: {user_profile.goals if user_profile.goals else 'No goals specified'}")
            break
        
        # Print question
        print(f"Bot: {question[0]}")
        
        # Get user input
        user_input = input("You: ")
        print() # new line for readability
        
        # Determine what question was asked based on what_to_ask_next() output and extract user input and update user profile
        if question[1] == "skin_type":
            user_profile.add_skin_type(extract_semantics(user_input, "skin_type", debug=True))
            # follow up questions if user input doesn't give enough info
            retry_extract(user_profile, "skin_type", "I couldn't quite detect your skin type from that. Can you tell me more about your skin? For example, is it oily, dry, or a mix of both?", user_profile.add_skin_type)
                
        elif question[1] == "concerns":
            concerns = extract_semantics(user_input, "concerns", debug=True)
            for item in concerns:
                user_profile.add_concern(item)
            # follow up questions if user input doesn't give enough info
            retry_extract(user_profile, "concerns", "Can you tell me more about specific skin concerns are you hoping to address? For example, would it be acne, aging, sensitivity, or something else?", user_profile.add_concern)
        
        elif question[1] == "goals":
            goals = extract_semantics(user_input, "goals", debug=True)
            for item in goals:
                user_profile.add_goal(item)
            # follow up questions if user input doesn't give enough info
            retry_extract(user_profile, "goals", "Can you tell me more about your main skincare goals? Do you hope to improve hydration, reduce wrinkles, or something else?", user_profile.add_goal)
                
    # Re-adjustsment and Routine Loop    
    while True:
        print("\nWould you like to:")
        print("1. Satifisited with skincare information and move on to the routine")
        print("2. Adjust detected skin type")
        print("3. Adjust detected skin concerns")
        print("4. Adjust detected skin goals")
        print("5. Save and Exit")
        
        user_done = input("Enter 1-5\nYou: ").lower()
            
        if user_done not in ["1", "2", "3", "4", "5", "one", "two", "three", "four", "five"]:
                print("Please choose and answer with one of the number options listed.")    
        routine_time = ""
        
        if user_done in ["1", "one"]:
            while True:
                print("What routine would you like to generate first:\n")
                print("1: Morning a.m routine")
                print("2. Night p.m routine")
                routine_input = input("Enter 1 or 2\nYou: ").lower()
                
                if routine_input == "1" or routine_input == "one":
                    routine_time = "a.m"
                elif routine_input == "2" or routine_input == "two":
                    routine_time = "p.m"
                else:
                    print("\nPlease choose and answer with one of the number options listed.")
            
                context = {
                    "time": routine_time,
                    "skin_type": user_profile.skin_type,
                    "concerns": user_profile.concerns,
                    "goals": user_profile.goals
                }

                # build routine blueprint based on user profile and product rules
                # blueprint determines how manny products of each type we should recommend based on user profile and product rules but does not specify which products yet
                routine_blueprint = build_routine(context)

                recommend_routine = []
                for product_type in routine_blueprint:
                    # for each product type in routine_blueprint get specific product recommendations
                    products = recommend_for_product_type(product_type["category"], context, product_type["count"])
                    # extend recommend_routine with products while avoiding duplicates
                    recommend_routine.extend(products)
                
                user_profile.add_routine(recommend_routine, routine_time)
                
                print(f"\nBased on your profile, I recommend the following {routine_time} routine:\n")
                for item in recommend_routine:
                    print(f"  . Product: {item['product']}")
                    print(f"  . Type: {item['type']}")
                    print(f"  . Reasoning: {item['reason']}\n")
                
                # break after generating routine
                break
                
        if user_done in ["2", "two"]:
            # adjust user skin type
            adjust_user_profile(user_profile, "skin_type")
            print(f"Bot: Updated skin type to {user_profile.skin_type}.")
            
        elif user_done in ["3", "three"]:
            # adjust user skin concern
            adjust_user_profile(user_profile, "concerns")
            print(f"Bot: Updated skin concerns to {user_profile.concerns}.")
        elif user_done in ["4", "four"]:
            # adjust user skin goal
            adjust_user_profile(user_profile, "goals")
            print(f"Bot: Updated skin goals to {user_profile.goals}.")
        elif user_done in ["5", "five"]:
            print(f"Bot: Thank you for using the Skincare AI Consultant! Have a great day!\nUse your unique ID: {user_profile.unique_id} to access your profile again.")
            data = {
                    "name": user_profile.name,
                    "skin_type": user_profile.skin_type,
                    "concerns": user_profile.concerns,
                    "goals": user_profile.goals,
                    "am_routine": user_profile.am_routine,
                    "pm_routine": user_profile.pm_routine
                    }
            
            # append new user data to file
            existing_data["users"][str(user_profile.unique_id)] = data
            
            # write data back to json file
            with open("profile.json", "w") as f:
                json.dump(existing_data, f, indent=4)
            break

        


    
if __name__ == "__main__":
    have_conversation()
    