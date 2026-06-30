import streamlit as st
import requests
import base64

# --- Page Config ---
st.set_page_config(
    page_title="🍳 Fridge Chef AI",
    page_icon="🍳",
    layout="centered"
)

# --- Luxury Theme CSS ---
st.markdown("""
<style>
    h1 {
        color: #E8742C !important;
        font-weight: 600;
        letter-spacing: 1px;
    }
    .stButton > button {
        background-color: #E8742C;
        color: #0E0E10;
        border: none;
        font-weight: 600;
        letter-spacing: 0.5px;
        transition: all 0.2s ease;
    }
    .stButton > button:hover {
        background-color: #C75F1F;
        color: #0E0E10;
        transform: scale(1.01);
    }
    hr {
        border-color: #E8742C !important;
        opacity: 0.3;
    }
    .stTextArea textarea, .stTextInput input {
        border: 1px solid #E8742C !important;
        background-color: #FDF3E7 !important;
        color: #0E0E10 !important;
    }
    [data-testid="stSidebar"] {
        background-color: #1A1A1D;
        border-right: 1px solid #E8742C;
    }
</style>
""", unsafe_allow_html=True)

st.title("🍳 Fridge Chef AI")
st.markdown("Type the ingredients you have at home and I'll tell you what to cook!")
st.divider()

# --- API Key (Fixed by initializing first) ---
api_key = None

try:
    api_key = st.secrets["OPENROUTER_API_KEY"]
except Exception:
    api_key = st.sidebar.text_input("OpenRouter API Key", type="password", placeholder="sk-or-v1-...")
    if not api_key:
        st.sidebar.warning("⚠️ Enter your API key to get started")

# --- Initialize the ingredients text in session_state once ---
if "ingredients_text" not in st.session_state:
    st.session_state["ingredients_text"] = ""

# If a photo detection just ran, apply the result BEFORE the widget is
# instantiated (Streamlit forbids changing a widget's value after creation).
if "pending_ingredients" in st.session_state:
    st.session_state["ingredients_text"] = st.session_state.pop("pending_ingredients")

# --- Inputs ---
# Bound directly to session_state via the `key` param, so edits the user
# makes (or detections from a photo below) persist correctly across reruns.
ingredients = st.text_area(
    "🥦 What ingredients do you have?",
    placeholder="e.g. eggs, cheese, tomatoes, bread, chicken, garlic...",
    height=120,
    key="ingredients_text"
)

st.divider()

# --- Photo Upload: Auto-detect Ingredients ---
st.markdown("#### 📸 Or snap a photo of your fridge/pantry")
photo = st.file_uploader(
    "Upload a photo and I'll detect the ingredients for you",
    type=["jpg", "jpeg", "png", "webp"],
    label_visibility="collapsed"
)

# Free vision models on OpenRouter get rate-limited often (shared pool).
# Try a few in order so a 429 on one doesn't block detection entirely.
VISION_MODELS_FALLBACK = [
    "google/gemma-4-31b-it:free",
    "nvidia/nemotron-nano-12b-v2-vl:free",
    "nvidia/nemotron-3-nano-omni-30b-a3b-reasoning:free",
]

if photo is not None:
    st.image(photo, caption="Your photo", width=280)
    if st.button("🔍 Detect Ingredients", use_container_width=True):
        if not api_key:
            st.error("❌ Please enter your OpenRouter API key in the sidebar")
        else:
            with st.spinner("👀 Looking through your fridge..."):
                img_bytes = photo.getvalue()
                img_b64 = base64.b64encode(img_bytes).decode("utf-8")
                mime = photo.type or "image/jpeg"

                last_error = None
                detected = None

                for model_name in VISION_MODELS_FALLBACK:
                    try:
                        vision_response = requests.post(
                            url="https://openrouter.ai/api/v1/chat/completions",
                            headers={
                                "Authorization": f"Bearer {api_key}",
                                "Content-Type": "application/json",
                            },
                            json={
                                "model": model_name,
                                "messages": [
                                    {
                                        "role": "user",
                                        "content": [
                                            {
                                                "type": "text",
                                                "text": "Look at this photo of a fridge or pantry. "
                                                        "List only the food ingredients you can clearly identify, "
                                                        "as a simple comma-separated list (no extra text, no numbering, no descriptions)."
                                            },
                                            {
                                                "type": "image_url",
                                                "image_url": {"url": f"data:{mime};base64,{img_b64}"}
                                            }
                                        ]
                                    }
                                ]
                            },
                            timeout=30
                        )

                        vision_data = vision_response.json()

                        if vision_response.status_code == 200:
                            detected = vision_data["choices"][0]["message"]["content"].strip()
                            break
                        else:
                            # If rate-limited (429), try the next model. Otherwise stop and show the error.
                            last_error = vision_data
                            err_code = vision_data.get("error", {}).get("code")
                            if err_code != 429:
                                break

                    except Exception as e:
                        last_error = str(e)

                if detected:
                    st.session_state["pending_ingredients"] = detected
                    st.success(f"✅ Detected: {detected}")
                    st.rerun()
                else:
                    st.error(f"❌ All vision models are busy right now. Please try again in a moment. ({last_error})")

col1, col2, col3 = st.columns(3)
with col1:
    meal_type = st.selectbox("🍽️ Meal type", ["Any", "Breakfast", "Lunch", "Dinner", "Snack", "Dessert"])
with col2:
    cuisine = st.selectbox(
        "🌍 Cuisine type",
        ["Any", "Italian", "Mexican", "Chinese", "Indian", "Mediterranean",
         "Japanese", "Thai", "French", "American", "Middle Eastern"]
    )
with col3:
    cook_time = st.selectbox(
        "⏱️ Cook time",
        ["Any", "Quick (under 15 min)", "Medium (15-30 min)", "Long (30-60 min)", "Slow (60+ min)"]
    )

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
Cuisine type preference: {cuisine}
Cook time preference: {cook_time}

Suggest 3 recipes they can make. For each recipe provide:
1. Recipe name with a fitting emoji
2. Which of their ingredients are used + any common pantry staples needed
3. Estimated cook time
4. Step-by-step cooking instructions (numbered)
5. Nutrition info per serving (calories, protein, carbs, fat)
6. A fun tip or variation

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
                        # Uses OpenRouter's smart free-tier pool
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
