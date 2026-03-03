import re # regular expressions for text cleaning
from collections import Counter
from shlex import join

from sentence_transformers import SentenceTransformer, util
model = SentenceTransformer('all-MiniLM-L6-v2')

from collections import defaultdict # for product score and reasons (less if statements as keys are created on the go)

# User Profile Class to store user info
class UserProfile:
    def __init__(self):
        self.skin_type = None
        self.concerns = []
        self.goals = []   
        
    def add_skin_type(self, skin_type):
        self.skin_type = skin_type
    
    def add_concern(self, concern):
        if concern not in self.concerns:
            self.concerns.append(concern)
                
    def add_goal(self, goal):
        if goal not in self.goals:
            self.goals.append(goal)
    

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
            skin_type = extract_all_skin_type_semantics(user_input)
            user_profile.add_skin_type(skin_type)
        elif missing == "concerns":
            concerns = extract_all_concerns_semantics(user_input)
            for item in concerns:
                user_profile.add_concern(item)
        elif missing == "goals":
            goals = extract_all_goals_semantics(user_input)
            for item in goals:
                user_profile.add_goal(item)

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
        return scores[0][0]

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
    
    detected = []
    for label, score in raw_scores.items():
        # keep labels that are:
        # 1. reasonably similar (min similarity)
        # 2. close to the best score (margin)
        # purpose: Find other labels that are also good matches (multi answers)
        # raw_score: similarity score
        # relative_score: score compared to best score (0.0 to 1.0)
        if score >= min_similarity and (best_score - score) <= margin:
            detected.append(label)
    
    return detected
        
       
    
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
            detected.append(label)

    return detected 


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


# now i made the product_rules but am not sure how to use it yet
# product_rules should be used for building the routine with the recommended products
# product_rule is not done yet as i did not take into account the user profile when building the routine
# use rule base system to build routine based on user profile 

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
        "conerns_addressed": ["sensitivity"],
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


def recommend_for_product_type(category, context, count = 1):
    # Fill one product type at a time based on the routine blueprint and product rules
    candiates = []
    for product_name, product_details in Product_Info.items():
        if product_details["type"] == category:
            candiates.append((product_name, product_details))
    
    # calculate coverage score for each candidate product based on how well it addresses the user's skin type, concerns, and goals
    scored_candidates = []
    for category_product_name, category_product_details in candiates:
        score = calculate_coverage(category_product_details, context)
        scored_candidates.append((category_product_name, category_product_details, score))
        
    # sort candidates by score
    scored_candidates.sort(key=lambda x: x[2], reversed=True)
    results = []
    # [:count] to get top products based on count specified in Build Routine
    for product, info, score in scored_candidates[:count]:
        results.append({
            "product": product,
            "type": info["type"],
            "score": score,
            "reason": generate_reasoning(info, context)
        })
        
    return scored_candidates[:count]

def calculate_coverage(product, context):
    # Calculate how well a product addresses the user's skin type, concerns, and goals based on Product_Info and user profile
    score = 0
    # skin type match is most important 
    if context["skin_type"] in product["skin_types_addressed"]:
        score += 3
    else:
        score -= 2
    
    # find how many concerns the product addresses that the user has
    product_concerns = set(product["concerns_addressed"])
    user_concerns = set(context["concerns"])
    # intersection
    concern_matches = product_concerns & user_concerns
    score += len(concern_matches) * 2
    
    # find how many goals the product addressed that the user has
    product_goals = set(product["goals_addressed"])
    user_goals = set(context["goals"])
    
    goal_matches = product_goals & user_goals
    # * 1 because goal match is less important than concern and skin type match
    score += len(goal_matches) * 1
    
    
    return score

def generate_reasoning(info, context):
    # Generate reasoning for why a product is recommended based on how it addresses the user's skin type, concerns, and goals
    reasoning = []
    if context["skin_type"] in info["skin_types_addressed"]:
        reasoning.append(f"Addresses your skin type ({context['skin_type']}).")
    else:
        reasoning.append(f"Not ideal for your skin type ({context['skin_type']}), but may still provide some benefits.")
    
    concern_matches = set(info["concerns_addressed"]) & set(context["concerns"])
    if concern_matches:
        reasoning.append(f"Targets your skin concerns: {', '.join(concern_matches)}.")
        reasoning.append(f"Specifically, {info['description']}")
    else:
        reasoning.append("Does not directly target your specific concerns, but may still offer general skincare benefits.")
    
    goal_matches = set(info["goals_addressed"]) & set(context["goals"])
    if goal_matches:
        reasoning.append(f"Helps you work towards your skincare goals: {', '.join(goal_matches)}.")
    else:
        reasoning.append("May not directly align with your specific goals, but could still contribute to overall skin health.")
    
    return " ".join(reasoning)
    

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
                user_profile.add_skin_type(item)
        elif question.startswith("What concerns do you have about your skin"):
            concerns = extract_all_concerns_semantics(user_input)
            for item in concerns:
                user_profile.add_concern(item)
        elif question.startswith("What are your skincare goals"):
            goals = extract_all_goals_semantics(user_input)
            for item in goals:
                user_profile.add_goal(item)
        
        
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
            "goals": user_profile.goals
        }
        
        routine_blueprint = build_routine(context)
        print(f"Routine Blueprint: {routine_blueprint}\n")
        recommend_routine = []
        for product_type in routine_blueprint:
            products = recommend_for_product_type(product_type["category"], context, product_type["count"])
            #extend recommend_routine with products while avoiding duplicates
            recommend_routine.extend(products)

        
    elif user_done in ["2", "two"]:
        # adjust user skin type
        pass
    elif user_done in ["3", "three"]:
        # adjust user skin concern
        pass
    elif user_done in ["4", "four"]:
        # adjust user skin goal
        pass
    


    
    #for product in recommended_products:
     #   print(f"  . Product: {product['product']}")
      #  print(f"  . Reasons: {product['reasons']}\n")
        


    
if __name__ == "__main__":
    have_conversation()
    
    
# sematic verbosity 
# EX: I have oily skin
# User 1: My skin get extremely oily throughout the day around my nose and forehead and I constantly feel greasy
# User 2: Both user inputs means the same but due to second input having more descriptive languaage it will have higher semantics scoring.