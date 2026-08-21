# ======================== PLANING =========================
# routine building before product recommendations
# cleanser
# moisturizer
# sunscreen
# treatment/serum
Product_Rules = {
    "Cleanser": {
        "essential": True,
        "max": 1,
        "order": 1
    },
    "Toner": {
        "essential": False,
        "max": 1,
        "order": 2
    },
    "Treatment": {
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
    "Moisturizer": {
        "essential": True,
        "max": 1,
        "order": 4
    },
    "Oil / Facial Oil": {
        "essential": False,
        "max": 1,
        "order": 5
    },
    "Sunscreen": {
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
            if product_type == "Treatment":
                # acne and brightening are the only concerns that would require more than 1 treatment product
                if "acne" in context["concerns"] or "brightening" in context["concerns"]:
                    count = 2
                else:
                    count = 1
            else:
                count = 0
        
        # determine time for this product type
        if rules.get("require_am"):
            time = "am"
        elif context["time"] == "p.m":
            time = "pm"
        else:
            time = "am"
        
        plan.append({
            "category": product_type,
            "count": count,
            "order": rules.get("order", 999), # default order is 999 if not specified
            "time": time
        })

    # sort plan by order
    plan.sort(key=lambda x: x["order"])
    
    return plan
# =================== PLANING END ==========================