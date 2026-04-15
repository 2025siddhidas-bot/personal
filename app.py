import streamlit as st
import requests
import google.generativeai as genai

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
    # Filter only where "Available" is checked
    payload = {"filter": {"property": "Available", "checkbox": {"equals": True}}}
    
    response = requests.post(url, headers=headers, json=payload)
    data = response.json()
    
    ingredients = []
    for page in data.get("results", []):
        # NOTE: If your main column is named "Ingredient" instead of "Name", change "Name" below!
        try:
            name = page["properties"]["Ingredient"]["title"][0]["text"]["content"]
            ingredients.append(name)
        except IndexError:
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

# 4. Generate AI Recipe
if st.button("Generate Recipes 🪄", type="primary"):
    if not pantry_list:
        st.error("Your pantry is empty! Go shopping.")
    else:
        with st.spinner("Cooking up ideas..."):
            model = genai.GenerativeModel('gemini-1.5-flash')
            prompt = f"I have these ingredients: {', '.join(pantry_list)}. I want a {vibe} {meal}. Suggest 3 distinct recipes I can make. Give a 1-sentence description and a 1-5 star effort rating for each."
            response = model.generate_content(prompt)
            st.markdown(response.text)
