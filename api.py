from fastapi import FastAPI
from embedding_model import load_model
from pydantic import BaseModel
from retrieve_skin_info import extract_semantics, get_reference_embeddings, get_faiss_index

# Initialize the FastAPI application
# Creates a web server that listens for HTTP requests (waits for requests)
app = FastAPI()

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

# Define the request model for the analyze endpoint
# Define the data the API expects to receive from the frontend
class AnalyzeRequest(BaseModel):
    # frontend must send skin_text, concerns_text, and goals_text
    skin_text: str
    concerns_text: str
    goals_text: str

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
    
    # return as JSON response to the frontend
    return {
        "skin_type": skin_type,
        "concerns": concerns,
        "goals": goals
    }
    
