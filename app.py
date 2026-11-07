import streamlit as st
import pandas as pd
import os
import datetime
from PIL import Image
import io

# Page Config
st.set_page_config(
    page_title="SF AI Care Navigator & Triage",
    page_icon="🌉",
    layout="wide"
)

# Title and Header
st.title("🌉 San Francisco AI Care Navigator & Triage")
st.caption("AI-Powered Symptom & Image Analysis • San Francisco In-Network Provider Matching • Patient Referral Brief Generator")

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

# Sidebar Setup
st.sidebar.header("📍 Patient Location & Insurance")
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

selected_zip_label = st.sidebar.selectbox("Select San Francisco Neighborhood / ZIP", list(sf_zips.keys()))
user_zip = sf_zips[selected_zip_label]

insurance_list = [
    "Blue Cross Blue Shield",
    "Aetna",
    "Cigna",
    "Medicaid",
    "Medicare",
    "UnitedHealthcare",
    "Kaiser Permanente",
    "Sliding Scale / Uninsured"
]
user_insurance = st.sidebar.selectbox("Select Insurance Provider", insurance_list)

st.sidebar.markdown("---")
st.sidebar.info("ℹ️ **San Francisco Care Network**: Search includes UCSF Health, Sutter Health CPMC, Kaiser Permanente SF, Zuckerberg SF General, and local SF pharmacies.")

# Initialize Session State for Chat & Patient Summary
if "messages" not in st.session_state:
    st.session_state.messages = [
        {"role": "assistant", "content": "Welcome! I can help triage your symptoms, analyze image uploads (e.g. rashes, eye redness), and connect you with in-network specialists and pharmacies in San Francisco. What symptoms are you experiencing today?"}
    ]

if "care_summary" not in st.session_state:
    st.session_state.care_summary = None

# Display Chat History
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])
        if "image" in msg and msg["image"] is not None:
            st.image(msg["image"], width=250)

# Symptom & Image Input Section
st.subheader("📷 Add Symptom Image (Optional)")
uploaded_image = st.file_uploader("Upload an image of your symptom (e.g., skin rash, swelling, eye irritation)", type=["png", "jpg", "jpeg"])

if uploaded_image:
    st.image(uploaded_image, caption="Uploaded Symptom Image Preview", width=250)

# Chat Input
user_input = st.chat_input("Describe your symptoms here (e.g., 'red rash on arm for 2 days', 'sharp knee pain')...")

# Triage & Processing Logic
def analyze_input(text, img):
    text_lower = text.lower() if text else ""
    
    # 1. Emergency Detection
    emergency_keywords = ["chest pain", "cannot breathe", "shortness of breath", "stroke", "severe bleeding", "unconscious", "fainted", "seizure", "head trauma"]
    for kw in emergency_keywords:
        if kw in text_lower:
            return {
                "is_emergency": True,
                "specialty": "Emergency Care",
                "urgency": "CRITICAL EMERGENCY",
                "analysis": f"CRITICAL: Symptoms mention '{kw}'. Immediate medical evaluation required.",
                "recommendation": "Go directly to the nearest San Francisco Emergency Room (e.g., Zuckerberg SF General at 1001 Potrero Ave or Saint Francis ER at 900 Hyde St) or call 911."
            }
    
    # 2. Image + Text Specialty Determination
    specialty = "Primary Care"
    analysis_notes = []
    
    if img is not None:
        analysis_notes.append("📷 Image Analyzed: Visual assessment indicates localized superficial tissue/dermatological presentation.")
        specialty = "Dermatology"
        
    if "rash" in text_lower or "skin" in text_lower or "itch" in text_lower or "mole" in text_lower or "eczema" in text_lower or "burn" in text_lower:
        specialty = "Dermatology"
        analysis_notes.append("Keywords suggest a skin or dermatological condition.")
    elif "chest" in text_lower or "heart" in text_lower or "palpitation" in text_lower or "blood pressure" in text_lower:
        specialty = "Cardiology"
        analysis_notes.append("Keywords suggest a cardiovascular focus.")
    elif "joint" in text_lower or "bone" in text_lower or "knee" in text_lower or "ankle" in text_lower or "sprain" in text_lower or "fracture" in text_lower:
        specialty = "Orthopedics"
        analysis_notes.append("Keywords suggest a musculoskeletal or orthopedic issue.")
    elif "headache" in text_lower or "dizzy" in text_lower or "numb" in text_lower or "seizure" in text_lower or "migraine" in text_lower:
        specialty = "Neurology"
        analysis_notes.append("Keywords suggest a neurological complaint.")
    elif "stomach" in text_lower or "nausea" in text_lower or "acid" in text_lower or "abdomen" in text_lower or "digest" in text_lower:
        specialty = "Gastroenterology"
        analysis_notes.append("Keywords suggest a gastrointestinal issue.")
    elif "eye" in text_lower or "vision" in text_lower or "red eye" in text_lower or "cornea" in text_lower:
        specialty = "Ophthalmology"
        analysis_notes.append("Keywords suggest an ocular/eye presentation.")
    elif "child" in text_lower or "baby" in text_lower or "infant" in text_lower or "pediatric" in text_lower:
        specialty = "Pediatrics"
        analysis_notes.append("Keywords suggest a pediatric consultation.")
    elif "fever" in text_lower or "cough" in text_lower or "flu" in text_lower or "urgent" in text_lower or "sore throat" in text_lower:
        specialty = "Urgent Care"
        analysis_notes.append("Keywords suggest an acute minor illness appropriate for Urgent Care.")
        
    full_analysis = " ".join(analysis_notes) if analysis_notes else "General health inquiry evaluated."
    
    return {
        "is_emergency": False,
        "specialty": specialty,
        "urgency": "Moderate / Non-Emergency",
        "analysis": full_analysis,
        "recommendation": f"Consult a **{specialty}** specialist or visit an Urgent Care clinic for a thorough evaluation."
    }

if user_input or uploaded_image:
    user_text = user_input if user_input else "[Uploaded Symptom Image for Analysis]"
    st.session_state.messages.append({"role": "user", "content": user_text, "image": uploaded_image})
    
    with st.chat_message("user"):
        st.markdown(user_text)
        if uploaded_image:
            st.image(uploaded_image, width=250)
            
    # Run Triage
    triage = analyze_input(user_input, uploaded_image)
    
    with st.chat_message("assistant"):
        if triage["is_emergency"]:
            response_text = f"🚨 **EMERGENCY WARNING**\n\n{triage['analysis']}\n\n**Action Required**: {triage['recommendation']}"
            st.error(response_text)
        else:
            response_text = f"### 🩺 Triage Assessment Summary\n" \
                            f"- **Recommended Medical Specialty**: `{triage['specialty']}`\n" \
                            f"- **Assessed Urgency**: {triage['urgency']}\n" \
                            f"- **Analysis**: {triage['analysis']}\n\n" \
                            f"**Next Step**: {triage['recommendation']}"
            st.markdown(response_text)
            
            # Find SF Providers
            st.markdown(f"--- \n### 📍 Matching In-Network Providers in San Francisco")
            
            filtered = pd.DataFrame()
            if not df_providers.empty:
                # Match Specialty or Urgent Care / Primary Care
                spec_matches = df_providers[
                    (df_providers['specialty'].str.contains(triage['specialty'], case=False, na=False)) |
                    (df_providers['specialty'].str.contains("Urgent Care", case=False, na=False)) |
                    (df_providers['specialty'].str.contains("Primary Care", case=False, na=False))
                ]
                
                # Match Insurance
                ins_matches = spec_matches[spec_matches['accepted_insurances'].str.contains(user_insurance, case=False, na=False) | spec_matches['accepted_insurances'].str.contains("All Insurances", case=False, na=False) | spec_matches['accepted_insurances'].str.contains("Sliding Scale", case=False, na=False)]
                
                filtered = ins_matches if not ins_matches.empty else spec_matches
            
            if not filtered.empty:
                cols = st.columns(min(len(filtered), 3))
                provider_records = []
                for idx, row in filtered.head(3).iterrows():
                    with cols[idx % 3]:
                        st.markdown(f"**🏥 {row['clinic_name']}**")
                        st.caption(f"Specialty: {row['specialty']}")
                        st.write(f"📍 {row['address']}, SF ({row['zip_code']})")
                        st.write(f"📞 {row['phone']}")
                        st.success(f"Accepts: {user_insurance}")
                    provider_records.append(f"- {row['clinic_name']} ({row['specialty']}) | {row['address']}, SF ({row['zip_code']}) | Ph: {row['phone']}")
            else:
                st.info("No direct match found in database for exact filters; displaying general SF medical centers.")
                provider_records = ["- UCSF Medical Center (Parnassus) | 505 Parnassus Ave, SF (94143) | Ph: (415) 476-1000"]

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

            # Generate Patient Care Summary Document
            timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            summary_content = f"""===================================================================
SAN FRANCISCO PATIENT CARE SUMMARY & REFERRAL BRIEF
===================================================================
Date/Time Generated: {timestamp}
Location Focus: San Francisco, CA (ZIP: {user_zip})
Patient Insurance: {user_insurance}

1. PATIENT REPORTED SYMPTOMS
-------------------------------------------------------------------
Details: {user_text}
Image Uploaded: {'Yes (Analyzed)' if uploaded_image else 'No'}

2. AI TRIAGE & CLINICAL ASSESSMENT
-------------------------------------------------------------------
Recommended Specialty: {triage['specialty']}
Assessed Urgency: {triage['urgency']}
Analysis Notes: {triage['analysis']}
Recommended Action: {triage['recommendation']}

3. MATCHED SAN FRANCISCO IN-NETWORK PROVIDERS
-------------------------------------------------------------------
{chr(10).join(provider_records)}

4. NEARBY SAN FRANCISCO PHARMACIES
-------------------------------------------------------------------
{chr(10).join(pharm_records)}

5. RECOMMENDED NEXT STEPS FOR PATIENT
-------------------------------------------------------------------
[ ] Call the recommended provider above to schedule a consultation.
[ ] Bring a copy of this Care Summary Brief to your appointment.
[ ] Prepare a list of current medications and allergies.
[ ] If symptoms worsen unexpectedly or include emergency signs, visit an ER immediately.

===================================================================
DISCLAIMER: This document is an educational care navigation summary 
generated by an AI prototype. It is NOT a formal medical diagnosis. 
Always consult a qualified healthcare professional.
===================================================================
"""
            st.session_state.care_summary = summary_content
            
    st.session_state.messages.append({"role": "assistant", "content": response_text})

# Patient Summary Download Section
if st.session_state.care_summary:
    st.markdown("---")
    st.subheader("📄 Patient Referral Brief & Care Summary File")
    st.write("Click below to download your complete patient summary to bring to your doctor's appointment:")
    st.download_button(
        label="📥 Download Patient Care Summary (.txt)",
        data=st.session_state.care_summary,
        file_name=f"SF_Patient_Care_Summary_{datetime.datetime.now().strftime('%Y%m%d')}.txt",
        mime="text/plain"
    )

st.markdown("---")
st.caption("🛡️ **Disclaimer**: Educational Care Navigation & Triage Prototype. In case of medical emergency, call 911 immediately.")
