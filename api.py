from fastapi import FastAPI
from fastapi import HTTPException
from fastapi.middleware.cors import CORSMiddleware
from embedding_model import load_model
from pydantic import BaseModel
from typing import Optional
import json
import os
from datetime import datetime

from retrieve_skin_info import extract_semantics, get_reference_embeddings, get_faiss_index
from product_recommendation import get_faiss_scores, recommend_for_product_type
from routine import build_routine
from skincareAI import load_profiles, save_profiles, get_user_profile, create_user_profile, update_user_profile, save_feedback
from database import init_db


# Initialize the FastAPI application
# Creates a web server that listens for HTTP requests (waits for requests)
app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Define a simple route
# functions run when someone vists the root URL ("/") using HTTP GET method
# GET is used for retrieving data from the server
@app.get("/")
def root(): # Define the root endpoint
    # Confirm API is working by returning a simple message
    return {"message": "Skincare AI API is running"}

# Load the embedding model when the application starts
# run once when you first start the API server
@app.on_event("startup")
def startup():
    # load sentence transformer model when the API starts
    load_model()
    # loads the reference embeddings into memory when the API starts
    get_reference_embeddings()
    # load the FAISS index when the API starts
    get_faiss_index()
    # get access to database when the API starts
    init_db()

# Define request/response models for authentication
class LoginRequest(BaseModel):
    unique_id: str
    name: str = "User"

class LoginResponse(BaseModel):
    unique_id: str
    name: str
    profile: dict

class SaveProfileRequest(BaseModel):
    unique_id: str
    skin_type: str
    concerns: list[str]
    goals: list[str]
    am_routine: list[dict]
    pm_routine: list[dict]
    # timestamps saved as ISO formatted strings (e.g. datetime.now().isoformat())
    created_at: Optional[str] = None
    last_updated: Optional[str] = None

# Login endpoint - creates or retrieves user profile
@app.post("/login", response_model=LoginResponse)
def login(request: LoginRequest):
    
    # If unique_id is provided, try to login existing user
    if request.unique_id:
        profile = get_user_profile(request.unique_id, request.name)
        
        if profile:
            # User found, return their profile
            return {
                "unique_id": request.unique_id,
                "name": profile["name"],
                "profile": profile
            }
        else:
            # User not found, create new profile with provided unique_id
            unique_id, new_profile = create_user_profile(request.name)
            # Override the generated unique_id with the one provided
            new_profile["unique_id_override"] = request.unique_id
            return {
                "unique_id": request.unique_id,
                "name": new_profile["name"],
                "profile": new_profile
            }
    else:
        # No unique_id provided, create new account
        unique_id, new_profile = create_user_profile(request.name)
        
        return {
            "unique_id": unique_id,
            "name": new_profile["name"],
            "profile": new_profile
        }

# Logout endpoint - clears session (frontend should clear stored unique_id)
@app.post("/logout")
def logout():
    # Logout endpoint - frontend should clear stored unique_id
    return {"message": "Logged out successfully"}

# Get user profile endpoint
@app.get("/profile/{unique_id}")
def get_profile(unique_id: str):
    # Get a user's saved profile
    profile = get_user_profile(unique_id)
    
    if not profile:
        return {"error": "User not found"}
    
    return {
        "unique_id": unique_id,
        "profile": profile
    }

# Save profile endpoint - saves analyzed data and routines
@app.post("/save-profile")
def save_profile(request: SaveProfileRequest):
    # Save user's profile data including skin analysis and routines
    profile_data = {
        "skin_type": request.skin_type,
        "concerns": request.concerns,
        "goals": request.goals,
        "am_routine": request.am_routine,
        "pm_routine": request.pm_routine,
        "created_at": request.created_at,
        "last_updated": request.last_updated
    }
    
    # update user profile
    updated_profile = update_user_profile(request.unique_id, profile_data)
    
    if not updated_profile:
        return {"error": "User not found"}
    
    return {
        "message": "Profile saved successfully",
        "unique_id": request.unique_id,
        "profile": updated_profile
    }

# Define the request model for the analyze endpoint
# Define the data the API expects to receive from the frontend
class AnalyzeRequest(BaseModel):
    # frontend must send skin_text, concerns_text, and goals_text
    skin_text: str
    concerns_text: str
    goals_text: str
    unique_id: str = None  # Optional unique_id for saving analysis

# Define the analyze endpoint to process the input data and return the analysis results
# @app.post means this handles HTTP POST requests
# POST is used for sending data to the server to be processed
@app.post("/analyze")
def analyze_profile(request: AnalyzeRequest):
    # request contains the JSON data the frontend sent
    # parse the input data and extract the relevant information using extract_semantics()
    
    print("Received request")
    missing_categories = []
    
    # Extract the input data from the request
    skin_type = extract_semantics(request.skin_text, "skin_type")
    concerns = extract_semantics(request.concerns_text, "concerns")
    goals = extract_semantics(request.goals_text, "goals")
    
    # Check each category for missing data in one loop
    categories = {
        "skin_type": skin_type,
        "concerns": concerns,
        "goals": goals,
    }
    
    # loop through if any empty
    for category_name, category_value in categories.items():
        if not category_value:  # Handles both "" and [] as falsy values
            print(f"{category_name} is missing")
            missing_categories.append(category_name)
        else:
            print(f"{category_name} done")
    
    # Only save if all categories are complete (no missing fields to prevent overwriting with empty values)
    saved = False
    if request.unique_id and not missing_categories:
        profile_data = {
            "skin_type": skin_type,
            "concerns": concerns,
            "goals": goals,
        }
        updated = update_user_profile(request.unique_id, profile_data)
        saved = updated is not None
    
    
    # return as JSON response to the frontend
    return {
        "skin_type": skin_type,
        "concerns": concerns,
        "goals": goals,
        "missing_categories": missing_categories,
        "saved": saved
    }

# Define the request model for the recommednation endpoint
# Define the data the API expects to receive from the frontend
class RecommendRequest(BaseModel):
    # frontend must send time, finalized skin_type, concerns, and goals
    time: str
    skin_type: str
    concerns: list[str]
    goals: list[str]
    unique_id: str = None  # Optional unique_id for saving routine

# Extract profile and generate routine
@app.post("/recommend")
def recommend(request: RecommendRequest):
    # request contains the JSON data the frontend set
    
    # format the inputs into context dictionary
    context = {
        "skin_type": request.skin_type,
        "concerns": request.concerns,
        "goals": request.goals
    }
    
    # get faiss scores for the current context
    faiss_score = get_faiss_scores(context)
    
    # Build routine blueprints for both AM and PM
    am_context = {**context, "time": "a.m"}
    pm_context = {**context, "time": "p.m"}
    
    am_blueprint = build_routine(am_context)
    pm_blueprint = build_routine(pm_context)

    recommend_routine = []
    am_routine = []
    pm_routine = []
    
    # Process AM routine blueprint
    for product_type in am_blueprint:
        # for each product type in routine_blueprint get specific product recommendations
        products = recommend_for_product_type(product_type["category"], am_context, faiss_score, product_type["count"])
        
        # extend recommend_routine with products while avoiding duplicates
        recommend_routine.extend(products)
        
        # Add to AM routine
        if product_type["time"] == "am":
            am_routine.extend(products)
    
    # Process PM routine blueprint
    for product_type in pm_blueprint:
        # for each product type in routine_blueprint get specific product recommendations
        products = recommend_for_product_type(product_type["category"], pm_context, faiss_score, product_type["count"])
        
        # extend recommend_routine with products while avoiding duplicates
        recommend_routine.extend(products)
        
        # Add to PM routine
        if product_type["time"] == "pm":
            pm_routine.extend(products)
    
    # If unique_id is provided, save the routine to their profile
    saved = False
    if request.unique_id:
        profile_data = {
            "am_routine": am_routine,
            "pm_routine": pm_routine
        }
        updated = update_user_profile(request.unique_id, profile_data)
        saved = updated is not None
    
    # return as JSON response to the frontend
    return {
        "routine": recommend_routine,
        "am_routine": am_routine,
        "pm_routine": pm_routine,
        "saved": saved
    }

# Define the request model for the feedback endpoint
# Define the data the API expects to receive from the frontend
# Pydantic model
class FeedbackRequest(BaseModel):
    unique_id: str
    product: str
    product_type: str
    rating: str
    routine_time: str
    
# Define the feedback endpoint to process user feedback on products
@app.post("/feedback")
def submit_feedback(request: FeedbackRequest):
    
    # validate rating in upvote or downvote format and routime_time in am or pm format
    if request.rating not in ["upvote", "downvote"]:
        raise HTTPException(status_code=400, detail="Invalid rating. Must be 'upvote' or 'downvote'")
    
    if request.routine_time not in ["a.m", "p.m"]:
        raise HTTPException(status_code=400, detail="Invalid routine time. Must be 'a.m' or 'p.m'")
    
    # Append the new entry    
    save_feedback(request.unique_id, request.product, request.product_type, request.rating,  request.routine_time)
    
    return {"message": "Feedback submitted successfully"}


