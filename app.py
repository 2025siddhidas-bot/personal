import streamlit as st
import requests
import google.generativeai as genai
import random

# 1. Grab the secret keys safely
NOTION_TOKEN = st.secrets["NOTION_TOKEN"]
DATABASE_ID = st.secrets["DATABASE_ID"]
genai.configure(api_key=st.secrets["GEMINI_API_KEY"])

st.title("👨‍🍳 The Backpack AI Chef")

# 2. Get available pantry items from Notion
def get_pantry_items():
    url = f"https://api.notion.com/v1/databases/{DATABASE_ID}/query"
    headers = {
        "Authorization": f"Bearer {NOTION_TOKEN}",
        "Notion-Version": "2022-06-28",
        "Content-Type": "application/json"
    }
    payload = {"filter": {"property": "Available", "checkbox": {"equals": True}}}
    
    response = requests.post(url, headers=headers, json=payload)
    data = response.json()
    
    ingredients = []
    for page in data.get("results", []):
        try:
            # Using "Ingredient" based on your previous fix!
            name = page["properties"]["Ingredient"]["title"][0]["text"]["content"]
            ingredients.append(name)
        except (IndexError, KeyError):
            continue
    return ingredients

with st.spinner("Scanning your pantry..."):
    pantry_list = get_pantry_items()

st.success(f"Found {len(pantry_list)} available ingredients!")
st.write(", ".join(pantry_list))

# 3. User Inputs
col1, col2 = st.columns(2)
with col1:
    meal = st.selectbox("Meal Type", ["Breakfast", "Lunch", "Dinner", "Snack"])
with col2:
    vibe = st.selectbox("Vibe", ["Savory", "Sweet", "Comforting", "Spicy"])

# 4. Generate AI Recipe Function
def generate_new_recipe():
    model = genai.GenerativeModel('gemini-2.5-flash')
    # We add a random number to the prompt so the AI doesn't just repeat the exact same recipe
    prompt = f"""
    I have these ingredients available: {', '.join(pantry_list)}. 
    I want a {vibe} {meal}. 
    
    Provide EXACTLY ONE recipe. Format it clearly with these 3 distinct sections:
    
    ### 1. Recipe Overview
    (1-2 sentences describing the dish)
    
    ### 2. Ingredients
    (Include the exact estimated quantities needed for the dish based on standard portions)
    
    ### 3. Detailed Instructions
    (Step-by-step cooking guide)
    
    (Internal generation seed: {random.randint(1, 10000)} - ensure this is a unique and creative idea)
    """
    response = model.generate_content(prompt)
    st.session_state.recipe = response.text

# 5. Buttons and Display
if st.button("Generate Recipe 🪄", type="primary"):
    if not pantry_list:
        st.error("Your pantry is empty! Go shopping.")
    else:
        with st.spinner("Cooking up a recipe..."):
            generate_new_recipe()

# If a recipe exists in the app's memory, display it and show the regenerate button
if "recipe" in st.session_state:
    st.markdown(st.session_state.recipe)
    
    st.divider()
    if st.button("🔄 I don't like this one, give me another!"):
        with st.spinner("Scrapping that... trying something else!"):
            generate_new_recipe()
