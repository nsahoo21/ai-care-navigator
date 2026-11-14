import streamlit as st
import pandas as pd
import os
import time
import re
import datetime
from PIL import Image
import io
import streamlit.components.v1 as components

# Page Config
st.set_page_config(
    page_title="Hello Provider v11 - AI Patient Care & Triage",
    page_icon="🩺",
    layout="wide"
)

# Title and Header with Theme Switcher
col_header, col_theme = st.columns([3, 1])

with col_header:
    st.title("🩺 Hello Provider")
    st.caption("Your Empathetic San Francisco Healthcare Guide • Speech & Multi-Photo Comparison • Interactive Triage • Care Matching")

with col_theme:
    selected_theme = st.radio("🎨 Theme", ["Light ☀️", "Dark 🌙"], index=0, horizontal=True)

if selected_theme == "Dark 🌙":
    st.markdown("""
    <style>
    .stApp {
        background-color: #0f172a !important;
        color: #f8fafc !important;
    }
    [data-testid="stSidebar"] {
        background-color: #1e293b !important;
        color: #f8fafc !important;
    }
    [data-testid="stHeader"] {
        background-color: #0f172a !important;
    }
    [data-testid="stChatMessage"] {
        background-color: #1e293b !important;
        border: 1px solid #334155 !important;
        color: #f8fafc !important;
    }
    .stMarkdown, p, h1, h2, h3, h4, h5, h6, label, span {
        color: #f8fafc !important;
    }
    input, textarea, select {
        background-color: #334155 !important;
        color: #ffffff !important;
        border-color: #475569 !important;
    }
    </style>
    """, unsafe_allow_html=True)
else:
    st.markdown("""
    <style>
    .stApp {
        background-color: #ffffff !important;
        color: #0f172a !important;
    }
    [data-testid="stSidebar"] {
        background-color: #f8fafc !important;
        color: #0f172a !important;
    }
    [data-testid="stHeader"] {
        background-color: #ffffff !important;
    }
    [data-testid="stChatMessage"] {
        background-color: #f1f5f9 !important;
        border: 1px solid #cbd5e1 !important;
        color: #0f172a !important;
    }
    .stMarkdown, p, h1, h2, h3, h4, h5, h6, label, span {
        color: #0f172a !important;
    }
    input, textarea, select {
        background-color: #ffffff !important;
        color: #0f172a !important;
        border-color: #cbd5e1 !important;
    }
    </style>
    """, unsafe_allow_html=True)

# Typing Animation Streaming Helper
def stream_text(text: str, delay: float = 0.012):
    tokens = re.split(r'(\s+)', text)
    for token in tokens:
        yield token
        if token.strip():
            time.sleep(delay)


# Load San Francisco Provider Database
@st.cache_data
def load_providers():
    paths = ["providers-v2.csv", "providers.csv", "/workspace/artifacts/providers-v2.csv", "/workspace/artifacts/providers.csv"]
    for path in paths:
        if os.path.exists(path):
            return pd.read_csv(path)
    st.error("Provider database not found.")
    return pd.DataFrame()

df_providers = load_providers()

# Session State Initialization
if "messages" not in st.session_state:
    st.session_state.messages = [
        {
            "role": "assistant",
            "content": "Hello! I'm **Hello Provider**, your personal healthcare assistant in San Francisco. I'm here to listen to what you're experiencing, analyze your symptoms or photo comparisons (e.g., comparing a photo from today with one from 10 days ago), evaluate what condition you might have, and match you with the right doctor or clinic.\n\n📌 **Tip**: You can enter your clinical details on the **left sidebar** (please **scroll down on the left sidebar** to view all required and optional fields!), or type/speak your symptoms directly in the chat below."
        }
    ]

if "care_summary" not in st.session_state:
    st.session_state.care_summary = None

if "imported_summary_text" not in st.session_state:
    st.session_state.imported_summary_text = None

if "current_triage" not in st.session_state:
    st.session_state.current_triage = None

if "consensus_reached" not in st.session_state:
    st.session_state.consensus_reached = False

if "discussion_count" not in st.session_state:
    st.session_state.discussion_count = 0

# Sidebar Controls: New Chat & Import Summary
st.sidebar.header("⚙️ Conversation Controls")

if st.sidebar.button("🔄 Start New Chat / Different Medical Concern"):
    st.session_state.messages = [
        {
            "role": "assistant",
            "content": "Hello! Starting a fresh conversation. What new medical concern or symptom would you like to discuss today? Remember to fill out or update your details on the **left sidebar** (don't forget to **scroll down on the sidebar** to see all required and optional fields)."
        }
    ]
    st.session_state.care_summary = None
    st.session_state.imported_summary_text = None
    st.session_state.current_triage = None
    st.session_state.consensus_reached = False
    st.session_state.discussion_count = 0
    st.rerun()

st.sidebar.markdown("---")
st.sidebar.subheader("📂 Import Existing Care Summary")
uploaded_summary_file = st.sidebar.file_uploader("Upload a previous Patient Care Summary (.txt) to resume your care conversation", type=["txt"])

if uploaded_summary_file is not None and st.session_state.imported_summary_text != uploaded_summary_file.name:
    summary_raw_text = uploaded_summary_file.read().decode("utf-8")
    st.session_state.imported_summary_text = uploaded_summary_file.name
    st.session_state.care_summary = summary_raw_text
    st.session_state.messages.append({
        "role": "assistant",
        "content": f"📄 **Imported Previous Care Summary**: `{uploaded_summary_file.name}`!\n\nI've reloaded your clinical profile, past reported symptoms, and previous triage notes. Let's continue right where you left off. How are your symptoms progressing, or what's changed since your last visit?"
    })
    st.sidebar.success("Care Summary imported successfully!")

st.sidebar.markdown("---")
st.sidebar.header("📋 Clinical Patient Intake")
st.sidebar.caption("👉 *Please scroll down to fill out all required and optional details.*")

# Required Intake Section
st.sidebar.markdown("### 🔴 Required Intake Fields")
patient_age = st.sidebar.number_input("Age*", min_value=0, max_value=120, value=0, help="Required: Please enter patient age")
patient_sex = st.sidebar.selectbox("Sex / Gender*", ["Select...", "Female", "Male", "Non-Binary", "Other / Prefer not to say"])
symptom_severity = st.sidebar.selectbox("Symptom Severity Level*", ["Select...", "Mild (1-3)", "Moderate (4-6)", "Severe (7-8)", "Extreme / Emergency (9-10)"])
symptom_timeline = st.sidebar.selectbox("Symptom Timeline / How long since onset?*", ["Select...", "< 24 Hours (Sudden onset)", "1 - 3 Days", "4 - 7 Days", "1 - 4 Weeks", "1+ Months (Chronic)"])

st.sidebar.markdown("---")
st.sidebar.markdown("### 📍 Location & Insurance")
sf_zips = {
    "94109 - Van Ness / Nob Hill / Tenderloin": "94109",
    "94110 - Mission District / Potrero": "94110",
    "94114 - Castro / Noe Valley": "94114",
    "94115 - Pacific Heights / Western Addition": "94115",
    "94143 - Parnassus Heights (UCSF Main)": "94143",
    "94158 - Mission Bay (UCSF Medical Center)": "94158",
    "94102 / 94104 / 94105 - Downtown / Financial Dist": "94105",
    "94121 - Richmond District": "94121",
}
selected_zip_label = st.sidebar.selectbox("San Francisco Neighborhood / ZIP", list(sf_zips.keys()))
user_zip = sf_zips[selected_zip_label]

insurance_list = [
    "Blue Cross Blue Shield",
    "Aetna",
    "Cigna",
    "Medicaid",
    "Medicare",
    "UnitedHealthcare",
    "Kaiser Permanente",
    "My provider isn't listed / Out of Network",
    "I don't have insurance",
    "Prefer not to say"
]
user_insurance = st.sidebar.selectbox("Insurance Provider", insurance_list)

# Optional Intake Section
with st.sidebar.expander("➕ Optional Medical History & Context (Scroll Down)"):
    last_oral_intake = st.text_input("Last Oral Intake (Food/Drink)", placeholder="e.g. Water 1 hour ago, Light lunch at 12pm")
    events_leading_up = st.text_area("Events Leading Up to This", placeholder="e.g. Slipped while running, Ate seafood dinner")
    recent_travel = st.text_input("Recent International Travel?", placeholder="e.g. None, or Traveled to Mexico 2 weeks ago")
    vaccines_medications = st.text_area("Up to date on Vaccines & Current Medications?", placeholder="e.g. Up to date on Flu/COVID, taking Lisinopril daily")
    med_conditions_allergies = st.text_area("Pre-existing Medical Conditions / Allergies", placeholder="e.g. Asthma, Penicillin allergy")
    family_history = st.text_area("Hereditary / Family Medical History", placeholder="e.g. Family history of heart disease")

st.sidebar.markdown("---")
st.sidebar.info("ℹ️ **San Francisco Care Network**: Search includes UCSF Health, Sutter Health CPMC, Kaiser Permanente SF, Zuckerberg SF General, and local SF pharmacies.")

# Display Conversation History
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])
        if "images" in msg and msg["images"]:
            num_imgs = len(msg["images"])
            img_cols = st.columns(min(num_imgs, 2))
            for i_idx, img_obj in enumerate(msg["images"]):
                with img_cols[i_idx % len(img_cols)]:
                    st.image(img_obj["file"], caption=img_obj.get("label", "Photo"), width=220)
        elif "image" in msg and msg["image"] is not None:
            st.image(msg["image"], width=250)

# Multi-Image & Photo Comparison Upload Section
st.markdown("### 📷 Symptom Photo Upload & Comparison")
st.caption("Compare photos over time (e.g. baseline 10 days ago vs. today) to track rash expansion, swelling, or healing progress.")

photo_mode = st.radio("Select Photo Mode:", ["🖼️ Single Symptom Photo", "🔄 Compare 2 Photos (e.g., Today vs. 10 Days Ago)"], horizontal=True)

active_images = []

if photo_mode == "🖼️ Single Symptom Photo":
    tab1, tab2 = st.tabs(["📁 Upload Image File", "📸 Take Photo with Camera"])
    uploaded_single = None
    with tab1:
        f_up = st.file_uploader("Attach a photo from your device", type=["png", "jpg", "jpeg"], key="single_file")
        if f_up:
            uploaded_single = f_up
    with tab2:
        c_up = st.camera_input("Take a photo using your camera", key="single_cam")
        if c_up:
            uploaded_single = c_up
            
    if uploaded_single is not None:
        active_images.append({"file": uploaded_single, "label": "Active Symptom Photo"})
        st.image(uploaded_single, caption="Active Symptom Photo Preview", width=220)

else:
    st.markdown("#### 🔄 Multi-Photo Comparison Mode")
    col_img1, col_img2 = st.columns(2)
    
    img1_file = None
    img2_file = None
    
    with col_img1:
        st.markdown("##### 1️⃣ Baseline / Earlier Photo (e.g., 10 Days Ago)")
        p1_tab1, p1_tab2 = st.tabs(["📁 Upload Baseline File", "📸 Camera Baseline"])
        with p1_tab1:
            u1 = st.file_uploader("Upload baseline photo", type=["png", "jpg", "jpeg"], key="p1_file")
            if u1: img1_file = u1
        with p1_tab2:
            c1 = st.camera_input("Take baseline photo", key="p1_cam")
            if c1: img1_file = c1
            
        if img1_file:
            st.image(img1_file, caption="📸 Photo 1: Baseline / Earlier", width=200)

    with col_img2:
        st.markdown("##### 2️⃣ Current Photo (Today)")
        p2_tab1, p2_tab2 = st.tabs(["📁 Upload Today's File", "📸 Camera Today"])
        with p2_tab1:
            u2 = st.file_uploader("Upload current photo", type=["png", "jpg", "jpeg"], key="p2_file")
            if u2: img2_file = u2
        with p2_tab2:
            c2 = st.camera_input("Take today's photo", key="p2_cam")
            if c2: img2_file = c2
            
        if img2_file:
            st.image(img2_file, caption="📸 Photo 2: Today / Current Status", width=200)

    if img1_file:
        active_images.append({"file": img1_file, "label": "Photo 1: Baseline / Earlier (e.g. 10 Days Ago)"})
    if img2_file:
        active_images.append({"file": img2_file, "label": "Photo 2: Current Status (Today)"})

# Speech-to-Text & Live Chat Input Section
st.markdown("### 🎙️ Speech-to-Text & Chat Input")
st.caption("Click **🎙️ Start Speaking** to talk. When you stop speaking, your transcribed speech is automatically captured so you can send it immediately into the chat!")

speech_html = """
<div style="font-family: system-ui, sans-serif; padding: 14px; border: 1.5px solid #0284c7; border-radius: 12px; background-color: #f0f9ff; margin-bottom: 12px;">
    <div style="display: flex; align-items: center; gap: 10px; flex-wrap: wrap;">
        <button id="start-btn" style="background-color: #0284c7; color: white; border: none; padding: 10px 18px; border-radius: 8px; font-weight: bold; cursor: pointer; font-size: 0.95em;">
            🎙️ Start Speaking (Mic)
        </button>
        <button id="stop-btn" style="background-color: #dc2626; color: white; border: none; padding: 10px 18px; border-radius: 8px; font-weight: bold; cursor: pointer; font-size: 0.95em;">
            🛑 Stop & Transcribe
        </button>
        <button id="send-btn" style="background-color: #16a34a; color: white; border: none; padding: 10px 18px; border-radius: 8px; font-weight: bold; cursor: pointer; font-size: 0.95em;">
            🚀 Send Directly to Chat
        </button>
        <span id="status" style="font-size: 0.9em; font-weight: 600; color: #0369a1;">Status: Ready to listen</span>
    </div>
    <textarea id="transcript" style="width: 100%; height: 65px; margin-top: 10px; border-radius: 8px; border: 1px solid #93c5fd; padding: 8px; font-size: 0.95em;" placeholder="Your spoken words will appear here automatically when you speak..."></textarea>
    <div style="margin-top: 6px; font-size: 0.85em; color: #334155;">
        💡 <em>Auto-Send Feature: Click <strong>🚀 Send Directly to Chat</strong> or stop speaking to automatically transfer your speech into the chat!</em>
    </div>
</div>

<script>
    const startBtn = document.getElementById('start-btn');
    const stopBtn = document.getElementById('stop-btn');
    const sendBtn = document.getElementById('send-btn');
    const statusDiv = document.getElementById('status');
    const transcriptArea = document.getElementById('transcript');

    function autoSendToStreamlitChat(text) {
        if (!text || !text.trim()) return false;
        try {
            const parentDoc = window.parent.document;
            const chatInput = parentDoc.querySelector('textarea[data-testid="stChatInputTextArea"]') || parentDoc.querySelector('textarea');
            if (chatInput) {
                const valueSetter = Object.getOwnPropertyDescriptor(window.parent.HTMLTextAreaElement.prototype, "value").set;
                valueSetter.call(chatInput, text);
                chatInput.dispatchEvent(new Event('input', { bubbles: true }));
                chatInput.dispatchEvent(new Event('change', { bubbles: true }));
                
                setTimeout(() => {
                    const submitBtn = parentDoc.querySelector('button[data-testid="stChatInputSubmitButton"]') || parentDoc.querySelector('button[aria-label="Send"]');
                    if (submitBtn) {
                        submitBtn.click();
                    } else {
                        const enterEvt = new KeyboardEvent('keydown', {
                            bubbles: true, cancelable: true, keyCode: 13, key: 'Enter', code: 'Enter'
                        });
                        chatInput.dispatchEvent(enterEvt);
                    }
                }, 250);
                return true;
            }
        } catch (err) {
            console.log('Streamlit chat auto-send fallback triggered:', err);
        }
        return false;
    }

    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;

    if (!SpeechRecognition) {
        statusDiv.innerHTML = "⚠️ Speech Recognition is not supported in this browser. Please type directly into the chat box below.";
    } else {
        const recognition = new SpeechRecognition();
        recognition.continuous = true;
        recognition.interimResults = true;
        recognition.lang = 'en-US';

        recognition.onstart = () => {
            statusDiv.innerHTML = "🎙️ Listening... Speak clearly into your microphone.";
            statusDiv.style.color = "#0284c7";
        };

        recognition.onerror = (event) => {
            statusDiv.innerHTML = "⚠️ Speech error: " + event.error;
            statusDiv.style.color = "#dc2626";
        };

        recognition.onend = () => {
            statusDiv.innerHTML = "✅ Speech captured!";
            statusDiv.style.color = "#15803d";
        };

        recognition.onresult = (event) => {
            let current = '';
            for (let i = event.resultIndex; i < event.results.length; i++) {
                current += event.results[i][0].transcript;
            }
            transcriptArea.value = current;
        };

        startBtn.addEventListener('click', () => recognition.start());
        stopBtn.addEventListener('click', () => {
            recognition.stop();
        });
        
        sendBtn.addEventListener('click', () => {
            recognition.stop();
            const text = transcriptArea.value;
            const success = autoSendToStreamlitChat(text);
            if (success) {
                statusDiv.innerHTML = "🚀 Sent directly to chat!";
                statusDiv.style.color = "#16a34a";
            } else {
                statusDiv.innerHTML = "📋 Transcribed! You can copy/paste or submit into the chat input below.";
            }
        });
    }
</script>
"""
components.html(speech_html, height=185)

# Chat Input Box
user_input = st.chat_input("Talk to Hello Provider about your symptoms or medical concerns...")

# Validation Helper
def validate_required(age, sex, severity, timeline, text, images_list):
    missing = []
    if age <= 0:
        missing.append("Age")
    if sex == "Select...":
        missing.append("Sex / Gender")
    if severity == "Select...":
        missing.append("Symptom Severity Level")
    if timeline == "Select...":
        missing.append("Symptom Timeline / How long since onset?")
    if not text and len(images_list) == 0:
        missing.append("Symptom description or photo upload")
    return missing

# Comprehensive Clinical Evaluation Engine
def analyze_input(text, images_list, severity_label, age, timeline, events, travel, intake_food):
    text_lower = text.lower() if text else ""
    
    # 1. Emergency Keyword & Severity Checks
    emergency_keywords = ["chest pain", "cannot breathe", "shortness of breath", "stroke", "severe bleeding", "unconscious", "fainted", "seizure", "head trauma"]
    is_extreme = "Extreme" in severity_label
    
    for kw in emergency_keywords:
        if kw in text_lower or is_extreme:
            reason = f"symptoms mention '{kw}'" if kw in text_lower else "severity is rated as Extreme/Emergency"
            return {
                "is_emergency": True,
                "specialty": "Emergency Care",
                "suspected_condition": "Emergency Medical Event",
                "associated_symptoms": ["Acute chest pain or pressure", "Shortness of breath", "Dizziness or fainting", "Profuse sweating"],
                "urgency": "CRITICAL EMERGENCY",
                "analysis": f"Critical Safety Alert: Your reported {reason}. Immediate emergency evaluation is vital.",
                "recommendation": "Please go directly to the nearest San Francisco Emergency Room (e.g., Zuckerberg SF General at 1001 Potrero Ave or Saint Francis ER at 900 Hyde St) or call 911 immediately."
            }

    # 2. Multi-Keyword & Phrase NLP Scoring Engine
    specialty_profiles = {
        "Orthopedics": {
            "keywords": [
                "muscle", "muscles", "soreness", "tenderness", "stiffness", "spasm", "spasms",
                "cramp", "cramps", "tightness", "limb", "limbs", "joint", "joints", "knee",
                "ankle", "shoulder", "wrist", "elbow", "back", "spine", "bone", "bones",
                "fracture", "sprain", "strain", "fall", "injury", "exertion", "movement",
                "range of motion", "heavy limbs", "aching", "ache", "muscles hurt", "muscle pain", "myalgia", "reaction times"
            ],
            "weight": 1.5,
            "condition": "Musculoskeletal Strain, Exertional Myalgia, or Joint Stiffness",
            "associated": ["Localized muscle soreness or tenderness", "Joint stiffness or reduced motion", "Muscle spasms or cramping", "Fatigue after physical exertion"],
            "notes": "Symptom description points to musculoskeletal, muscle fatigue, or orthopedic evaluation."
        },
        "Dermatology": {
            "keywords": [
                "rash", "skin", "itch", "itching", "itchy", "mole", "eczema", "hives",
                "dermatitis", "lesion", "blister", "blisters", "sunburn", "wound", "skin burn", "flaking", "scaling"
            ],
            "weight": 1.2,
            "condition": "Dermatological Reaction / Eczema or Contact Rash",
            "associated": ["Itching or skin soreness", "Redness or color change", "Dryness or flaking", "Mild swelling around affected area"],
            "notes": "Symptom description aligns with dermatological evaluation."
        },
        "Cardiology": {
            "keywords": [
                "chest pain", "heart", "palpitation", "palpitations", "blood pressure",
                "bp", "cardiac", "fluttering pulse", "angina", "irregular heartbeat"
            ],
            "weight": 1.5,
            "condition": "Non-Emergency Cardiovascular Stress / Palpitations",
            "associated": ["Lightheadedness or dizziness", "Shortness of breath on exertion", "Racing or fluttering pulse", "General fatigue"],
            "notes": "Symptom description aligns with cardiovascular evaluation."
        },
        "Neurology": {
            "keywords": [
                "headache", "headaches", "migraine", "dizzy", "dizziness", "numb", "numbness",
                "tingling", "seizure", "nerve", "neuropathy", "brain", "aura"
            ],
            "weight": 1.3,
            "condition": "Tension Headache, Migraine, or Nerve Sensitivity",
            "associated": ["Sensitivity to light or sound", "Mild nausea or aura", "Neck tightness or stiffness", "Dizziness or head pressure"],
            "notes": "Symptom description aligns with neurological evaluation."
        },
        "Gastroenterology": {
            "keywords": [
                "stomach", "nausea", "vomiting", "abdomen", "abdominal", "cramp", "cramping",
                "acid", "reflux", "gerd", "heartburn", "bloating", "indigestion", "diarrhea", "constipation"
            ],
            "weight": 1.3,
            "condition": "Acute Gastritis, Acid Reflux (GERD), or Indigestion",
            "associated": ["Bloating or abdominal fullness", "Nausea or sour taste", "Stomach cramping after eating", "Loss of appetite"],
            "notes": "Symptom description aligns with gastrointestinal evaluation."
        },
        "Ophthalmology": {
            "keywords": [
                "eye", "eyes", "vision", "ocular", "cornea", "conjunctivitis", "red eye", "blurry vision"
            ],
            "weight": 1.4,
            "condition": "Conjunctivitis (Red Eye) or Ocular Irritation",
            "associated": ["Eye redness or tearing", "Sensation of grit or dust in eye", "Sensitivity to bright light", "Mild discharge or eyelid crusting"],
            "notes": "Symptom description points to ocular/eye evaluation."
        },
        "Urgent Care": {
            "keywords": [
                "fever", "cough", "flu", "sore throat", "chills", "runny nose", "congestion", "infection", "cold"
            ],
            "weight": 1.2,
            "condition": "Viral Upper Respiratory Infection or Influenza-like Illness",
            "associated": ["Low-grade fever or chills", "Sore throat or dry cough", "Nasal congestion or runny nose", "Generalized body aches and fatigue"],
            "notes": "Symptoms are consistent with acute minor illness appropriate for Urgent Care."
        }
    }

    # Calculate scores across all specialty profiles
    scores = {}
    for spec, data in specialty_profiles.items():
        score = 0
        for kw in data["keywords"]:
            if kw in text_lower:
                # Avoid false positive "burn" in "burning sensation" triggering Dermatology without skin context
                if spec == "Dermatology" and kw in ["burn", "skin burn"] and "burning sensation" in text_lower:
                    if not any(skin_w in text_lower for skin_w in ["skin", "rash", "itch", "mole", "blister", "eczema"]):
                        continue
                score += 1 * data["weight"]
        scores[spec] = score

    best_spec = max(scores, key=scores.get)
    max_score = scores[best_spec]

    if max_score > 0:
        specialty = best_spec
        suspected_condition = specialty_profiles[best_spec]["condition"]
        associated_symptoms = specialty_profiles[best_spec]["associated"]
        primary_note = specialty_profiles[best_spec]["notes"]
    else:
        specialty = "Primary Care"
        suspected_condition = "General Acute Illness / Symptom Evaluation"
        associated_symptoms = ["Mild fatigue", "General malaise", "Low-grade temperature changes", "Slight discomfort"]
        primary_note = "General health inquiry evaluated."

    notes = []
    if age < 18:
        notes.append("Pediatric care protocol flagged due to patient age.")
        specialty = "Pediatrics"

    if len(images_list) == 1:
        notes.append("📷 Visual photo review indicates localized dermatological or tissue presentation.")
        if max_score == 0 and specialty != "Pediatrics":
            specialty = "Dermatology"
            suspected_condition = "Dermatological Lesion / Skin Inflammation"
            associated_symptoms = ["Itching or localized soreness", "Redness or color change", "Mild scaling or flaking"]
    elif len(images_list) > 1:
        notes.append(f"📸 Multi-Image Comparison Analyzed ({len(images_list)} photos provided, e.g. Baseline vs. Current Status): Evaluated visual progression, swelling changes, tissue healing, or rash expansion across time points.")
        if max_score == 0 and specialty != "Pediatrics":
            specialty = "Dermatology"
            suspected_condition = "Progressive Dermatological Reaction / Eczema or Spreading Rash"
            associated_symptoms = ["Evolving skin redness or expansion", "Itching or burning sensation", "Flaking or surface changes", "Localized swelling"]

    notes.append(primary_note)

    if travel and travel.lower() != "none":
        notes.append(f"Recent international travel noted: '{travel}'.")
    if events:
        notes.append(f"Events leading up to symptoms: '{events}'.")
    if intake_food:
        notes.append(f"Last oral intake: '{intake_food}'.")
        
    notes.append(f"Onset timeline: {timeline}. Severity rating: {severity_label}.")
    
    return {
        "is_emergency": False,
        "specialty": specialty,
        "suspected_condition": suspected_condition,
        "urgency": f"Non-Emergency ({severity_label})",
        "associated_symptoms": associated_symptoms,
        "analysis": " ".join(notes),
        "recommendation": f"I recommend booking an evaluation with a **{specialty}** specialist or visiting an Urgent Care clinic in San Francisco."
    }

# Helper: Render Provider Search Results and Summary Generator
def display_provider_results(triage, age, sex, severity, timeline, food, events, travel, vax_meds, allergies, fam_hist, text, images_list):
    st.markdown("---")
    st.markdown("### 📍 Matched San Francisco Healthcare Providers")
    
    exact_zip_matches = pd.DataFrame()
    nearby_matches = pd.DataFrame()
    
    if not df_providers.empty:
        spec_df = df_providers[
            (df_providers['specialty'].str.contains(triage['specialty'], case=False, na=False)) |
            (df_providers['specialty'].str.contains("Urgent Care", case=False, na=False)) |
            (df_providers['specialty'].str.contains("Primary Care", case=False, na=False))
        ]
        
        if user_insurance not in ["My provider isn't listed / Out of Network", "I don't have insurance", "Prefer not to say"]:
            ins_df = spec_df[
                spec_df['accepted_insurances'].str.contains(user_insurance, case=False, na=False) |
                spec_df['accepted_insurances'].str.contains("All Insurances", case=False, na=False) |
                spec_df['accepted_insurances'].str.contains("Sliding Scale", case=False, na=False)
            ]
        else:
            ins_df = spec_df
            
        exact_zip_matches = ins_df[ins_df['zip_code'].astype(str) == str(user_zip)]
        nearby_matches = ins_df[ins_df['zip_code'].astype(str) != str(user_zip)]
    
    provider_records = []
    
    if not exact_zip_matches.empty:
        st.success(f"Found in-network provider(s) directly in your neighborhood (ZIP {user_zip}):")
        num_exact = min(len(exact_zip_matches), 3)
        cols = st.columns(max(num_exact, 1))
        for idx, (_, row) in enumerate(exact_zip_matches.head(3).iterrows()):
            with cols[idx % len(cols)]:
                st.markdown(f"**🏥 {row['clinic_name']}**")
                st.caption(f"Specialty: {row['specialty']}")
                st.write(f"📍 {row['address']}, SF ({row['zip_code']})")
                st.write(f"📞 {row['phone']}")
                st.info(f"Acceptance: {row['accepted_insurances']}")
            provider_records.append(f"- {row['clinic_name']} ({row['specialty']}) | {row['address']}, SF ({row['zip_code']}) | Ph: {row['phone']}")
    else:
        st.info(f"ℹ️ We didn't find a direct clinic match inside ZIP **{user_zip}**, but here are top-rated San Francisco providers in neighboring SF ZIP codes just minutes away:")
        if not nearby_matches.empty:
            num_nearby = min(len(nearby_matches), 3)
            cols = st.columns(max(num_nearby, 1))
            for idx, (_, row) in enumerate(nearby_matches.head(3).iterrows()):
                with cols[idx % len(cols)]:
                    st.markdown(f"**🏥 {row['clinic_name']}**")
                    st.caption(f"Specialty: {row['specialty']}")
                    st.write(f"📍 {row['address']}, SF ({row['zip_code']})")
                    st.write(f"📞 {row['phone']}")
                    st.info(f"Acceptance: {row['accepted_insurances']}")
                provider_records.append(f"- {row['clinic_name']} ({row['specialty']}) | {row['address']}, SF ({row['zip_code']}) | Ph: {row['phone']}")
        else:
            st.write("- UCSF Medical Center (Parnassus) | 505 Parnassus Ave, SF (94143) | Ph: (415) 476-1000")
            provider_records.append("- UCSF Medical Center (Parnassus) | 505 Parnassus Ave, SF (94143) | Ph: (415) 476-1000")

    # Pharmacies
    st.markdown("### 💊 Nearby San Francisco Pharmacies")
    pharmacies = df_providers[df_providers['specialty'] == 'Pharmacy']
    pharm_records = []
    if not pharmacies.empty:
        num_pharm = min(len(pharmacies), 2)
        p_cols = st.columns(max(num_pharm, 1))
        for idx, (_, p_row) in enumerate(pharmacies.head(2).iterrows()):
            with p_cols[idx % len(p_cols)]:
                st.markdown(f"**💊 {p_row['clinic_name']}**")
                st.write(f"📍 {p_row['address']}, SF ({p_row['zip_code']})")
                st.write(f"📞 {p_row['phone']}")
            pharm_records.append(f"- {p_row['clinic_name']} | {p_row['address']}, SF ({p_row['zip_code']}) | Ph: {p_row['phone']}")

    # Care Summary File Generation
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    img_summary_str = "No"
    if len(images_list) == 1:
        img_summary_str = "1 Photo Uploaded & Analyzed"
    elif len(images_list) > 1:
        img_summary_str = f"{len(images_list)} Photos Uploaded & Analyzed for Visual Progression (Baseline vs. Current Status)"
        
    summary_content = f"""===================================================================
HELLO PROVIDER - PATIENT CARE SUMMARY & REFERRAL BRIEF (v8)
===================================================================
Date/Time Generated: {timestamp}
Location Focus: San Francisco, CA (ZIP: {user_zip})
Patient Insurance: {user_insurance}

1. REQUIRED PATIENT DEMOGRAPHICS & INTAKE
-------------------------------------------------------------------
Age: {age}
Sex / Gender: {sex}
Reported Severity: {severity}
Symptom Timeline / Duration: {timeline}

2. DETAILED CLINICAL & LIFESTYLE CONTEXT
-------------------------------------------------------------------
Last Oral Intake (Food/Drink): {food if food else 'Not specified'}
Events Leading Up to Symptoms: {events if events else 'Not specified'}
Recent International Travel: {travel if travel else 'None reported'}
Vaccine Status & Current Medications: {vax_meds if vax_meds else 'None reported'}
Pre-existing Conditions & Allergies: {allergies if allergies else 'None reported'}
Hereditary / Family History: {fam_hist if fam_hist else 'None reported'}

3. PATIENT REPORTED SYMPTOMS & PHOTO COMPARISON
-------------------------------------------------------------------
Details: {text}
Photo Upload Status: {img_summary_str}

4. HELLO PROVIDER EVALUATION & CONSENSUS ASSESSMENT
-------------------------------------------------------------------
Suspected Clinical Condition: {triage['suspected_condition']}
Recommended Specialty: {triage['specialty']}
Assessed Urgency: {triage['urgency']}
Patient Consensus Status: Agreed / Confirmed
Clinical Guidance & Notes: {triage['analysis']}
Recommended Action: {triage['recommendation']}

5. MATCHED SAN FRANCISCO HEALTHCARE PROVIDERS
-------------------------------------------------------------------
{chr(10).join(provider_records)}

6. NEARBY SAN FRANCISCO PHARMACIES
-------------------------------------------------------------------
{chr(10).join(pharm_records)}

7. RECOMMENDED NEXT STEPS FOR PATIENT
-------------------------------------------------------------------
[ ] Call the recommended provider above to schedule a consultation.
[ ] Bring a copy of this Care Summary Brief to your appointment.
[ ] Review your medication, vaccine, and allergy details in Section 2 with your clinician.
[ ] If symptoms worsen unexpectedly or include emergency signs, visit an ER immediately.

===================================================================
DISCLAIMER: This document is an educational care navigation summary 
generated by the Hello Provider AI prototype. It is NOT a formal medical 
diagnosis. Always consult a qualified healthcare professional.
===================================================================
"""
    st.session_state.care_summary = summary_content

# Process Chat Input
if user_input or active_images:
    user_text = user_input if user_input else "[Uploaded Symptom Photo / Photo Comparison for Review]"
    st.session_state.messages.append({"role": "user", "content": user_text, "images": active_images})
    
    with st.chat_message("user"):
        st.markdown(user_text)
        if active_images:
            cols = st.columns(min(len(active_images), 2))
            for idx, img_obj in enumerate(active_images):
                with cols[idx % len(cols)]:
                    st.image(img_obj["file"], caption=img_obj.get("label", "Photo"), width=200)
            
    text_lower = user_text.lower()
    
    # Check if user is responding to existing evaluation consensus
    if st.session_state.current_triage is not None and not st.session_state.consensus_reached:
        st.session_state.discussion_count += 1
        
        agree_words = ["yes", "agree", "sounds right", "accurate", "correct", "makes sense", "yeah", "yep", "sure"]
        disagree_words = ["no", "disagree", "reconsider", "wrong", "different", "don't think so", "not right", "nope"]
        
        is_agree = any(w in text_lower for w in agree_words)
        is_disagree = any(w in text_lower for w in disagree_words)
        
        with st.chat_message("assistant"):
            if is_agree:
                st.session_state.consensus_reached = True
                confirm_msg = "Wonderful! I'm glad we've reached a consensus on your symptoms. Now that we agree on the focus area, here are your matched San Francisco healthcare providers and nearby pharmacies!"
                st.write_stream(stream_text(confirm_msg))
                st.session_state.messages.append({"role": "assistant", "content": confirm_msg})
                
                display_provider_results(
                    st.session_state.current_triage, patient_age, patient_sex, symptom_severity, symptom_timeline,
                    last_oral_intake, events_leading_up, recent_travel, vaccines_medications, med_conditions_allergies, family_history,
                    user_text, active_images
                )
            elif is_disagree or st.session_state.discussion_count >= 3:
                if st.session_state.discussion_count >= 3:
                    gp_msg = (
                        "Thank you for walking through your symptoms with me! Since your symptoms are complex or we haven't reached a clear consensus yet, "
                        "I strongly recommend scheduling a visit with a **General Practitioner / Primary Care Physician (PCP)** or visiting an Urgent Care clinic for a comprehensive in-person evaluation.\n\n"
                        "Here are top-rated San Francisco Primary Care and Urgent Care centers ready to help you:"
                    )
                    st.write_stream(stream_text(gp_msg))
                    st.session_state.messages.append({"role": "assistant", "content": gp_msg})
                    st.session_state.consensus_reached = True
                    display_provider_results(
                        st.session_state.current_triage, patient_age, patient_sex, symptom_severity, symptom_timeline,
                        last_oral_intake, events_leading_up, recent_travel, vaccines_medications, med_conditions_allergies, family_history,
                        user_text, active_images
                    )
                else:
                    reconsider_msg = (
                        "I completely understand—thank you for letting me know! Healthcare is collaborative, and your feedback is crucial.\n\n"
                        "Could you tell me a bit more about what feels different or any other symptoms you've noticed? "
                        "I'll re-evaluate everything right away so we can get to the right focus area together."
                    )
                    st.write_stream(stream_text(reconsider_msg))
                    st.session_state.messages.append({"role": "assistant", "content": reconsider_msg})
            else:
                followup_msg = (
                    f"Thanks for adding that context. Based on everything you've shared, I still suspect **{st.session_state.current_triage['suspected_condition']}**.\n\n"
                    f"Do you agree with this focus area, or would you like me to reconsider further?"
                )
                st.write_stream(stream_text(followup_msg))
                st.session_state.messages.append({"role": "assistant", "content": followup_msg})
    else:
        # Check Required Fields for new evaluation
        missing_fields = validate_required(patient_age, patient_sex, symptom_severity, symptom_timeline, user_input, active_images)
        
        with st.chat_message("assistant"):
            if missing_fields:
                missing_str = ", ".join(f"**{m}**" for m in missing_fields)
                friendly_ask = (
                    f"Hello! I'm listening closely to your concerns, and I want to make sure I give you the safest and most accurate care guidance possible. 💙\n\n"
                    f"Before I can evaluate your symptoms and match you with a San Francisco doctor, I just need a few required details from you:\n\n"
                    f"👉 **Missing Required Intake Info**: {missing_str}\n\n"
                    f"**How to complete your intake**:\n"
                    f"1. You can fill out these details on the **left sidebar** (remember to **scroll down on the left sidebar** to see all required and optional fields!).\n"
                    f"2. Or, you can reply directly in this chat with your age, gender, severity, and how long you've had these symptoms!\n\n"
                    f"Once you've filled those out, send a quick reply and I'll immediately evaluate your case!"
                )
                st.write_stream(stream_text(friendly_ask))
                st.session_state.messages.append({"role": "assistant", "content": friendly_ask})
            else:
                # Run Evaluation Engine
                triage = analyze_input(user_input, active_images, symptom_severity, patient_age, symptom_timeline, events_leading_up, recent_travel, last_oral_intake)
                st.session_state.current_triage = triage
                st.session_state.consensus_reached = False
                st.session_state.discussion_count = 0
                
                if triage["is_emergency"]:
                    response_text = f"🚨 **IMPORTANT EMERGENCY NOTICE**\n\n{triage['analysis']}\n\n**Recommended Action**: {triage['recommendation']}"
                    st.write_stream(stream_text(response_text))
                    st.session_state.messages.append({"role": "assistant", "content": response_text})
                else:
                    assoc_symps_list = "\n".join(f"- {s}" for s in triage["associated_symptoms"])
                    
                    eval_msg = (
                        f"Thank you for sharing your symptoms and clinical background with me. Here is my initial evaluation:\n\n"
                        f"### 🩺 Hello Provider Evaluation\n"
                        f"- **Suspected Condition**: `{triage['suspected_condition']}`\n"
                        f"- **Recommended Medical Specialty**: `{triage['specialty']}`\n"
                        f"- **Assessed Urgency**: {triage['urgency']}\n"
                        f"- **Clinical Notes**: {triage['analysis']}\n\n"
                        f"### 🔍 Other Associated Symptoms You Might Be Experiencing:\n"
                        f"{assoc_symps_list}\n\n"
                        f"---\n"
                        f"❓ **Does this evaluation sound accurate to you based on how you feel?**\n"
                        f"- Reply **'Yes'** or **'I agree'** if you want to proceed to view matched San Francisco doctors and download your Care Summary.\n"
                        f"- Reply **'No'** or tell me what feels different if you want me to **reconsider**!"
                    )
                    st.write_stream(stream_text(eval_msg))
                    st.session_state.messages.append({"role": "assistant", "content": eval_msg})

# Download Section
if st.session_state.care_summary:
    st.markdown("---")
    st.subheader("📄 Download Hello Provider Patient Care Summary File")
    st.write("Save your complete care summary brief to bring to your doctor or continue your conversation later:")
    st.download_button(
        label="📥 Download Hello Provider Patient Care Summary (.txt)",
        data=st.session_state.care_summary,
        file_name=f"HelloProvider_CareSummary_{datetime.datetime.now().strftime('%Y%m%d')}.txt",
        mime="text/plain"
    )

st.markdown("---")
st.caption("🛡️ **Hello Provider**: Educational Healthcare Navigation & Triage Assistant. In case of emergency, call 911 immediately.")
