import streamlit as st
import requests
import google.generativeai as genai
import random

# 1. Grab the secret keys safely
NOTION_TOKEN = st.secrets["NOTION_TOKEN"]
DATABASE_ID = st.secrets["DATABASE_ID"]
genai.configure(api_key=st.secrets["GEMINI_API_KEY"])

st.set_page_config(page_title="My AI Chef", page_icon="👨‍🍳")
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
            name = page["properties"]["Ingredient"]["title"][0]["text"]["content"]
            ingredients.append(name)
        except (IndexError, KeyError):
            continue
    return ingredients

with st.spinner("Scanning your pantry..."):
    pantry_list = get_pantry_items()

st.success(f"Found {len(pantry_list)} available ingredients!")
with st.expander("👀 See full pantry list"):
    st.write(", ".join(pantry_list))

st.divider()

# 3. User Inputs & Constraints
st.subheader("What are we cooking?")
preferred_ingredients = st.multiselect(
    "Any specific cravings? (Optional)",
    options=pantry_list,
    placeholder="e.g., Chicken, Rice..."
)

col1, col2, col3 = st.columns(3)
with col1:
    meal = st.selectbox("Meal Type", ["Breakfast", "Lunch", "Dinner", "Snack"])
with col2:
    vibe = st.selectbox("Vibe", ["Savory", "Sweet", "Comforting", "Spicy"])
with col3:
    difficulty = st.selectbox("Effort Level", ["Super Easy (5-10 mins)", "Moderate (30 mins)", "Elaborate (1 hr+)"])

col4, col5 = st.columns(2)
with col4:
    servings = st.number_input("Servings", min_value=1, max_value=10, value=1)
with col5:
    extra_notes = st.text_input("Extra Notes (Optional)", placeholder="e.g., Make it extra spicy, no dairy...")

# 4. Generate AI Recipe Function
def generate_new_recipe():
    model = genai.GenerativeModel('gemini-2.5-flash')
    
    craving_instruction = ""
    if len(preferred_ingredients) > 0:
        craving_instruction = f"- CRITICAL FOCUS: Must prominently feature these ingredients: {', '.join(preferred_ingredients)}."
        
    prompt = f"""
    I have these ingredients available: {', '.join(pantry_list)}. 
    
    Recipe Requirements:
    - Meal: {vibe} {meal}
    - Time/Effort Limit: {difficulty}
    - Servings: {servings} portion(s)
    - Additional user notes: {extra_notes if extra_notes else 'None'}
    {craving_instruction}
    
    STRICT BACKEND CONSTRAINTS:
    1. ONE POT RULE: I only have ONE pot/pan to cook with. All instructions and preparation MUST reflect using a single vessel. Keep it realistic to this constraint.
    2. CULTURAL PREFERENCE: I am Indian. Please lean heavily into Indian flavor profiles, spices, and cooking styles where appropriate given my ingredients.
    
    Provide EXACTLY ONE recipe. Format it clearly with these 3 distinct sections:
    
    ### 1. Recipe Overview
    (1-2 sentences describing the dish)
    
    ### 2. Ingredients
    (Include exact estimated quantities based on {servings} servings)
    
    ### 3. Detailed Instructions
    (Step-by-step cooking guide ensuring the one-pot rule is strictly followed)
    
    (Internal generation seed: {random.randint(1, 100000)} - ensure this is a unique and creative idea)
    """
    
    # The new "Crash Proof" block
    try:
        response = model.generate_content(prompt)
        st.session_state.recipe = response.text
    except Exception as e:
        error_msg = str(e)
        if "ResourceExhausted" in error_msg or "429" in error_msg:
            st.error(f"⏳ Whoa there, Chef! We hit an AI limit. Here is the exact error from Google so we know if it's per-minute or per-day:\n\n{error_msg}")
        else:
            st.error(f"An unexpected error occurred: {error_msg}")

# 5. Buttons and Display
if st.button("Generate Recipe 🪄", type="primary"):
    if not pantry_list:
        st.error("Your pantry is empty! Go shopping.")
    else:
        with st.spinner("Cooking up a recipe..."):
            generate_new_recipe()

if "recipe" in st.session_state:
    st.markdown(st.session_state.recipe)
    
    st.divider()
    if st.button("🔄 I don't like this one, give me another!"):
        with st.spinner("Scrapping that... trying something else!"):
            generate_new_recipe()
