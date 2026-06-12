from fastapi import FastAPI
from embedding_model import load_model
from pydantic import BaseModel
from retrieve_skin_info import extract_semantics, get_reference_embeddings, get_faiss_index

# Initialize the FastAPI application
app = FastAPI()

# Define a simple route
@app.get("/")
def root(): # Define the root endpoint
    return {"message": "Skincare AI API is running"}

# Load the embedding model when the application starts
@app.on_event("startup")
def startup():
    load_model()
    get_reference_embeddings()
    get_faiss_index()

# Define the request model for the analyze endpoint
class AnalyzeRequest(BaseModel):
    skin_text: str
    concerns_text: str
    goals_text: str

# Define the analyze endpoint to process the input data and return the analysis results
@app.post("/analyze")
def analyze_profile(request: AnalyzeRequest):
    
    print("Received request")
    
    # Extract the input data from the request
    skin_type = extract_semantics(request.skin_text, "skin_type")
    print("Skin type done")
    
    concerns = extract_semantics(request.concerns_text, "concerns")
    print("Concerns done")
    
    goals = extract_semantics(request.goals_text, "goals")
    print("Goals done")
    
    return {
        "skin_type": skin_type,
        "concerns": concerns,
        "goals": goals
    }
    
