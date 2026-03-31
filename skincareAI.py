from collections import Counter
from shlex import join
import random # random number generator
import json # for saving userProfile data

# read json file
#with open("profile.json", "r") as f:
#    data = json.load(f)
    
# modify json file
#data["users"]["1003"] = {"name": "Charile", "age": 30}

# write back json file
#with open("profile.json", "w") as f:
#    json.dump(data, f, index=4)

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
        self.skin_type = None
        self.concerns = []
        self.goals = []
        self.am_routine = []
        self.pm_routine = []
    
    
    def add_skin_type(self, skin_type):
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
    print()

    # skintype easily updated as its one label
    if aspect == "skin_type":
        user_profile.add_skin_type(extract_all_skin_type_semantics(user_input))
    # update = True to handle new user input as override of previous info instead of appending to it
    elif aspect == "concerns":
        concerns = extract_all_concerns_semantics(user_input)
        for item in concerns:
            user_profile.add_concern(item, update=True)
    elif aspect == "goals":
        goals = extract_all_goals_semantics(user_input)
        for item in goals:
            user_profile.add_goal(item, update=True)

# ==================== ML Semantics ====================

def extract_all_skin_type_semantics(text, min_similarity=0.35):
        
    # embed user text
    user_emb = model.encode(text)
    
    # Semantic comparsion between user text and reference descriptions for each skin type
    references = {
        "oily": "oily greasy shiny excess oil production enlarge pores",

        "dry": "dry dehyrated flaky tight rough texture lacking moisture dryness",

        "combination": "combination with t-zone shiny greasy forehead nose chin cheeks tight patchy uneven zones",

        "sensitive": "sensitive reactive irritated red easily inflamed",

        "normal": "normal balanced healthy even comfortable"
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

def extract_all_concerns_semantics(text, min_similarity=0.35, top_k=3):
    user_emb = model.encode(text)
    
    references = {
        "acne": "acne pimples breakouts blemish clogged pores blackheads",

        "aging": "aging wrinkles fine lines sagging firmness elasticity crow's feet",

        "sensitivity": "sensitive redness irritation reactive burning itching inflamed rosacea",

        "sun protection": "sun uv sunburn spf photoaging sun damage rays",
        
        "hydration": "dry dehydrated tight flaky moisture barrier plump",
        
        "brightening": "dull uneven dark spots hyperpigmentation glow discoloration melasma"
    }
    
    raw_scores = {}
    
    # calculate similarity score between reference text and user text
    # raw_scores[label] = similarity score
    for label, references_text in references.items():
        ref_emb = model.encode(references_text)
        raw_scores[label] = util.cos_sim(user_emb, ref_emb).item()
        
    # sort labels by similarity score (highest to lowest)
    sorted_labels = sorted(raw_scores, key=raw_scores.get, reveresd=True)
    
    detected = []
    # filer if similarity score is above min_similarity threshold and top_k?
    for label, score in sorted_labels:
        if score >= min_similarity:
            detected.append(label)
            
    # return top 3 most similar labels 
    return detected[:top_k]
        
       
    
def extract_all_goals_semantics(text, min_similarity=0.35, top_k=3):
    user_emb = model.encode(text)
    
    references = {
        "clear_skin": "clear smooth clean blemish-free fewer breakouts refined",

        "anti_aging": "youthful wrinkle-free firm plump reduce aging lines",

        "hydration": "hydrated moisturized dewy soft plump moisture barrier",

        "protection": "protect shield uv sun damage pollution prevention",

        "soothe": "calm soothe reduce redness irritation comfort sensitive",
        
        "brighten": "bright radiant glow even tone luminous dark spots fade"
    }
    raw_scores = {}
    
    # calculate similarity score between reference text and user text
    # raw_scores[label] = similarity score
    for label, references_text in references.items():
        ref_emb = model.encode(references_text)
        raw_scores[label] = util.cos_sim(user_emb, ref_emb).item()
        
    # sort labels by similarity score (highest to lowest)
    sorted_labels = sorted(raw_scores, key=raw_scores.get, reveresd=True)
    
    detected = []
    # filer if similarity score is above min_similarity threshold and top_k?
    for label, score in sorted_labels:
        if score >= min_similarity:
            detected.append(label)
            
    # return top 3 most similar labels 
    return detected[:top_k]


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
    scored_candidates.sort(key=lambda x: x[2], reverse=True)
    results = []
    # [:count] to get top products based on count specified in Build Routine
    for product, info, score in scored_candidates[:count]:
        results.append({
            "product": product,
            "type": info["type"],
            "score": score,
            "reason": generate_reasoning(info, context)
        })
        
    return results

def calculate_coverage(product, context):
    # Calculate how well a product addresses the user's skin type, concerns, and goals based on Product_Info and user profile
    score = 0
    # skin type match is most important 
    if context["skin_type"] in product["skin_types_addressed"]:
        score += 3
    else:
        score -= 2
    
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
# ============ CONVERSATION AND PROFILE MANAGEMENT ===============

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
                        break
                
            
        elif existing_profile.startswith("no") or existing_profile == "n":
            print("No problem! Let's create a new profile for you.\n")
            login_status = True
        else:
            print("Please answer with yes or no.")
    
    # Create user profile
    user_profile = UserProfile()
    number = 1
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
            
        print(f"Nice to meet you {name_input}. Here is your unique ID to receive your profile {unique_id}")
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
        
        # attempt counter for missing info to determine how many times we ask follow up question before we move on (3 attempts)
        missing_info_attempts = 0
        
        # Determine what question was asked based on what_to_ask_next() output and extract user input and update user profile
        if question[1] == "skin_type":
            user_profile.add_skin_type(extract_all_skin_type_semantics(user_input))
            
            while not user_profile.skin_type:
                # follow up question if couldn't detect skin type from user input
                print("Bot: I couldn't quite detect your skin type from that. Can you tell me more about your skin? For example, is it oily, dry, or a mix of both?")
                user_input = input("You: ")
                print()
                user_profile.add_skin_type(extract_all_skin_type_semantics(user_input))
                if not user_profile.skin_type:
                    missing_info_attempts += 1
                if missing_info_attempts >= 3:
                    # reset missing_info_attempts after done so it can be used for other missing info if needed
                    missing_info_attempts = 0
                    print("Bot: No worries, we can move on with the information we have and adjust later if needed.")
                    user_profile.add_skin_type("general") # default
                    break
                if user_profile.skin_type:
                    # reset attempts if we do detect skin type so it can be used for other missing info if needed
                    missing_info_attempts = 0 
                
        elif question[1] == "concerns":
            concerns = extract_all_concerns_semantics(user_input)
            for item in concerns:
                user_profile.add_concern(item)
            while not user_profile.concerns:
                print("Can you tell me more about specific skin concerns are you hoping to address? For example, would it be acne, aging, sensitivity, or something else?")
                user_input = input("You: ")
                print()
                concerns = extract_all_concerns_semantics(user_input)
                for item in concerns:
                    user_profile.add_concern(item)
                if not user_profile.concerns:
                    missing_info_attempts += 1
                if missing_info_attempts >= 3:
                    missing_info_attempts = 0
                    print("Bot: No worries, we can move on with the information we have and adjust later if needed.")
                    user_profile.add_concern("general") # default
                    break
                if user_profile.concerns:
                    # reset attempts when done
                    missing_info_attempts = 0
        elif question[1] == "goals":
            goals = extract_all_goals_semantics(user_input)
            for item in goals:
                user_profile.add_goal(item)
            while not user_profile.goals:
                print("Can you tell me more about your main skincare goals? Do you hope to improve hydration, reduce wrinkles, or something else?")
                user_input = input("You: ")
                print()
                goals = extract_all_goals_semantics(user_input)
                for item in goals:
                    user_profile.add_goal(item)
                if not user_profile.goals:
                    missing_info_attempts += 1
                if missing_info_attempts >= 3:
                    missing_info_attempts = 0
                    print("Bot: No worries, we can move on with the information we have and adjust later if needed.")
                    user_profile.add_goal("general") # default
                    break
                if user_profile.goals:
                    # reset attempts when done
                    missing_info_attempts = 0
                
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
            print("What routine would you like to generate first:\n")
            print("1: Morning a.m routine")
            print("2. Night p.m routine")
            routine_input = input("Enter 1 or 2\nYou: ").lower()
            
            if routine_input == "1" or routine_input == "one":
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
            print(f"Blueprint: {routine_blueprint}.")

            recommend_routine = []
            for product_type in routine_blueprint:
                products = recommend_for_product_type(product_type["category"], context, product_type["count"])
                # extend recommend_routine with products while avoiding duplicates
                recommend_routine.extend(products)
            
            user_profile.add_routine(recommend_routine, routine_time)
            
            print(f"\nBased on your profile, I recommend the following {routine_time} routine:\n")
            for item in recommend_routine:
                print(f"  . Product: {item['product']}")
                print(f"  . Type: {item['type']}")
                print(f"  . Reasoning: {item['reason']}\n")
        
            
   
        elif user_done in ["2", "two"]:
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
    