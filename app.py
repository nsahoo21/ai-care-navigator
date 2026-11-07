import streamlit as st
import pandas as pd
import re

# Set page configuration
st.set_page_config(
    page_title="AI Patient Care Navigator & Triage",
    page_icon="🩺",
    layout="wide"
)

# Custom CSS for styling cards
st.markdown("""
    <style>
    .emergency-box {
        background-color: #ff4b4b;
        color: white;
        padding: 18px;
        border-radius: 8px;
        font-weight: bold;
        font-size: 1.1rem;
        margin-bottom: 20px;
    }
    .care-card {
        background-color: #f8f9fa;
        border-left: 5px solid #0284c7;
        padding: 15px;
        border-radius: 6px;
        margin-bottom: 12px;
        box-shadow: 0 1px 3px rgba(0,0,0,0.1);
    }
    .pharmacy-card {
        background-color: #f0fdf4;
        border-left: 5px solid #16a34a;
        padding: 15px;
        border-radius: 6px;
        margin-bottom: 12px;
        box-shadow: 0 1px 3px rgba(0,0,0,0.1);
    }
    .badge {
        display: inline-block;
        background-color: #e2e8f0;
        color: #334155;
        padding: 3px 8px;
        border-radius: 12px;
        font-size: 0.8rem;
        font-weight: 600;
        margin-right: 4px;
    }
    </style>
""", unsafe_allow_html=True)

# Load database
@st.cache_data
def load_data():
    try:
        return pd.read_csv("providers.csv")
    except Exception:
        # Fallback inline sample data if file missing
        data = {
            "clinic_name": ["Metro Heart Institute", "Pacific Dermatology", "Sunset Urgent Care"],
            "specialty": ["Cardiology", "Dermatology", "Urgent Care"],
            "accepted_insurances": ["Medicaid, Blue Cross Blue Shield, Aetna", "Blue Cross Blue Shield, Cigna", "Medicaid, Cash/Uninsured"],
            "city_zip": [90210, 90210, 90210],
            "address_phone": ["123 Health Ave | (555) 019-2831", "456 Skin Care Blvd | (555) 012-9843", "789 Sunset Blvd | (555) 014-5512"],
            "type": ["Clinic", "Clinic", "Clinic"]
        }
        return pd.DataFrame(data)

df_providers = load_data()

# Header Section
st.title("🩺 AI Patient Care Navigator & Triage")
st.caption("Empowering patients to find appropriate, in-network specialist care and avoid delays.")

# Sidebar Filters & Setup
with st.sidebar:
    st.header("📋 Patient Settings")
    
    insurance_options = [
        "Medicaid", 
        "Blue Cross Blue Shield", 
        "Aetna", 
        "Cigna", 
        "UnitedHealthcare", 
        "Medicare", 
        "Cash/Uninsured"
    ]
    selected_insurance = st.selectbox("Select Your Insurance Provider:", insurance_options)
    
    user_zip = st.text_input("Enter Your ZIP Code:", value="90210")
    
    st.divider()
    st.warning("⚠️ **Medical Emergency Alert**\nIf you are experiencing a life-threatening emergency, please call **911** or go to the nearest Emergency Room immediately.")

# Emergency Keyword Detection
EMERGENCY_KEYWORDS = [
    "chest pain", "shortness of breath", "cannot breathe", "can't breathe", 
    "numbness", "paralysis", "stroke", "heart attack", "unconscious", 
    "fainted", "severe bleeding", "poison", "coughing blood"
]

# Triage Mapping Logic
SPECIALTY_MAP = {
    "Cardiology": ["heart", "chest pain", "palpitation", "high blood pressure", "artery", "cardiac"],
    "Dermatology": ["skin", "rash", "mole", "itch", "acne", "eczema", "lesion", "hive", "spot"],
    "Orthopedics": ["bone", "joint", "knee", "shoulder", "fracture", "sprain", "back pain", "ligament", "ankle"],
    "Neurology": ["headache", "migraine", "dizziness", "seizure", "numbness", "tingling", "brain", "memory"],
    "Gastroenterology": ["stomach", "nausea", "vomiting", "acid reflux", "gut", "abdomen", "diarrhea", "cramp"],
    "Psychiatry": ["anxiety", "depression", "panic", "mental health", "stress", "insomnia", "mood"],
    "Ophthalmology": ["eye", "vision", "blurry", "cataract", "cornea", "sight"]
}

def analyze_symptoms(symptoms_text):
    text = symptoms_text.lower()
    
    # Check for emergency
    for kw in EMERGENCY_KEYWORDS:
        if kw in text:
            return "EMERGENCY", "High Risk / Emergency"
            
    # Check specialty mapping
    for specialty, keywords in SPECIALTY_MAP.items():
        for kw in keywords:
            if re.search(r'\b' + re.escape(kw) + r'\b', text):
                return specialty, "Routine / Specialist Needed"
                
    # Default fallback
    return "Urgent Care", "General / Primary Care Needed"

# Chatbot Interface
st.subheader("💬 Describe Your Symptoms")
user_input = st.text_area(
    "How are you feeling today? (e.g., 'I have a painful red rash on my arm' or 'My knee hurts when I walk')",
    placeholder="Type your symptoms here...",
    height=100
)

if st.button("Find Care & Match Specialist", type="primary"):
    if not user_input.strip():
        st.info("Please describe your symptoms above to receive triage guidance.")
    else:
        specialty, urgency = analyze_symptoms(user_input)
        
        if specialty == "EMERGENCY":
            st.markdown("""
                <div class="emergency-box">
                    🚨 <strong>EMERGENCY DETECTED</strong><br>
                    Your symptoms may indicate a serious medical condition requiring immediate attention.<br>
                    Please call <strong>911</strong> or go to the nearest Emergency Room right away. Do not wait for an appointment.
                </div>
            """, unsafe_allow_html=True)
        else:
            st.success(f"**Recommended Medical Specialty:** {specialty}")
            st.info(f"**Assessed Urgency Level:** {urgency}")
            
            st.divider()
            st.markdown(f"### 📍 Matching In-Network Care Near `{user_zip}` for `{selected_insurance}`")
            
            # Convert zip code to integer for comparison if possible
            try:
                zip_int = int(user_zip)
            except ValueError:
                zip_int = None

            # Filter clinics
            clinics_df = df_providers[df_providers['type'] == 'Clinic']
            matching_clinics = clinics_df[
                (clinics_df['specialty'].str.lower() == specialty.lower()) & 
                (clinics_df['accepted_insurances'].str.contains(selected_insurance, case=False, na=False))
            ]
            
            if zip_int is not None:
                local_clinics = matching_clinics[matching_clinics['city_zip'] == zip_int]
            else:
                local_clinics = matching_clinics

            if not local_clinics.empty:
                st.write(f"Found **{len(local_clinics)}** specialist clinic(s) in your area:")
                for _, row in local_clinics.iterrows():
                    st.markdown(f"""
                        <div class="care-card">
                            <h4 style="margin:0; color:#0369a1;">🏥 {row['clinic_name']}</h4>
                            <p style="margin:4px 0;"><strong>Specialty:</strong> {row['specialty']}</p>
                            <p style="margin:4px 0;"><strong>Location & Contact:</strong> {row['address_phone']}</p>
                            <p style="margin:4px 0;"><span class="badge">In-Network ({selected_insurance})</span> <span class="badge">ZIP: {row['city_zip']}</span></p>
                        </div>
                    """, unsafe_allow_html=True)
            elif not matching_clinics.empty:
                st.warning(f"No direct clinic match found in ZIP `{user_zip}`. Here are in-network **{specialty}** options nearby:")
                for _, row in matching_clinics.iterrows():
                    st.markdown(f"""
                        <div class="care-card">
                            <h4 style="margin:0; color:#0369a1;">🏥 {row['clinic_name']}</h4>
                            <p style="margin:4px 0;"><strong>Specialty:</strong> {row['specialty']}</p>
                            <p style="margin:4px 0;"><strong>Location & Contact:</strong> {row['address_phone']}</p>
                            <p style="margin:4px 0;"><span class="badge">In-Network ({selected_insurance})</span> <span class="badge">ZIP: {row['city_zip']}</span></p>
                        </div>
                    """, unsafe_allow_html=True)
            else:
                st.warning(f"No specific in-network clinic found for {specialty}. We recommend reaching out to a local Urgent Care or your Primary Care Physician.")

            # Filter pharmacies
            pharmacies_df = df_providers[df_providers['type'] == 'Pharmacy']
            matching_pharmacies = pharmacies_df[
                pharmacies_df['accepted_insurances'].str.contains(selected_insurance, case=False, na=False)
            ]
            if zip_int is not None and not matching_pharmacies.empty:
                local_pharmacies = matching_pharmacies[matching_pharmacies['city_zip'] == zip_int]
                if local_pharmacies.empty:
                    local_pharmacies = matching_pharmacies
            else:
                local_pharmacies = matching_pharmacies

            if not local_pharmacies.empty:
                st.markdown("#### 💊 Nearby In-Network Pharmacies")
                for _, row in local_pharmacies.iterrows():
                    st.markdown(f"""
                        <div class="pharmacy-card">
                            <h5 style="margin:0; color:#15803d;">💊 {row['clinic_name']}</h5>
                            <p style="margin:4px 0;"><strong>Address & Phone:</strong> {row['address_phone']}</p>
                            <p style="margin:4px 0;"><span class="badge">Accepts {selected_insurance}</span></p>
                        </div>
                    """, unsafe_allow_html=True)

# Footer Disclaimer
st.divider()
st.caption("ℹ️ **Disclaimer**: This AI prototype is an educational demonstration designed for triage assistance and care navigation. It does not provide medical diagnoses or replace professional medical evaluation.")
