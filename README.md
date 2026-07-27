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
- User profiles stored locally using JSON
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

User information is stored in JSON files, allowing the application to save profile information without requiring a database. This keeps the project lightweight while still demonstrating basic account management.

---

## Technologies Used

### Frontend

- React
- CSS
- JavaScript

### Backend

- FastAPI
- Python

### Machine Learning

- Sentence Transformers
- FAISS
- Semantic embeddings

### Data Storage

- JSON

---

## Project Structure

```
frontend/
    React user interface

backend/
    FastAPI API

embedding_model.py
    Loads the embedding model

retrieve_skin_info.py
    Determines skin type, concerns, and goals

product_recommendation.py
    Finds matching skincare products using FAISS

routine.py
    Builds AM and PM skincare routines

profile.json
    Stores user account information
```

---

## Future Improvements

Some features I would like to add in the future include:

- Integrate real skincare product pages so users can view ingredients, pricing, and purchase links directly from the recommendations.
- Allow users to enter their current skincare routine and receive feedback on potential issues, missing steps, or ingredient conflicts.
- Improve routine generation by considering product compatibility and ingredient interactions.
- Expand the skincare product database with more brands and products.
- Add image-based skin analysis to complement the text-based assessment.
- Store user data in a cloud database instead of local JSON files.
- Track user progress over time by allowing users to save previous skin analyses and routines.
- Include filters for budget, skin sensitivity, preferred brands, and ingredient preferences.

---

## What I Learned

This project gave me experience building a full-stack application that combines React, FastAPI, and machine learning.

I learned how semantic embeddings can be used to understand user input, how FAISS can perform efficient similarity searches, and how those results can be integrated into a recommendation system. It also helped me gain experience connecting a frontend to a backend, managing user data, and designing an application around a conversational user experience.