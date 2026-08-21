import pandas as pd
import ast

# Read the raw CSV and produce a normalized version for the application.
KNOWN_MULTIWORD_BRANDS = ["The Ordinary", "La Roche-Posay", "Paula's Choice", "First Aid Beauty", "Drunk Elephant"]

df = pd.read_csv("../data/skincare_products_clean.csv")

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

# guess brand using knwon brand names
def guess_brand(product_name):
    for brand in KNOWN_MULTIWORD_BRANDS:
        if product_name .startswith(brand):
            return brand
        return product_name.split()[0]

df["ingredients"] = df["ingredients"].apply(parse_ingredients)

# Guess the brand from the first word because the source has no brand column.
df['brand_guess'] = df['product'].apply(guess_brand)

# Keep only the columns required by the cleaned-data schema.
df = df[['product', 'brand_guess', 'category', 'ingredients', 'price', 'product_url']]

# Save the cleaned data without adding a pandas index column.
df.to_csv("../data/products_clean.csv", index=False)

# Display a quick summary for verification.
print(df.shape)
print(df.head(3))
print(df["category"].unique())
        