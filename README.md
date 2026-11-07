# Hello Provider: AI-Powered Patient Care Navigation &amp; Triage System

Hello Provider is an intelligent, empathetic web application designed to bridge the gap between patient symptom onset and timely, in-network medical care. Built specifically for the San Francisco healthcare ecosystem, the system combines multi-modal input processing (voice transcription, live camera capture, and side-by-side photo comparison) with interactive clinical triage and real-time provider matching.

---

## 1\. Project Mission &amp; Problem Statement

### The Healthcare Navigation Gap

Navigating medical care during acute or evolving health issues presents significant challenges for patients:

* **Diagnostic Delays**: Patients frequently struggle to identify the correct medical specialty, leading to misdirection or delayed treatment.
* **Administrative &amp; Network Barriers**: Finding local providers who accept specific insurance plans or offer sliding-scale fees in immediate geographic proximity can be overwhelming.
* **Visual Progression Tracking**: Patients and clinicians often lack accessible tools to track how physical symptoms (e.g., rashes, swelling, surgical wounds) evolve over time.

### The Hello Provider Solution

Hello Provider addresses these friction points through an accessible, privacy-conscious Streamlit interface:

* **Guided Triage &amp; Consensus**: Evaluates patient symptoms conversationally, proposing suspected conditions and associated symptoms while seeking patient consensus before recommending specialist pathways.
* **Geographic &amp; Insurance Precision**: Queries a curated database of 23 San Francisco medical centers, specialty clinics, emergency rooms, and pharmacies, matching by exact neighborhood ZIP codes or nearby SF proximity.
* **Multi-Modal Visual Progression**: Enables patients to upload or capture baseline and current photos (e.g., Today vs. 10 Days Ago) to monitor visual symptom changes.

---

## 2\. Key Features

### 🎙️ Speech-to-Text &amp; Multi-Modal Input

* **Web Speech Integration**: Built-in HTML5 Web Speech API widget allows hands-free voice transcription directly within the application window.
* **Live Camera Capture**: Integrated camera input enables patients to snap real-time photos of symptoms using a smartphone camera or desktop webcam.
* **Side-by-Side Photo Comparison**: Dedicated dual-photo mode allows patients to upload a baseline image (e.g., 10 days ago) alongside a current photo for comparative visual analysis.

### 🩺 Clinical Triage Engine &amp; Emergency Safety

* **Emergency Safeguards**: Automated keyword and severity filters detect critical symptoms (such as chest pain, breathing difficulty, or severe bleeding) and immediately trigger high-priority Red Emergency Alerts directing patients to 911 or local SF Emergency Rooms.
* **Specialty Mapping**: Categorizes complaints into appropriate specialties including Dermatology, Cardiology, Orthopedics, Neurology, Gastroenterology, Ophthalmology, Pediatrics, and Urgent Care.
* **Interactive Patient Consensus**: Presents suspected conditions alongside associated symptom checklists and asks patients for agreement before displaying provider contacts.

### 📍 San Francisco Care Network &amp; Insurance Filtering

* **Comprehensive SF Database**: Features leading institutions such as UCSF Health (Parnassus &amp; Mission Bay), Sutter Health CPMC, Kaiser Permanente SF, Zuckerberg San Francisco General ER, Saint Francis Memorial, One Medical, and local pharmacies (Walgreens, CVS, UCSF Pharmacy).
* **Insurance Alignment**: Filters by major providers (Blue Cross Blue Shield, Aetna, Cigna, Medicaid, Medicare, UnitedHealthcare, Kaiser) alongside options for out-of-network, uninsured, or sliding-scale care.
* **ZIP Code Proximity Fallback**: Prioritizes exact neighborhood match and automatically identifies top-rated facilities in adjacent SF ZIP codes when local matches are unavailable.

### 📄 Care Summary Generator &amp; Session Import

* **Downloadable Referral Brief**: Generates a standardized text document (`HelloProvider_CareSummary.txt`) detailing patient demographics, clinical context, reported symptoms, triage notes, matched providers, and next steps.
* **Historical Session Resume**: Allows returning patients to re-upload previous summary files to restore clinical context and continue past conversations seamlessly.

---

## 3\. System Architecture &amp; Workflow

```
[ User Inputs: Text / Voice / Single or Dual Photos ]
                       │
                       ▼
[ Required &amp; Optional Clinical Intake Validation ]
                       │
                       ▼
[ Emergency Safety Filter ] ──► [ Emergency Red Alert (911 / ER) ]
                       │ (If Non-Emergency)
                       ▼
[ AI Clinical Triage &amp; Visual Progression Analysis ]
                       │
                       ▼
[ Interactive Consensus Prompt ("Do You Agree?") ]
            │                               │
  (Disagrees / Reconsider)             (Agrees)
            │                               │
            ▼                               ▼
[ Discussion / Re-evaluation ]   [ SF Provider &amp; Pharmacy Matching ]
                                            │
                                            ▼
                               [ Download Care Summary Brief ]

```

---

## 4\. Repository Structure

```
hello-provider/
├── app.py                 # Main Streamlit web application script
├── providers-v2.csv       # San Francisco healthcare provider &amp; pharmacy database
├── requirements.txt       # Python dependencies (streamlit, pandas, Pillow)
└── README.md              # Project documentation

```

---

## 5\. Local Setup &amp; Installation

### Prerequisites

* Python 3.9 or higher
* `pip` package manager

### Step-by-step Installation

1. **Clone the Repository**:  
```  
git clone
```
## 6\. Run on the Web
Head over to https://helloprovider.streamlit.app/
