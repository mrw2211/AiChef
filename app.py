import streamlit as st
import requests

# --- Page Config ---
st.set_page_config(
    page_title="🍳 Fridge Chef AI",
    page_icon="🍳",
    layout="centered"
)

st.title("🍳 Fridge Chef AI")
st.markdown("Type the ingredients you have at home and I'll tell you what to cook!")
st.divider()

# --- API Key (Fixed by initializing first) ---
api_key = None

try:
    api_key = st.secrets["OPENROUTER_API_KEY"]
except:
    api_key = st.sidebar.text_input("OpenRouter API Key", type="password", placeholder="sk-or-v1-...")
    if not api_key:
        st.sidebar.warning("⚠️ Enter your API key to get started")

# --- Inputs ---
ingredients = st.text_area(
    "🥦 What ingredients do you have?",
    placeholder="e.g. eggs, cheese, tomatoes, bread, chicken, garlic...",
    height=120
)

col1, col2 = st.columns(2)
with col1:
    meal_type = st.selectbox("🍽️ Meal type", ["Any", "Breakfast", "Lunch", "Dinner", "Snack", "Dessert"])
with col2:
    diet = st.selectbox("🥗 Dietary preference", ["None", "Vegetarian", "Vegan", "Low carb", "High protein"])

# --- Generate ---
if st.button("👨‍🍳 Find Recipes!", use_container_width=True, type="primary"):
    if not api_key:
        st.error("❌ Please enter your OpenRouter API key in the sidebar")
    elif not ingredients.strip():
        st.warning("⚠️ Please enter at least one ingredient!")
    else:
        prompt = f"""You are a professional chef and nutritionist.
The user has these ingredients: {ingredients}
Meal type preference: {meal_type}
Dietary preference: {diet}

Suggest 3 recipes they can make. For each recipe provide:
1. Recipe name with a fitting emoji
2. Which of their ingredients are used + any common pantry staples needed
3. Step-by-step cooking instructions (numbered)
4. Nutrition info per serving (calories, protein, carbs, fat)
5. A fun tip or variation

Format each recipe clearly with headers. Be practical and delicious!"""

        with st.spinner("👨‍🍳 Chef AI is thinking..."):
            try:
                response = requests.post(
                    url="https://openrouter.ai/api/v1/chat/completions",
                    headers={
                        "Authorization": f"Bearer {api_key}",
                        "Content-Type": "application/json",
                    },
                    json={
                        # Fixed: Uses OpenRouter's smart free-tier pool 
                        # to automatically bypass rate-limited models
                        "model": "openrouter/free",
                        "messages": [
                            {"role": "system", "content": "You are a helpful chef and nutritionist assistant."},
                            {"role": "user", "content": prompt}
                        ]
                    },
                    timeout=30
                )

                data = response.json()

                if response.status_code == 200:
                    result = data["choices"][0]["message"]["content"]
                    st.success("✅ Here's what you can cook!")
                    st.markdown(result)
                else:
                    st.error(f"❌ API Error: {data}")

            except Exception as e:
                st.error(f"❌ Error: {e}")

st.divider()
st.caption("Powered by OpenRouter Free Tier | Made with ❤️ using Streamlit")