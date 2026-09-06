# Skincare AI Recommendation System

## Overview

This project is a skincare recommendation web application that allows users to describe their skin in their own words through a chat interface. Instead of selecting predefined options, users can freely explain their skin type, concerns, and skincare goals. The system analyzes their responses, recommends products that best match their profile, and generates both a morning and evening skincare routine.

The goal of this project was to explore how semantic search and machine learning embeddings can be used to improve user experience over traditional keyword matching.

---

## Features

- Chat-based skin analysis using free text
- Semantic understanding using sentence embeddings
- Product recommendations using FAISS similarity search
- Automatically generated AM and PM skincare routines
- User login and logout system
- User profiles and feedback stored in a SQLite database
- Real purchasable skincare products matched to every recommended product (brand, price, ingredients, buy link)
- Upvote / downvote feedback on products with global counts across all accounts
- Follow-up questions that ask for missing information (up to three attempts per field)
- Navigation bar with Chat, Routine, and Shop pages (Shop unlocks after a routine exists)
- Modern React frontend with FastAPI backend

---

## How It Works

### 1. Skin Analysis

The user answers a series of questions through a chat interface, describing:

- Skin type
- Skin concerns
- Skincare goals

Instead of searching for exact keywords, the application converts the user's responses into sentence embeddings. These embeddings capture the meaning of the text, allowing the system to understand similar phrases even when different wording is used.

The embeddings are compared against reference embeddings using FAISS similarity search to determine the user's skin profile.

---

### 2. Product Recommendation

Once the user's skin profile has been identified, the application searches through the product database.

Each product contains information describing:

- Recommended skin types
- Target concerns
- Intended skincare goals

The same embedding and FAISS similarity search process is used to compare the user's profile against each product description. Products with the highest similarity scores are selected as recommendations.

This approach makes recommendations based on overall meaning instead of relying on exact word matches.

---

### 3. Routine Generation

After selecting products, the application builds a skincare routine using a simple rule-based system.

The routine follows a standard skincare order while placing the recommended products into the appropriate steps.

Morning routine generally includes:

- Cleanser
- Serum
- Moisturizer
- Sunscreen

Night routine generally includes:

- Cleanser
- Treatment or serum
- Moisturizer

This keeps the routine organized while remaining easy to modify in the future.

---

### 4. User Accounts

Users can create an account and log in before using the application.

User information is stored in a SQLite database (`data/feedback.db`). Each user gets a unique ID, and their skin profile and generated routines are saved so they can log back in and pick up where they left off.

---

### 5. Real Products

Every product recommended in the routine is matched against a dataset of real skincare products (`data/products_clean.csv`) using the same embedding + FAISS similarity search. Users see up to 20 real matches per recommended product — including the brand, price, ingredients, and a link to buy — in both the Routine and Shop pages.

A special rule detects sunscreens by SPF branding or UV-filter ingredients, because the dataset does not label products with a sunscreen category.

---

### 6. Product Feedback

Users can upvote or downvote each recommended product. Votes are saved in SQLite, and each product's upvote / downvote counts are aggregated across every account, so the totals reflect the whole community rather than just one user.

---

## Technologies Used

### Frontend

- React
- CSS
- JavaScript

### Backend

- FastAPI
- Python
- SQLite

### Machine Learning

- Sentence Transformers
- FAISS
- Semantic embeddings

### Data Storage

- SQLite — user profiles and feedback
- JSON — semantic reference data and the placeholder product catalogue
- CSV — real skincare product dataset

---

## How to Run

### Backend

1. (Recommended) Create and activate a virtual environment (the project's working one is `venv`):
   ```
   venv\Scripts\activate
   ```
2. Install the dependencies:
   ```
   pip install -r requirements.txt
   ```
3. Start the API server:

   ```
   uvicorn api:app --reload
   ```

### Frontend

1. `cd skincare-ai-frontend`
2. `npm install`
3. `npm run dev`

Open the local URL printed by Vite (default `http://localhost:5173`).

---

## Project Structure

```
skincare-ai-frontend/
    React user interface (Chat, Routine Dashboard, Shop)

api.py
    FastAPI endpoints (login, recommend, feedback)

database.py
    SQLite connection and table creation

skincareAI.py
    Conversation logic, user profile and feedback functions

embedding_model.py
    Loads the embedding model

retrieve_skin_info.py
    Determines skin type, concerns, and goals using embeddings + FAISS

product_recommendation.py
    Finds matching skincare products using FAISS

real_products.py
    Matches recommendations to real purchasable products

routine.py
    Builds AM and PM skincare routines

data/
    feedback.db           SQLite database (profiles + feedback)
    skin_info.json        Reference descriptions used for skin analysis
    product.json          Placeholder product catalogue
    products_clean.csv    Real product dataset (brand, ingredients, price, link)
```

---

## Future Improvements

Completed along the way:

- Integrated real skincare product pages so users can view ingredients, pricing, and purchase links directly from the recommendations.
- Moved user data from JSON files into a SQLite database.
- Added a Shop page that lists real products for each recommended routine product.

Ideas still to explore:

- Allow users to enter their current skincare routine and receive feedback on potential issues, missing steps, or ingredient conflicts.
- Improve routine generation by considering product compatibility and ingredient interactions.
- Expand the skincare product database with more brands and products.
- Add image-based skin analysis to complement the text-based assessment.
- Move to a fully cloud-hosted database and deploy the app online.
- Track user progress over time by allowing users to save previous skin analyses and routines.
- Include filters for budget, skin sensitivity, preferred brands, and ingredient preferences.

---

## What I Learned

This project gave me experience building a full-stack application that combines React, FastAPI, SQL, and machine learning.

I learned how semantic embeddings can be used to understand user input, how FAISS can perform efficient similarity searches, and how those results can be integrated into a recommendation system. I also gained experience connecting a frontend to a backend, designing a SQLite database schema, migrating from plain JSON file storage, matching recommendations against a real product dataset, and designing an application around a conversational user experience.