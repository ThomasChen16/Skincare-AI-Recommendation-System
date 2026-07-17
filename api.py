from fastapi import FastAPI
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
from skincareAI import load_profiles, save_profiles, get_user_profile, create_user_profile, update_user_profile


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
    # Login or create a new user profile using unique_id
    profile = create_user_profile(request.unique_id, request.name)
    
    return {
        "unique_id": request.unique_id,
        "name": profile["name"],
        "profile": profile
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
    
    # Extract the input data from the request
    skin_type = extract_semantics(request.skin_text, "skin_type")
    print("Skin type done")
    
    concerns = extract_semantics(request.concerns_text, "concerns")
    print("Concerns done")
    
    goals = extract_semantics(request.goals_text, "goals")
    print("Goals done")
    
    # If unique_id is provided, save the analysis to their profile
    saved = False
    if request.unique_id:
        profile_data = {
            "skin_type": skin_type,
            "concerns": concerns,
            "goals": goals
        }
        updated = update_user_profile(request.unique_id, profile_data)
        saved = updated is not None
    
    # return as JSON response to the frontend
    return {
        "skin_type": skin_type,
        "concerns": concerns,
        "goals": goals,
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
        "time": request.time,
        "skin_type": request.skin_type,
        "concerns": request.concerns,
        "goals": request.goals
    }
    
    # get faiss scores for the current context
    faiss_score = get_faiss_scores(context)
    
    # build routine blueprint based on user profile and product rules
    # blueprint determines how manny products of each type we should recommend based on user profile and product rules but does not specify which products yet
    routine_blueprint = build_routine(context)

    recommend_routine = []
    am_routine = []
    pm_routine = []
    
    for product_type in routine_blueprint:
        # for each product type in routine_blueprint get specific product recommendations
        products = recommend_for_product_type(product_type["category"], context, faiss_score, product_type["count"])
        
        # extend recommend_routine with products while avoiding duplicates
        recommend_routine.extend(products)
        
        # Separate AM and PM routines
        if product_type["time"] == "am":
            am_routine.extend(products)
        elif product_type["time"] == "pm":
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
    
