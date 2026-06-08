from embedding_model import get_model
import faiss # for faster similarity search
import numpy as np
from collections import defaultdict # for product score and reasons (less if statements as keys are created on the go)

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
def get_reference_embeddings():
    global reference_embeddings
    
    # Load model and create reference embeddings only once and reuse across files
    if not reference_embeddings:
        print("Creating reference embeddings...")
        model = get_model() # get loaded model
        
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

    return reference_embeddings 

faiss_index = None
metadata = None

def get_faiss_index():
    global faiss_index, metadata
    
    if faiss_index is None:
        print("Building reference FAISS index...")
        
        model = get_model() # get loaded model

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
    faiss_index = faiss.IndexFlatIP(dim)
    faiss_index.add(xb)
    
    return faiss_index, metadata


configuration = {
    "skin_type": {"min_similarity": 0.6, "top_k": 1},
    "concerns": {"min_similarity": 0.5, "top_k": 3},
    "goals": {"min_similarity": 0.4,"top_k": 3}
}

# function to perform FAISS search for similar reference text to user input and return the scores and labels of the matches
# semantics
def faiss_search(text, top_k=20):
    model = get_model() # get loaded model
    # embed the input text
    user_emb = model.encode(text)
    user_emb = np.array([user_emb]).astype("float32")
    
    # normalize the user embedding for cosine similarity
    faiss.normalize_L2(user_emb)
    
    # search the index for the top_k most similar embeddings and return the scores and indices of the matches
    scores, indices = faiss_index.search(user_emb, top_k)

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
        aggregated[label] = float(max(scores))
        
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
    scores = [float(s) for s in scores]
    
    # detected labels candidates
    label_scores = {}
    
    # loop through scores and indices and get the category and label for each match from metadata
    for score, idx in zip(scores, indices):
        group, label = metadata[idx]
        
        if group != category:
            continue
        
        # take max score per label
        if label not in label_scores:
            label_scores[label] = float(score)
        else:
            label_scores[label] = float(max(label_scores[label], score))
    
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