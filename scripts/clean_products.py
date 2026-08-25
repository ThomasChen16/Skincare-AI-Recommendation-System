import pandas as pd
import ast
import os

# resolve paths relative to this script's location
BASE_DIR = os.path.dirname(os.path.abspath(__file__))           # ...\skincare_AI\scripts
DATA_PATH = os.path.join(os.path.dirname(BASE_DIR), "data", "products_clean.csv")  # ...\skincare_AI\data\products_clean.csv

# Read the raw CSV and produce a normalized version for the application.
KNOWN_MULTIWORD_BRANDS = ["The Ordinary", "La Roche-Posay", "Paula's Choice", "First Aid Beauty", "Drunk Elephant"]

df = pd.read_csv(DATA_PATH)

# rename columns to match schema
df = df.rename(columns={
    'product_name': 'product',
    'product_type': 'category',
    'clean_ingreds': 'ingredients',
})

# Remove any row where either the product name or ingredients value is missing.
# These fields are required for the cleaned data, so incomplete rows are excluded.
df = df.dropna(subset=['product', 'ingredients'])

def parse_ingredients(raw):
    # Convert list-formatted ingredients to readable text when possible.
    try:
        parsed = ast.literal_eval(raw)
        if isinstance(parsed, list):
            return ", ".join(parsed)
    except (ValueError, SyntaxError):
        pass
    
    return raw # already plain text, leave as is

# Guess brand using known brand names.
def guess_brand(product_name):
    for brand in KNOWN_MULTIWORD_BRANDS:
        if product_name.startswith(brand):
            return brand

    # Return first word only when no known multiword brand matches
    return product_name.split()[0]

# change currency GBP -> USD
GBP_TO_USD = 1.27 # fixed rate
def gbp_to_usd(price_str):
    # strip the pound symbol and any whitespace, then parse the number
    try:
        amount = float(str(price_str).replace('£', '').replace('Â£', '').strip())
    except (ValueError, TypeError):
        return price_str # leave non-numeric/unparseable values as is

    # return converted value in USD with two decimal places
    return f"${amount * GBP_TO_USD:,.2f}"

df["ingredients"] = df["ingredients"].apply(parse_ingredients)

# Guess the brand from the first word because the source has no brand column.
df['brand_guess'] = df['product'].apply(guess_brand)

df['price'] = df['price'].apply(gbp_to_usd)

# Keep only the columns required by the cleaned-data schema.
df = df[['product', 'brand_guess', 'category', 'ingredients', 'price', 'product_url']]

# Save the cleaned data without adding a pandas index column.
df.to_csv(DATA_PATH, index=False)

# Display a quick summary for verification.
print(df.shape)
print(df.head(3))
print(df["category"].unique())


        