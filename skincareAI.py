from collections import Counter
from shlex import join
import random # random number generator
import json # for saving userProfile data
import faiss # for faster similarity search
import numpy as np

# import functions from files
from retrieve_skin_info import extract_semantics
from retrieve_skin_info import get_reference_embeddings
from retrieve_skin_info import get_faiss_index


from product_recommendation import recommend_for_product_type
from product_recommendation import get_faiss_scores

from routine import build_routine

from embedding_model import load_model

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
    

def initialize():
    # Load model and reference data
    load_model()
    get_reference_embeddings()
    get_faiss_index()
    

# Main Conservation Function Loop
def have_conversation():
    initialize()
    
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
                
                # get the faiss score for the current context
                faiss_score = get_faiss_scores(context)

                # build routine blueprint based on user profile and product rules
                # blueprint determines how manny products of each type we should recommend based on user profile and product rules but does not specify which products yet
                routine_blueprint = build_routine(context)

                recommend_routine = []
                for product_type in routine_blueprint:
                    # for each product type in routine_blueprint get specific product recommendations
                    products = recommend_for_product_type(product_type["category"], context, faiss_score,product_type["count"])
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
            if str(user_profile.unique_id) in existing_data["users"]:
                print("\nUpdating existing profile with new information...")
            # append new user data to file
            existing_data["users"][str(user_profile.unique_id)] = data
            
            # write data back to json file
            with open("profile.json", "w") as f:
                json.dump(existing_data, f, indent=4)
            break


    