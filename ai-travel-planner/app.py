import streamlit as st
from groq import Groq
import os
import json
import re
from PIL import Image
from dotenv import load_dotenv

load_dotenv()

# ── GROQ SETUP ──────────────────────────────────────────────
def get_groq_client():
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        return None
    return Groq(api_key=api_key)

def groq_text(prompt: str) -> str:
    client = get_groq_client()
    if client is None:
        raise ValueError("Missing GROQ API Key")

    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[
            {"role": "system", "content": "You are a helpful travel planner AI."},
            {"role": "user", "content": prompt}
        ],
        temperature=0.7
    )

    return response.choices[0].message.content


# ── JSON PARSER (FIXED) ─────────────────────────────────────
def parse_itinerary(raw):
    try:
        raw = raw.strip()

        # Remove markdown formatting
        raw = re.sub(r"```json", "", raw)
        raw = re.sub(r"```", "", raw)

        # Extract JSON block safely
        start = raw.find("{")
        end = raw.rfind("}") + 1

        if start == -1 or end == 0:
            return None

        clean_json = raw[start:end]

        return json.loads(clean_json)

    except Exception as e:
        print("Parse error:", e)
        return None


# ── PAGE CONFIG ─────────────────────────────────────────────
st.set_page_config(page_title="Wandr – Student Travel AI", page_icon="🧭", layout="wide")

# ── SIDEBAR ────────────────────────────────────────────────
with st.sidebar:
    st.title("🧭 Wandr")
    st.caption("AI Travel Planner for Students")

    destination = st.text_input("Destination", "Goa")
    days = st.slider("Trip Duration (days)", 1, 10, 4)
    budget = st.number_input("Budget (₹)", 1000, 50000, 10000)

    interests = st.multiselect(
        "Interests",
        ["Adventure", "Food", "Nature", "Party"],
        default=["Food"]
    )

# ── PROMPT ─────────────────────────────────────────────────
def build_prompt(dest, days, budget, interests):
    return f"""
Create a {days}-day travel itinerary for students.

Destination: {dest}
Budget: {budget} INR
Interests: {', '.join(interests)}

Return ONLY raw JSON. Do not include markdown, backticks, or explanation.

Format:
{{
 "destination": "...",
 "duration": {days},
 "total_estimated_cost": "...",
 "days":[
   {{
     "day":1,
     "plan":"..."
   }}
 ]
}}
"""

# ── UI ─────────────────────────────────────────────────────
st.title("🌍 AI Travel Planner for Students")

if st.button("✈️ Generate Itinerary"):
    with st.spinner("Generating..."):
        try:
            prompt = build_prompt(destination, days, budget, interests)
            raw = groq_text(prompt)

            data = parse_itinerary(raw)

            if data:
                st.success("Here is your plan 👇")

                st.subheader(data["destination"])
                st.write(f"💰 Budget: ₹{data['total_estimated_cost']}")

                for d in data["days"]:
                    st.markdown(f"### Day {d['day']}")
                    st.write(d["plan"])

                st.download_button(
                    "Download Plan",
                    data=json.dumps(data, indent=2),
                    file_name="travel_plan.json"
                )

            else:
                st.warning("Couldn't parse response")
                with st.expander("Raw Output"):
                    st.text(raw)

        except Exception as e:
            st.error(f"Error: {e}")

# ── IMAGE ANALYZER ─────────────────────────────────────────
st.markdown("---")
st.subheader("📸 Image Analyzer")

img_file = st.file_uploader("Upload Image", type=["jpg", "png"])

if img_file:
    image = Image.open(img_file)
    st.image(image)

    if st.button("Analyze Image"):
        with st.spinner("Analyzing..."):
            try:
                result = groq_text(
                    "Describe this travel location and suggest budget travel tips for students."
                )
                st.success(result)
            except Exception as e:
                st.error(e)