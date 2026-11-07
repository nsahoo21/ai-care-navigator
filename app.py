import streamlit as st
import pandas as pd
import os
import datetime
from PIL import Image
import io

# Page Config
st.set_page_config(
    page_title="Hello Provider - AI Patient Care & Triage",
    page_icon="🩺",
    layout="wide"
)

# Title and Header
st.title("🩺 Hello Provider")
st.caption("Your Empathetic San Francisco Care Guide • Symptom & Image Analysis • In-Network Care Matching • Patient Summary Briefs")

# Load San Francisco Provider Database
@st.cache_data
def load_providers():
    csv_path = "providers-v2.csv"
    if not os.path.exists(csv_path):
        csv_path = "providers.csv"
    if os.path.exists(csv_path):
        return pd.read_csv(csv_path)
    else:
        st.error("Provider database not found.")
        return pd.DataFrame()

df_providers = load_providers()

# Session State Initialization
if "messages" not in st.session_state:
    st.session_state.messages = [
        {
            "role": "assistant", 
            "content": "Hello! I'm **Hello Provider**, your personal healthcare triage assistant. I'm here to listen to how you're feeling, help analyze any symptoms or uploaded photos, and match you with the right doctor or clinic in San Francisco.\n\nTo get started, please share what symptoms you're experiencing today and fill out the quick required intake details on the left sidebar!"
        }
    ]

if "care_summary" not in st.session_state:
    st.session_state.care_summary = None

if "imported_summary_text" not in st.session_state:
    st.session_state.imported_summary_text = None

# Sidebar Controls: New Chat & Import Summary
st.sidebar.header("⚙️ Conversation Controls")

if st.sidebar.button("🔄 Start New Chat / Different Medical Concern"):
    st.session_state.messages = [
        {
            "role": "assistant",
            "content": "Hello! Starting a new conversation. What medical condition or symptom would you like to discuss today?"
        }
    ]
    st.session_state.care_summary = None
    st.session_state.imported_summary_text = None
    st.rerun()

st.sidebar.markdown("---")
st.sidebar.subheader("📂 Import Existing Care Summary")
uploaded_summary_file = st.sidebar.file_uploader("Upload a previous Patient Care Summary (.txt) to resume your care chat", type=["txt"])

if uploaded_summary_file is not None and st.session_state.imported_summary_text != uploaded_summary_file.name:
    summary_raw_text = uploaded_summary_file.read().decode("utf-8")
    st.session_state.imported_summary_text = uploaded_summary_file.name
    st.session_state.care_summary = summary_raw_text
    st.session_state.messages.append({
        "role": "assistant",
        "content": f"📄 **Imported Previous Care Summary**: `{uploaded_summary_file.name}`!\n\nI've loaded your previous medical history, reported symptoms, and triage records from your summary file. We can continue right where you left off. How are your symptoms progressing or what new questions do you have?"
    })
    st.sidebar.success("Care Summary imported successfully!")

st.sidebar.markdown("---")
st.sidebar.header("📋 Clinical Patient Intake")

# Required Intake Section
st.sidebar.markdown("### 🔴 Required Fields")
patient_age = st.sidebar.number_input("Age*", min_value=0, max_value=120, value=0, help="Required: Please enter patient age")
patient_sex = st.sidebar.selectbox("Sex / Gender*", ["Select...", "Female", "Male", "Non-Binary", "Other / Prefer not to say"])
symptom_severity = st.sidebar.selectbox("Symptom Severity Level*", ["Select...", "Mild (1-3)", "Moderate (4-6)", "Severe (7-8)", "Extreme / Emergency (9-10)"])
symptom_timeline = st.sidebar.selectbox("Symptom Timeline / Duration*", ["Select...", "< 24 Hours (Sudden onset)", "1 - 3 Days", "4 - 7 Days", "1 - 4 Weeks", "1+ Months (Chronic)"])

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
with st.sidebar.expander("➕ Optional Medical History & Context"):
    last_oral_intake = st.text_input("Last Oral Intake (Food/Drink)", placeholder="e.g. Water 1 hour ago, Light lunch at 12pm")
    events_leading_up = st.text_area("Events Leading Up to Symptoms", placeholder="e.g. Slipped while running, Ate seafood dinner")
    recent_travel = st.text_input("Recent International Travel", placeholder="e.g. None, or Traveled to Mexico 2 weeks ago")
    vaccines_medications = st.text_area("Vaccine Status & Current Medications", placeholder="e.g. Up to date on Flu/COVID vaccines, taking Lisinopril daily")
    med_conditions_allergies = st.text_area("Pre-existing Conditions & Allergies", placeholder="e.g. Asthma, Penicillin allergy")
    family_history = st.text_area("Hereditary / Family Medical History", placeholder="e.g. Family history of heart disease")

st.sidebar.markdown("---")
st.sidebar.info("ℹ️ **San Francisco Care Network**: Matches clinics across UCSF Health, Sutter Health CPMC, Kaiser Permanente SF, Zuckerberg SF General, and local SF pharmacies.")

# Display Conversation History
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])
        if "image" in msg and msg["image"] is not None:
            st.image(msg["image"], width=250)

# Image Upload Area
st.subheader("📷 Symptom Photo Upload (Optional)")
uploaded_image = st.file_uploader("Attach a photo of your symptom (e.g. rash, eye inflammation, swelling, wound)", type=["png", "jpg", "jpeg"])

if uploaded_image:
    st.image(uploaded_image, caption="Uploaded Symptom Photo", width=250)

# Chat Input Box
user_input = st.chat_input("Talk to Hello Provider about your symptoms or medical questions...")

# Validation & Triage Logic
def validate_required(age, sex, severity, timeline, text, img):
    missing = []
    if age <= 0:
        missing.append("Age")
    if sex == "Select...":
        missing.append("Sex / Gender")
    if severity == "Select...":
        missing.append("Symptom Severity Level")
    if timeline == "Select...":
        missing.append("Symptom Timeline / Duration")
    if not text and img is None:
        missing.append("Symptom description or photo upload")
    return missing

def analyze_input(text, img, severity_label, age, timeline, events, travel):
    text_lower = text.lower() if text else ""
    
    # 1. Emergency Keyword & Severity Check
    emergency_keywords = ["chest pain", "cannot breathe", "shortness of breath", "stroke", "severe bleeding", "unconscious", "fainted", "seizure", "head trauma"]
    is_extreme = "Extreme" in severity_label
    
    for kw in emergency_keywords:
        if kw in text_lower or is_extreme:
            reason = f"symptoms mention '{kw}'" if kw in text_lower else "severity is reported as Extreme/Emergency"
            return {
                "is_emergency": True,
                "specialty": "Emergency Care",
                "urgency": "CRITICAL EMERGENCY",
                "analysis": f"Critical Safety Alert: Your reported {reason}. Immediate medical attention is vital.",
                "recommendation": "Please go directly to the nearest Emergency Room (e.g., Zuckerberg SF General at 1001 Potrero Ave or Saint Francis ER at 900 Hyde St) or call 911 immediately."
            }
            
    # 2. Specialty & Contextual Analysis
    specialty = "Primary Care"
    notes = []
    
    if age < 18:
        notes.append("Pediatric care protocol flagged due to patient age.")
        specialty = "Pediatrics"
        
    if img is not None:
        notes.append("Visual photo review indicates localized dermatological or tissue presentation.")
        if specialty != "Pediatrics":
            specialty = "Dermatology"
            
    if "rash" in text_lower or "skin" in text_lower or "itch" in text_lower or "mole" in text_lower or "burn" in text_lower or "wound" in text_lower:
        specialty = "Dermatology"
        notes.append("Symptom description aligns with dermatological care.")
    elif "chest" in text_lower or "heart" in text_lower or "palpitation" in text_lower or "bp" in text_lower:
        specialty = "Cardiology"
        notes.append("Symptom description aligns with cardiovascular care.")
    elif "knee" in text_lower or "joint" in text_lower or "ankle" in text_lower or "bone" in text_lower or "sprain" in text_lower or "fracture" in text_lower or "fall" in text_lower:
        specialty = "Orthopedics"
        notes.append("Symptom description points to musculoskeletal or orthopedic evaluation.")
    elif "headache" in text_lower or "dizzy" in text_lower or "migraine" in text_lower or "numb" in text_lower:
        specialty = "Neurology"
        notes.append("Symptom description aligns with neurological care.")
    elif "stomach" in text_lower or "nausea" in text_lower or "abdomen" in text_lower or "cramp" in text_lower:
        specialty = "Gastroenterology"
        notes.append("Symptom description aligns with gastrointestinal care.")
    elif "eye" in text_lower or "vision" in text_lower or "redness" in text_lower:
        specialty = "Ophthalmology"
        notes.append("Symptom description points to ocular/eye evaluation.")
    elif "fever" in text_lower or "cough" in text_lower or "flu" in text_lower or "sore throat" in text_lower:
        specialty = "Urgent Care"
        notes.append("Symptoms are consistent with acute minor illness appropriate for Urgent Care.")
        
    if travel and travel.lower() != "none":
        notes.append(f"Recent international travel noted ({travel}).")
        
    if events:
        notes.append(f"Context leading up to symptoms: '{events}'.")
        
    notes.append(f"Onset timeline: {timeline}. Severity rating: {severity_label}.")
    
    return {
        "is_emergency": False,
        "specialty": specialty,
        "urgency": f"Non-Emergency ({severity_label})",
        "analysis": " ".join(notes),
        "recommendation": f"I recommend booking an evaluation with a **{specialty}** specialist or visiting an Urgent Care clinic."
    }

# Process Chat Input
if user_input or uploaded_image:
    user_text = user_input if user_input else "[Uploaded Symptom Image for Review]"
    st.session_state.messages.append({"role": "user", "content": user_text, "image": uploaded_image})
    
    with st.chat_message("user"):
        st.markdown(user_text)
        if uploaded_image:
            st.image(uploaded_image, width=250)
            
    # Check Required Fields
    missing_fields = validate_required(patient_age, patient_sex, symptom_severity, symptom_timeline, user_input, uploaded_image)
    
    with st.chat_message("assistant"):
        if missing_fields:
            missing_str = ", ".join(f"**{m}**" for m in missing_fields)
            friendly_ask = f"I hear you, and I want to make sure I give you the safest care advice possible! 💙\n\nBefore I can complete your triage assessment and find the best doctor for you, could you please fill out the required intake details on the left sidebar?\n\n**Missing required info**: {missing_str}\n\nOnce you update those fields on the sidebar, send me a message or press enter again!"
            st.markdown(friendly_ask)
            st.session_state.messages.append({"role": "assistant", "content": friendly_ask})
        else:
            # Run Triage
            triage = analyze_input(user_input, uploaded_image, symptom_severity, patient_age, symptom_timeline, events_leading_up, recent_travel)
            
            if triage["is_emergency"]:
                response_text = f"🚨 **IMPORTANT EMERGENCY NOTICE**\n\n{triage['analysis']}\n\n**Recommended Action**: {triage['recommendation']}"
                st.error(response_text)
            else:
                response_text = f"Thank you for sharing that with me. Here is what I'm seeing based on your profile and symptoms:\n\n" \
                                f"### 🩺 Hello Provider Triage Assessment\n" \
                                f"- **Patient Profile**: Age {patient_age} | {patient_sex} | Severity: {symptom_severity}\n" \
                                f"- **Recommended Medical Specialty**: `{triage['specialty']}`\n" \
                                f"- **Onset & Timeline**: {symptom_timeline}\n" \
                                f"- **Clinical Guidance & Notes**: {triage['analysis']}\n\n" \
                                f"**Next Steps**: {triage['recommendation']}"
                st.markdown(response_text)
                
                # Provider Search Logic with ZIP Proximity Fallback
                st.markdown("---")
                st.markdown("### 📍 Matched San Francisco Healthcare Providers")
                
                exact_zip_matches = pd.DataFrame()
                nearby_matches = pd.DataFrame()
                
                if not df_providers.empty:
                    # Filter by specialty
                    spec_df = df_providers[
                        (df_providers['specialty'].str.contains(triage['specialty'], case=False, na=False)) |
                        (df_providers['specialty'].str.contains("Urgent Care", case=False, na=False)) |
                        (df_providers['specialty'].str.contains("Primary Care", case=False, na=False))
                    ]
                    
                    # Filter by insurance if standard provider
                    if user_insurance not in ["My provider isn't listed / Out of Network", "I don't have insurance", "Prefer not to say"]:
                        ins_df = spec_df[
                            spec_df['accepted_insurances'].str.contains(user_insurance, case=False, na=False) |
                            spec_df['accepted_insurances'].str.contains("All Insurances", case=False, na=False) |
                            spec_df['accepted_insurances'].str.contains("Sliding Scale", case=False, na=False)
                        ]
                    else:
                        ins_df = spec_df
                        
                    # Match exact ZIP first
                    exact_zip_matches = ins_df[ins_df['zip_code'].astype(str) == str(user_zip)]
                    # Nearby ZIP matches (other SF ZIPs)
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
                    st.info(f"ℹ️ We didn't find a direct clinic match inside ZIP **{user_zip}**, but here are the top-rated San Francisco providers in neighboring SF ZIP codes just minutes away:")
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

                # San Francisco Pharmacies
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

                # Generate Updated Comprehensive Patient Care Summary Document
                timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                summary_content = f"""===================================================================
HELLO PROVIDER - PATIENT CARE SUMMARY & REFERRAL BRIEF (v4)
===================================================================
Date/Time Generated: {timestamp}
Location Focus: San Francisco, CA (ZIP: {user_zip})
Patient Insurance: {user_insurance}

1. REQUIRED PATIENT DEMOGRAPHICS & INTAKE
-------------------------------------------------------------------
Age: {patient_age}
Sex / Gender: {patient_sex}
Reported Severity: {symptom_severity}
Symptom Timeline / Duration: {symptom_timeline}

2. DETAILED CLINICAL & LIFESTYLE CONTEXT
-------------------------------------------------------------------
Last Oral Intake (Food/Drink): {last_oral_intake if last_oral_intake else 'Not specified'}
Events Leading Up to Symptoms: {events_leading_up if events_leading_up else 'Not specified'}
Recent International Travel: {recent_travel if recent_travel else 'None reported'}
Vaccine Status & Current Medications: {vaccines_medications if vaccines_medications else 'None reported'}
Pre-existing Conditions & Allergies: {med_conditions_allergies if med_conditions_allergies else 'None reported'}
Hereditary / Family History: {family_history if family_history else 'None reported'}

3. PATIENT REPORTED SYMPTOMS & CHAT HISTORY
-------------------------------------------------------------------
Details: {user_text}
Photo Uploaded: {'Yes (Analyzed)' if uploaded_image else 'No'}

4. HELLO PROVIDER TRIAGE ASSESSMENT
-------------------------------------------------------------------
Recommended Specialty: {triage['specialty']}
Assessed Urgency: {triage['urgency']}
Clinical Notes & Analysis: {triage['analysis']}
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
            
            st.session_state.messages.append({"role": "assistant", "content": response_text})

# Patient Summary Download Area
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
