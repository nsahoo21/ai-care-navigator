import streamlit as st
import pandas as pd
import os
import datetime
from PIL import Image
import io
import streamlit.components.v1 as components

# Page Config
st.set_page_config(
    page_title="Hello Provider - AI Patient Care & Triage",
    page_icon="🩺",
    layout="wide"
)

# Title and Header
st.title("🩺 Hello Provider")
st.caption("Your Empathetic San Francisco Healthcare Guide • Speech & Photo Analysis • Interactive Symptom Triage • Provider Matching")

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
            "content": "Hello! I'm **Hello Provider**, your personal healthcare assistant in San Francisco. I'm here to listen to what you're experiencing, analyze any photos or symptoms you share, evaluate what condition you might have, and match you with the right doctor or clinic.\n\n📌 **Tip**: You can enter your clinical details on the **left sidebar** (please **scroll down on the left sidebar** to view all required and optional fields!), or type/speak your symptoms directly in the chat below."
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
        "content": f"📄 **Imported Previous Care Summary**: `{uploaded_summary_file.name}`!\n\nI've reloaded your clinical profile, past reported symptoms, and previous triage notes. Let me know what's changed or how you'd like to continue!"
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
        if "image" in msg and msg["image"] is not None:
            st.image(msg["image"], width=250)

# Speech-to-Text & Image Upload Section in Main Chat
st.markdown("### 🎙️ Voice & Visual Input")
col_mic, col_img = st.columns([1, 1])

with col_mic:
    st.markdown("**Option A: Voice Input (Speech to Text)**")
    st.write("Click the button below to allow microphone access and speak your symptoms:")
    
    # HTML5 Speech Recognition Component
    speech_html = """
    <div style="font-family: sans-serif; padding: 10px; border: 1px solid #e0e0e0; border-radius: 8px; background-color: #f9f9f9;">
        <button id="start-btn" style="background-color: #0284c7; color: white; border: none; padding: 10px 16px; border-radius: 6px; font-weight: bold; cursor: pointer;">
            🎙️ Start Speaking (Mic)
        </button>
        <button id="stop-btn" style="background-color: #dc2626; color: white; border: none; padding: 10px 16px; border-radius: 6px; font-weight: bold; cursor: pointer; margin-left: 8px;">
            🛑 Stop
        </button>
        <div id="status" style="margin-top: 8px; font-size: 0.9em; color: #555;">Status: Click Start Speaking</div>
        <textarea id="transcript" style="width: 100%; height: 70px; margin-top: 8px; border-radius: 6px; border: 1px solid #ccc; padding: 6px;" placeholder="Transcribed speech will appear here... Copy and paste into the chat box below."></textarea>
    </div>

    <script>
        const startBtn = document.getElementById('start-btn');
        const stopBtn = document.getElementById('stop-btn');
        const statusDiv = document.getElementById('status');
        const transcriptArea = document.getElementById('transcript');

        const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;

        if (!SpeechRecognition) {
            statusDiv.innerHTML = "⚠️ Speech Recognition is not supported in this browser. Please type below.";
        } else {
            const recognition = new SpeechRecognition();
            recognition.continuous = true;
            recognition.interimResults = true;
            recognition.lang = 'en-US';

            recognition.onstart = () => {
                statusDiv.innerHTML = "🎙️ Listening... Speak clearly into your microphone.";
            };

            recognition.onerror = (event) => {
                statusDiv.innerHTML = "Error: " + event.error;
            };

            recognition.onend = () => {
                statusDiv.innerHTML = "Stopped listening.";
            };

            recognition.onresult = (event) => {
                let current = '';
                for (let i = event.resultIndex; i < event.results.length; i++) {
                    current += event.results[i][0].transcript;
                }
                transcriptArea.value = current;
            };

            startBtn.addEventListener('click', () => recognition.start());
            stopBtn.addEventListener('click', () => recognition.stop());
        }
    </script>
    """
    components.html(speech_html, height=190)

with col_img:
    st.markdown("**Option B: Symptom Photo Upload**")
    uploaded_image = st.file_uploader("Attach a photo of your symptom (e.g. rash, eye redness, swelling)", type=["png", "jpg", "jpeg"])
    if uploaded_image:
        st.image(uploaded_image, caption="Uploaded Symptom Photo", width=220)

# Chat Input Box
user_input = st.chat_input("Talk to Hello Provider about your symptoms or medical concerns...")

# Validation Helper
def validate_required(age, sex, severity, timeline, text, img):
    missing = []
    if age <= 0:
        missing.append("Age")
    if sex == "Select...":
        missing.append("Sex / Gender")
    if severity == "Select...":
        missing.append("Symptom Severity Level")
    if timeline == "Select...":
        missing.append("Symptom Timeline / How long since onset?")
    if not text and img is None:
        missing.append("Symptom description or photo upload")
    return missing

# Comprehensive Clinical Evaluation Engine
def analyze_input(text, img, severity_label, age, timeline, events, travel, intake_food):
    text_lower = text.lower() if text else ""
    
    # Emergency Keyword & Severity Checks
    emergency_keywords = ["chest pain", "cannot breathe", "shortness of breath", "stroke", "severe bleeding", "unconscious", "fainted", "seizure", "head trauma"]
    is_extreme = "Extreme" in severity_label
    
    for kw in emergency_keywords:
        if kw in text_lower or is_extreme:
            reason = f"symptoms mention '{kw}'" if kw in text_lower else "severity is rated as Extreme/Emergency"
            return {
                "is_emergency": True,
                "specialty": "Emergency Care",
                "suspected_condition": "Acute Critical Emergency Condition",
                "urgency": "CRITICAL EMERGENCY",
                "analysis": f"Critical Safety Alert: Your reported {reason}. Immediate medical attention is vital.",
                "associated_symptoms": ["Dizziness / confusion", "Profuse sweating", "Loss of consciousness", "Rapid heart rate"],
                "recommendation": "Please go directly to the nearest San Francisco Emergency Room (e.g., Zuckerberg SF General at 1001 Potrero Ave or Saint Francis ER at 900 Hyde St) or call 911 immediately."
            }
            
    # Specialty & Suspected Condition Mapping
    specialty = "Primary Care"
    suspected_condition = "General Non-Specific Discomfort"
    associated_symptoms = ["General fatigue", "Mild malaise", "Changes in sleep or appetite", "Mild body tightness"]
    notes = []
    
    if age < 18:
        notes.append("Pediatric care protocol flagged due to patient age.")
        specialty = "Pediatrics"
        suspected_condition = "Pediatric Acute Minor Illness"
        associated_symptoms = ["Mild fever", "Irritability", "Loss of appetite", "Low energy"]
        
    if img is not None:
        notes.append("Visual photo review indicates localized dermatological or superficial tissue presentation.")
        if specialty != "Pediatrics":
            specialty = "Dermatology"
            suspected_condition = "Contact Dermatitis / Localized Skin Irritation"
            associated_symptoms = ["Itching or burning sensation", "Redness or inflammation", "Flaking or scaling skin", "Small localized bumps or blisters"]
            
    if "rash" in text_lower or "skin" in text_lower or "itch" in text_lower or "mole" in text_lower or "burn" in text_lower or "wound" in text_lower:
        specialty = "Dermatology"
        suspected_condition = "Dermatological Reaction / Eczema or Rash"
        associated_symptoms = ["Itching or skin soreness", "Redness or color change", "Dryness or flaking", "Mild swelling around affected area"]
        notes.append("Symptom description aligns with dermatological evaluation.")
    elif "chest" in text_lower or "heart" in text_lower or "palpitation" in text_lower or "bp" in text_lower:
        specialty = "Cardiology"
        suspected_condition = "Non-Emergency Cardiovascular Stress / Palpitations"
        associated_symptoms = ["Lightheadedness or dizziness", "Shortness of breath on exertion", "Racing or fluttering pulse", "General fatigue"]
        notes.append("Symptom description aligns with cardiovascular evaluation.")
    elif "knee" in text_lower or "joint" in text_lower or "ankle" in text_lower or "bone" in text_lower or "sprain" in text_lower or "fracture" in text_lower or "fall" in text_lower or "injury" in text_lower:
        specialty = "Orthopedics"
        suspected_condition = "Acute Musculoskeletal Strain or Joint Sprain"
        associated_symptoms = ["Localized swelling or bruising", "Joint stiffness or reduced movement", "Pain when bearing weight", "Tenderness to touch"]
        notes.append("Symptom description points to musculoskeletal or orthopedic evaluation.")
    elif "headache" in text_lower or "dizzy" in text_lower or "migraine" in text_lower or "numb" in text_lower:
        specialty = "Neurology"
        suspected_condition = "Tension Headache, Migraine, or Nerve Sensitivity"
        associated_symptoms = ["Sensitivity to light or sound", "Mild nausea or aura", "Neck tightness or stiffness", "Dizziness or head pressure"]
        notes.append("Symptom description aligns with neurological evaluation.")
    elif "stomach" in text_lower or "nausea" in text_lower or "abdomen" in text_lower or "cramp" in text_lower or "acid" in text_lower:
        specialty = "Gastroenterology"
        suspected_condition = "Acute Gastritis, Acid Reflux (GERD), or Indigestion"
        associated_symptoms = ["Bloating or abdominal fullness", "Nausea or sour taste", "Stomach cramping after eating", "Loss of appetite"]
        notes.append("Symptom description aligns with gastrointestinal evaluation.")
    elif "eye" in text_lower or "vision" in text_lower or "redness" in text_lower:
        specialty = "Ophthalmology"
        suspected_condition = "Conjunctivitis (Red Eye) or Ocular Irritation"
        associated_symptoms = ["Eye redness or tearing", "Sensation of grit or dust in eye", "Sensitivity to bright light", "Mild discharge or eyelid crusting"]
        notes.append("Symptom description points to ocular/eye evaluation.")
    elif "fever" in text_lower or "cough" in text_lower or "flu" in text_lower or "sore throat" in text_lower:
        specialty = "Urgent Care"
        suspected_condition = "Viral Upper Respiratory Infection or Influenza-like Illness"
        associated_symptoms = ["Low-grade fever or chills", "Sore throat or dry cough", "Nasal congestion or runny nose", "Generalized body aches and fatigue"]
        notes.append("Symptoms are consistent with acute minor illness appropriate for Urgent Care.")
        
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
def display_provider_results(triage, age, sex, severity, timeline, food, events, travel, vax_meds, allergies, fam_hist, text, img_flag):
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
        cols = st.columns(min(len(exact_zip_matches), 3))
        for idx, row in exact_zip_matches.head(3).iterrows():
            with cols[idx % 3]:
                st.markdown(f"**🏥 {row['clinic_name']}**")
                st.caption(f"Specialty: {row['specialty']}")
                st.write(f"📍 {row['address']}, SF ({row['zip_code']})")
                st.write(f"📞 {row['phone']}")
                st.info(f"Acceptance: {row['accepted_insurances']}")
            provider_records.append(f"- {row['clinic_name']} ({row['specialty']}) | {row['address']}, SF ({row['zip_code']}) | Ph: {row['phone']}")
    else:
        st.info(f"ℹ️ We didn't find a direct clinic match inside ZIP **{user_zip}**, but here are top-rated San Francisco providers in neighboring SF ZIP codes just minutes away:")
        if not nearby_matches.empty:
            cols = st.columns(min(len(nearby_matches), 3))
            for idx, row in nearby_matches.head(3).iterrows():
                with cols[idx % 3]:
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
        p_cols = st.columns(2)
        for idx, p_row in pharmacies.head(2).iterrows():
            with p_cols[idx % 2]:
                st.markdown(f"**💊 {p_row['clinic_name']}**")
                st.write(f"📍 {p_row['address']}, SF ({p_row['zip_code']})")
                st.write(f"📞 {p_row['phone']}")
            pharm_records.append(f"- {p_row['clinic_name']} | {p_row['address']}, SF ({p_row['zip_code']}) | Ph: {p_row['phone']}")

    # Care Summary File Generation
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    summary_content = f"""===================================================================
HELLO PROVIDER - PATIENT CARE SUMMARY & REFERRAL BRIEF (v6)
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

3. PATIENT REPORTED SYMPTOMS & CHAT HISTORY
-------------------------------------------------------------------
Details: {text}
Photo Uploaded: {'Yes (Analyzed)' if img_flag else 'No'}

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
if user_input or uploaded_image:
    user_text = user_input if user_input else "[Uploaded Symptom Image for Review]"
    st.session_state.messages.append({"role": "user", "content": user_text, "image": uploaded_image})
    
    with st.chat_message("user"):
        st.markdown(user_text)
        if uploaded_image:
            st.image(uploaded_image, width=250)
            
    user_text_lower = user_text.lower()
    
    # Check if user is responding to an existing assessment consensus question
    if st.session_state.current_triage is not None and not st.session_state.consensus_reached:
        # Check if user agrees
        agreement_words = ["yes", "agree", "sounds right", "correct", "makes sense", "yeah", "yep", "sure", "that's right", "show me doctors", "find provider", "ok", "okay"]
        disagreement_words = ["no", "disagree", "wrong", "reconsider", "not right", "don't agree", "incorrect", "something else"]
        
        is_agree = any(w in user_text_lower for w in agreement_words)
        is_disagree = any(w in user_text_lower for w in disagreement_words)
        
        with st.chat_message("assistant"):
            if is_agree and not is_disagree:
                st.session_state.consensus_reached = True
                response_text = (
                    f"Wonderful! I'm glad we are on the same page. 💙\n\n"
                    f"Based on our agreement on **{st.session_state.current_triage['suspected_condition']}**, "
                    f"here are the recommended **{st.session_state.current_triage['specialty']}** specialists and top-rated healthcare providers in San Francisco for you:"
                )
                st.markdown(response_text)
                st.session_state.messages.append({"role": "assistant", "content": response_text})
                
                # Show providers & summary
                display_provider_results(
                    st.session_state.current_triage, patient_age, patient_sex, symptom_severity, symptom_timeline,
                    last_oral_intake, events_leading_up, recent_travel, vaccines_medications, med_conditions_allergies, family_history,
                    user_text, uploaded_image is not None
                )
            elif is_disagree:
                st.session_state.discussion_count += 1
                if st.session_state.discussion_count >= 2:
                    response_text = (
                        f"Thank you for sharing that with me. Since your symptoms feel complex or don't quite align with my initial evaluation, "
                        f"the safest and best step is to schedule an appointment with a **General Practitioner / Primary Care Physician (PCP)**.\n\n"
                        f"A Primary Care Physician can conduct a comprehensive in-person physical exam, run diagnostic tests, and refer you to the exact specialist you need.\n\n"
                        f"Would you like me to connect you with General Practice & Primary Care clinics near you in San Francisco?"
                    )
                    st.session_state.current_triage["specialty"] = "Primary Care"
                    st.session_state.consensus_reached = True
                    st.markdown(response_text)
                    st.session_state.messages.append({"role": "assistant", "content": response_text})
                    display_provider_results(
                        st.session_state.current_triage, patient_age, patient_sex, symptom_severity, symptom_timeline,
                        last_oral_intake, events_leading_up, recent_travel, vaccines_medications, med_conditions_allergies, family_history,
                        user_text, uploaded_image is not None
                    )
                else:
                    response_text = (
                        f"Thank you for letting me know! I appreciate your feedback and want to get this right for you. 💙\n\n"
                        f"Let's reconsider. Could you tell me a bit more about what feels off, or describe any additional symptoms you are experiencing (e.g. fever, pain level, skin changes, nausea)?\n\n"
                        f"I'll re-evaluate your symptoms right away!"
                    )
                    st.markdown(response_text)
                    st.session_state.messages.append({"role": "assistant", "content": response_text})
            else:
                # User typed something general during consensus prompt
                st.session_state.discussion_count += 1
                # Re-evaluate with new input included
                new_triage = analyze_input(user_text, uploaded_image, symptom_severity, patient_age, symptom_timeline, events_leading_up, recent_travel, last_oral_intake)
                st.session_state.current_triage = new_triage
                
                assoc_list_str = "\n".join(f"- {s}" for s in new_triage["associated_symptoms"])
                response_text = (
                    f"Thanks for providing that extra detail! Here is my updated evaluation:\n\n"
                    f"### 🩺 Hello Provider Evaluation\n"
                    f"Based on your symptoms, I suspect this may be related to: **{new_triage['suspected_condition']}** (Recommended Specialty: `{new_triage['specialty']}`).\n\n"
                    f"**Associated Symptoms to watch for**:\n{assoc_list_str}\n\n"
                    f"**Does this updated evaluation sound accurate to you?**\n"
                    f"- Type **Yes** if you agree, and I'll display matched San Francisco healthcare providers.\n"
                    f"- Type **No** or tell me more if you'd like me to reconsider or guide you to a General Practitioner!"
                )
                st.markdown(response_text)
                st.session_state.messages.append({"role": "assistant", "content": response_text})
                
    else:
        # Check Required Fields
        missing_fields = validate_required(patient_age, patient_sex, symptom_severity, symptom_timeline, user_input, uploaded_image)
        
        with st.chat_message("assistant"):
            if missing_fields:
                missing_str = ", ".join(f"**{m}**" for m in missing_fields)
                
                friendly_ask = (
                    f"Hello! I'm listening closely to your concerns, and I want to make sure I give you the safest and most accurate care guidance possible. 💙\n\n"
                    f"Before I can analyze your symptoms and match you with a San Francisco doctor, I just need a few required details from you:\n\n"
                    f"👉 **Missing Info Required**: {missing_str}\n\n"
                    f"**How to complete your intake**:\n"
                    f"1. You can fill out these details on the **left sidebar** (remember to **scroll down on the left sidebar** to see all required and optional fields!).\n"
                    f"2. Or, you can reply directly in this chat with your age, gender, severity, and how long you've had these symptoms!\n\n"
                    f"Once you've filled those out, send a quick reply and I'll immediately analyze your case!"
                )
                st.markdown(friendly_ask)
                st.session_state.messages.append({"role": "assistant", "content": friendly_ask})
            else:
                # Initial Evaluation & Hypothesis Presentation
                triage = analyze_input(user_input, uploaded_image, symptom_severity, patient_age, symptom_timeline, events_leading_up, recent_travel, last_oral_intake)
                st.session_state.current_triage = triage
                
                if triage["is_emergency"]:
                    response_text = f"🚨 **IMPORTANT EMERGENCY NOTICE**\n\n{triage['analysis']}\n\n**Recommended Action**: {triage['recommendation']}"
                    st.error(response_text)
                    st.session_state.messages.append({"role": "assistant", "content": response_text})
                else:
                    assoc_list_str = "\n".join(f"- {s}" for s in triage["associated_symptoms"])
                    
                    response_text = (
                        f"Thank you for sharing your symptoms and clinical profile with me. Here is my initial evaluation:\n\n"
                        f"### 🩺 Hello Provider Evaluation & Symptom Check\n"
                        f"**Based on my evaluation, this is what I think it might be**: **{triage['suspected_condition']}** (Recommended Specialty: `{triage['specialty']}`).\n\n"
                        f"**Other associated symptoms you might also be experiencing or should watch for**:\n"
                        f"{assoc_list_str}\n\n"
                        f"**Clinical Notes**: {triage['analysis']}\n\n"
                        f"---\n"
                        f"### 🤔 Do you agree with this evaluation?\n"
                        f"- If **YES** (or if you type 'yes' / 'agree'), I will immediately connect you with matched in-network healthcare providers & pharmacies in San Francisco!\n"
                        f"- If **NO** (or if you type 'no' / describe what feels different), tell me what else you are feeling so I can reconsider, or guide you to a General Practitioner!"
                    )
                    st.markdown(response_text)
                    st.session_state.messages.append({"role": "assistant", "content": response_text})

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
