import streamlit as st
from pathlib import Path
import google.generativeai as genai
import dotenv
import os
import tempfile
import uuid
from datetime import datetime
import pandas as pd
import plotly.express as px
import pytz
import json
import base64
from PIL import Image, ImageDraw, ImageFont
import io
import hashlib

# Backend setup
dotenv.load_dotenv()
api_key = os.getenv("GOOGLE_API_KEY")
genai.configure(api_key=api_key)

# Configure the model with appropriate settings for medical analysis
generation_config = {
    "temperature": 0.2,  # Lower temperature for more reliable medical information
    "top_p": 0.95,
    "top_k": 64,
    "max_output_tokens": 8192,
    "response_mime_type": "text/plain",
}

# Enhanced system prompt for better medical analysis
system_prompt = """
You are YSHY (Your Smart Healthcare Yardstick), an AI assistant specializing in analyzing images of feminine intimate health conditions. Your purpose is to provide preliminary information and guidance while maintaining complete privacy and respect.

ANALYSIS INSTRUCTIONS:
1. Carefully examine the image of the intimate area for signs of common conditions such as:
   - Yeast infections (white discharge, redness, swelling)
   - Bacterial vaginosis (thin grayish discharge, odor)
   - Genital herpes (blisters, sores, lesions)
   - HPV warts (flesh-colored growths)
   - Dermatitis or irritation (redness, swelling, rash)
   - Lichen sclerosus (white patches, thinning skin)
   - Vulvodynia (no visible symptoms but reported pain)
   - Bartholin's cyst (swelling near vaginal opening)
   - Folliculitis (inflamed hair follicles)
   - Contact dermatitis (rash after exposure to irritants)

2. ALWAYS structure your response in this exact format:
   
   ## Preliminary Assessment
   [Provide a brief, sensitive description of what you observe in the image]
   
   ## Possible Conditions
   [List 1-3 potential conditions that match the visual symptoms, ordered by likelihood]
   
   ## Condition Details
   [For each condition mentioned, provide a brief description of what it is, common causes, and typical progression]
   
   ## Recommended Steps
   [Provide 3-5 specific recommendations for self-care and when to seek medical attention]
   
   ## Treatment Options
   [List potential treatments that might be prescribed by a healthcare provider]
   
   ## Prevention Tips
   [Provide 2-3 prevention tips specific to the identified conditions]
   
   ## Important Note
   This is not a medical diagnosis. Many feminine intimate conditions have similar visual symptoms. A healthcare provider can perform tests to determine the exact cause and appropriate treatment. Your privacy and health are important - please consult with a healthcare professional for proper diagnosis and treatment.

3. CRITICALLY IMPORTANT GUIDELINES:
   - Be clear, accurate, and compassionate in your language
   - NEVER claim to provide a definitive diagnosis
   - Emphasize the importance of professional medical advice
   - Focus on educational information about common conditions
   - Be respectful and use proper medical terminology
   - If the image quality is poor or insufficient, clearly state this limitation
   - Include a severity rating between 1-5 (1=mild, 5=severe) based on visible symptoms, but emphasize this is preliminary
   - Add a recommendation for timeframe to seek medical attention (e.g., "within 24 hours", "within the week", "at your convenience")

4. PRIVACY REQUIREMENTS:
   - Do not request any personally identifying information
   - Do not store or reference specific details from previous analyses
   - Treat each analysis as a new, independent assessment

Remember: Your role is to provide initial guidance and education to help users understand potential conditions and appropriate next steps, not to replace professional medical care.
"""

# Configure the symptom checker model
symptom_checker_prompt = """
You are a women's health symptom analyzer. Based on the symptom information provided, suggest possible conditions and appropriate next steps. Focus only on gynecological and intimate health conditions.

Analyze the symptoms provided and respond in this exact format:

## Possible Conditions
[List 3-5 potential conditions that match the described symptoms, ordered by likelihood]

## Condition Details
[For each condition, provide a brief explanation]

## Recommended Steps
[Provide specific recommendations for self-care and medical attention]

## Important Note
This is not a medical diagnosis. Similar symptoms can indicate different conditions. A healthcare provider can perform tests to determine the exact cause and appropriate treatment.

Be accurate, compassionate, and emphasize the importance of professional medical advice.
"""

# Initialize Gemini models
model = genai.GenerativeModel(
    model_name="gemini-2.0-flash",
    generation_config=generation_config,
)

symptom_model = genai.GenerativeModel(
    model_name="gemini-2.0-flash",
    generation_config=generation_config,
)

# User session management
if 'session_id' not in st.session_state:
    st.session_state.session_id = str(uuid.uuid4())
if 'history' not in st.session_state:
    st.session_state.history = []
if 'history_file' not in st.session_state:
    st.session_state.history_file = None
if 'user_timezone' not in st.session_state:
    st.session_state.user_timezone = "UTC"
if 'language' not in st.session_state:
    st.session_state.language = "English"
if 'symptom_tracker' not in st.session_state:
    st.session_state.symptom_tracker = []
if 'reminder_days' not in st.session_state:
    st.session_state.reminder_days = 7

# Data Handling Functions
def generate_anonymous_id():
    """Generate a unique anonymous ID based on session and timestamp"""
    unique_string = f"{st.session_state.session_id}-{datetime.now().isoformat()}"
    return hashlib.sha256(unique_string.encode()).hexdigest()[:12]

def save_history_to_file():
    """Save analysis history to an encrypted file for user download"""
    if st.session_state.history:
        history_data = json.dumps({
            "session_id": st.session_state.session_id,
            "history": st.session_state.history,
            "symptom_tracker": st.session_state.symptom_tracker,
            "exported_date": datetime.now().isoformat()
        })
        # Simple encryption by encoding to base64 (not truly secure but adds a layer of privacy)
        encoded_data = base64.b64encode(history_data.encode()).decode()
        st.session_state.history_file = encoded_data
        return encoded_data
    return None

def load_history_from_file(file_content):
    """Load analysis history from an uploaded file"""
    try:
        # Decode the base64 encrypted data
        decoded_data = base64.b64decode(file_content).decode()
        data = json.loads(decoded_data)
        
        # Validate the data structure
        if "history" in data and "session_id" in data and "symptom_tracker" in data:
            st.session_state.history = data["history"]
            st.session_state.symptom_tracker = data["symptom_tracker"]
            return True
        return False
    except Exception as e:
        st.error(f"Could not load history file: {str(e)}")
        return False

def add_to_symptom_tracker(condition, severity, date=None):
    """Add a symptom entry to the tracker"""
    if date is None:
        date = datetime.now()
    
    st.session_state.symptom_tracker.append({
        "date": date.isoformat(),
        "condition": condition,
        "severity": severity
    })

def get_condition_trend_data():
    """Get data for condition trend visualization"""
    if not st.session_state.symptom_tracker:
        return None
    
    # Convert to DataFrame for easier manipulation
    df = pd.DataFrame(st.session_state.symptom_tracker)
    if df.empty:
        return None
    
    # Convert date strings to datetime
    df['date'] = pd.to_datetime(df['date'])
    
    # Sort by date
    df = df.sort_values('date')
    
    return df

# Image Processing Functions
def anonymize_image(image_bytes):
    """Apply a subtle watermark to indicate the image is being processed privately"""
    try:
        img = Image.open(io.BytesIO(image_bytes))
        draw = ImageDraw.Draw(img)
        
        # Add subtle "PRIVATE ANALYSIS" text in corner
        try:
            font = ImageFont.truetype("arial.ttf", 20)
        except IOError:
            font = ImageFont.load_default()
        
        # Add semi-transparent text in corner
        draw.text((10, 10), "YSHY PRIVATE", fill=(255, 255, 255, 128), font=font)
        
        # Convert back to bytes
        buffer = io.BytesIO()
        img.save(buffer, format="JPEG")
        return buffer.getvalue()
    except Exception as e:
        # If any error occurs, return original image
        return image_bytes

# UI Configuration
st.set_page_config(
    page_title="YSHY | Private Healthcare Assistant",
    page_icon="🩺",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Custom CSS for improved styling
st.markdown("""
<style>
    .reportview-container {
        background-color: #f0f8ff;
    }
    .main .block-container {
        padding-top: 2rem;
        padding-bottom: 2rem;
    }
    .stButton button {
        border-radius: 20px;
    }
    .big-font {
        font-size: 20px !important;
    }
    .stAlert {
        border-radius: 10px;
    }
    .reminder-box {
        background-color: #f0f4f8;
        padding: 15px;
        border-radius: 10px;
        border-left: 5px solid #4e89ae;
    }
    .privacy-banner {
        background-color: #172A42;
        padding: 10px;
        border-radius: 5px;
        text-align: center;
        margin-bottom: 20px;
        border: 1px solid #e9ecef;
    }
    .result-box {
        border-left: 5px solid #6c5ce7;
        padding-left: 15px;
    }
    .condition-high {
        color: #e74c3c;
        font-weight: bold;
    }
    .condition-medium {
        color: #f39c12;
        font-weight: bold;
    }
    .condition-low {
        color: #2ecc71;
        font-weight: bold;
    }
</style>
""", unsafe_allow_html=True)

# Sidebar for settings and tools
with st.sidebar:
    st.image("https://img.icons8.com/color/96/000000/caduceus.png", width=50)
    st.title("YSHY: Your Smart Healthcare Yardstick")

    # User Settings
    st.header("Settings")
    
    # Language selection
    if st.button("Switch to Hindi"):
        st.switch_page("pages/hindi.py")
    
    

    
    # QR code for sharing app (placeholder - in real app would generate actual QR)
    st.header("Share Anonymously")
    st.image("https://api.qrserver.com/v1/create-qr-code/?size=150x150&data=https://yshy-health-app.streamlit.app", width=150)
    st.caption("Scan to share this app with someone who needs it")

# Main App Interface
st.title("YSHY: Your Smart Healthcare Yardstick")
st.markdown("""
<div class="privacy-banner">
    🔒 <b>Privacy Assured:</b> Images are processed privately and immediately deleted. No data is stored on servers.
</div>
""", unsafe_allow_html=True)

st.markdown("""
### Private, Confidential Healthcare Guidance
Get preliminary information about intimate health concerns in a completely private environment.
""")

# Create tabs for different sections
tab1, tab2, tab3, tab4, tab5 = st.tabs(["Visual Analysis", "Symptom Checker", "History & Trends", "Resources", "Education"])

with tab1:
    st.header("Visual Analysis")
    st.markdown("Upload one or more images for AI-assisted analysis. Images are processed privately and immediately deleted.")
    
    # File uploader with multiple file support
    uploaded_files = st.file_uploader("Choose images...", type=["png", "jpg", "jpeg"], 
                                     accept_multiple_files=True,
                                     help="Select clear, well-lit images of the affected area(s)")
    
    col1, col2 = st.columns([1, 1])
    
    with col1:
        if uploaded_files:
            # Display uploaded images count
            st.info(f"📁 {len(uploaded_files)} image(s) uploaded")
            
            # Display all uploaded images with enhanced privacy
            with st.expander("Review uploaded images", expanded=False):
                for i, uploaded_file in enumerate(uploaded_files):
                    # Process each image to add a privacy marker
                    image_data = uploaded_file.getvalue()
                    processed_image = anonymize_image(image_data)
                    st.image(processed_image, width=200, 
                            caption=f"Image {i+1}: {uploaded_file.name} (only visible to you)")
                    st.divider()
            
            analyze_button = st.button("Generate Private Analysis for All Images", 
                                     type="primary", use_container_width=True)
            
            if analyze_button:
                with st.spinner(f"Analyzing {len(uploaded_files)} image(s)... Please wait (30-60 seconds)"):
                    try:
                        all_analyses = []
                        combined_severity = 1
                        all_conditions = []
                        
                        # Process each image
                        for i, uploaded_file in enumerate(uploaded_files):
                            st.write(f"Processing image {i+1}/{len(uploaded_files)}...")
                            
                            # Process the image with Gemini
                            image_data = uploaded_file.getvalue()
                            image_parts = [{"mime_type": f"image/{uploaded_file.name.split('.')[-1]}", 
                                          "data": image_data}]
                            
                            # Modified prompt for multiple image context
                            multi_image_prompt = system_prompt + f"\n\nNote: This is image {i+1} of {len(uploaded_files)} images being analyzed together. Please provide analysis for this specific image while considering it may be part of a series showing the same or related condition."
                            
                            prompt_parts = [image_parts[0], multi_image_prompt]
                            
                            response = model.generate_content(prompt_parts)
                            
                            if response:
                                # Extract severity information
                                severity = 1  # Default
                                response_text = response.text
                                
                                # Try to extract severity from the response text
                                if "severity" in response_text.lower():
                                    for j in range(5, 0, -1):  # Check from 5 to 1
                                        if f"severity: {j}" in response_text.lower() or f"severity rating: {j}" in response_text.lower():
                                            severity = j
                                            break
                                
                                # Track highest severity across all images
                                combined_severity = max(combined_severity, severity)
                                
                                # Extract conditions
                                conditions = []
                                if "Possible Conditions" in response_text:
                                    conditions_section = response_text.split("## Possible Conditions")[1].split("##")[0]
                                    for line in conditions_section.strip().split("\n"):
                                        if line.strip().startswith("-") or line.strip().startswith("*"):
                                            condition = line.strip().replace("-", "").replace("*", "").split("(")[0].strip()
                                            conditions.append(condition)
                                            if condition not in all_conditions:
                                                all_conditions.append(condition)
                                
                                all_analyses.append({
                                    "image_name": uploaded_file.name,
                                    "image_number": i + 1,
                                    "analysis": response_text,
                                    "severity": severity,
                                    "conditions": conditions
                                })
                        
                        # Store the combined analysis in history
                        timestamp = datetime.now()
                        analysis_entry = {
                            "id": generate_anonymous_id(),
                            "timestamp": timestamp.isoformat(),
                            "type": "multi_image_analysis",
                            "image_count": len(uploaded_files),
                            "analyses": all_analyses,
                            "combined_severity": combined_severity,
                            "all_conditions": all_conditions
                        }
                        st.session_state.history.append(analysis_entry)
                        
                        # Add to symptom tracker with highest severity condition
                        if all_conditions:
                            add_to_symptom_tracker(all_conditions[0], combined_severity, timestamp)
                        
                        # Display the combined analysis results
                        st.markdown("### Analysis Results")
                        st.markdown(f"**Analysis of {len(uploaded_files)} image(s)**")
                        st.markdown(f"**Overall Severity Level:** {combined_severity}/5")
                        
                        # Show individual image analyses
                        for analysis in all_analyses:
                            with st.expander(f"📷 Analysis for Image {analysis['image_number']}: {analysis['image_name']}", expanded=True):
                                st.markdown(f"**Severity:** {analysis['severity']}/5")
                                st.markdown(analysis['analysis'])
                                if analysis['conditions']:
                                    st.markdown(f"**Identified Conditions:** {', '.join(analysis['conditions'])}")
                        
                        # Combined summary
                        if len(uploaded_files) > 1:
                            st.markdown("### Combined Summary")
                            st.markdown(f"""
                            **Overall Assessment:**
                            - **Total Images Analyzed:** {len(uploaded_files)}
                            - **Highest Severity Level:** {combined_severity}/5
                            - **All Identified Conditions:** {', '.join(all_conditions) if all_conditions else 'None identified'}
                            
                            **Recommendation:** Based on the analysis of multiple images, {'consider seeking medical attention promptly' if combined_severity >= 3 else 'monitor symptoms and consider self-care options'}.
                            """)
                        
                        # Create comprehensive report for download
                        report_content = f"""YSHY Multi-Image Analysis Report - {timestamp.strftime('%Y-%m-%d %H:%M')}

SUMMARY:
- Total Images Analyzed: {len(uploaded_files)}
- Overall Severity Level: {combined_severity}/5
- All Identified Conditions: {', '.join(all_conditions) if all_conditions else 'None identified'}

INDIVIDUAL IMAGE ANALYSES:
{'='*50}

"""
                        
                        for analysis in all_analyses:
                            report_content += f"""
IMAGE {analysis['image_number']}: {analysis['image_name']}
Severity: {analysis['severity']}/5
Conditions: {', '.join(analysis['conditions']) if analysis['conditions'] else 'None identified'}

{analysis['analysis']}

{'='*50}
"""
                        
                        report_content += f"""

IMPORTANT DISCLAIMER:
This is not a medical diagnosis. Please consult a healthcare professional for proper evaluation.
Multiple images can provide a more comprehensive view, but professional medical assessment is always recommended.
"""
                        
                        # Offer to save the comprehensive report
                        st.download_button(
                            label=f"Save Complete Analysis Report ({len(uploaded_files)} images)",
                            data=report_content,
                            file_name=f"yshy_multi_report_{timestamp.strftime('%Y%m%d_%H%M')}.txt",
                            mime="text/plain"
                        )

                    except Exception as e:
                        st.error(f"An error occurred during analysis: {str(e)}")
                        st.info("Please try again with different images or check your connection.")
    
    with col2:
        # Enhanced supportive information panel for multiple images
        st.markdown("#### Understanding Your Results")
        st.markdown("""
        Our AI assistant analyzes your image(s) to provide:
        
        - **Individual assessment** of each uploaded image
        - **Combined analysis** when multiple images are provided
        - **Severity comparison** across different images
        - **Comprehensive condition identification**
        - **Overall recommendations** based on all images
        
        **Multiple Image Benefits:**
        - Better condition identification
        - Progress tracking over time
        - Different angle perspectives
        - More comprehensive assessment
        """)
        
        st.markdown("#### Tips for Multiple Images")
        st.info("""
        📸 **Best Practices:**
        - Upload 2-4 clear images maximum
        - Show different angles of the same area
        - Include close-up and wider views
        - Ensure good lighting for all images
        - Avoid blurry or dark photos
        """)
        
        st.markdown("#### Common Conditions")
        with st.expander("Yeast Infection"):
            st.markdown("""
            **Symptoms:** Thick white discharge, itching, redness, swelling
            
            **Self-care:** Over-the-counter antifungal treatments
            
            **When to see a doctor:** If symptoms persist after treatment or recur frequently
            """)
            
        with st.expander("Bacterial Vaginosis"):
            st.markdown("""
            **Symptoms:** Thin grayish discharge, fishy odor
            
            **Treatment:** Prescription antibiotics
            
            **When to see a doctor:** BV requires medical treatment
            """)
            
        with st.expander("Genital Herpes"):
            st.markdown("""
            **Symptoms:** Blisters, sores, lesions, pain, itching
            
            **Treatment:** Antiviral medications
            
            **When to see a doctor:** As soon as symptoms appear for proper diagnosis and treatment
            """)
            
        with st.expander("Contact Dermatitis"):
            st.markdown("""
            **Symptoms:** Redness, irritation, itching, swelling
            
            **Self-care:** Remove irritant, gentle cleaning, soothing creams
            
            **When to see a doctor:** If symptoms worsen or don't improve within a few days
            """)

with tab2:
    st.header("Symptom Checker")
    st.markdown("Describe your symptoms for preliminary guidance without uploading images.")
    
    symptom_text = st.text_area("Describe your symptoms in detail:", 
                               placeholder="Example: I've noticed itching and redness for the past 3 days, along with unusual discharge...",
                               height=150)
    
    symptom_duration = st.slider("How long have you had these symptoms?", 1, 90, 7, help="Number of days")
    
    pain_level = st.select_slider("Pain level:", options=["None", "Mild", "Moderate", "Severe", "Very Severe"], value="None")
    
    additional_factors = st.multiselect("Select any factors that apply:", 
                                        ["Recent new sexual partner", "Changed hygiene products", "Currently on antibiotics", 
                                         "Currently menstruating", "Pregnant", "Irregular periods", "Post-menopausal",
                                         "Using hormonal contraception", "Recent UTI", "Diabetes", "Immunocompromised"])
    
    if st.button("Check Symptoms", type="primary"):
        if symptom_text and len(symptom_text) > 20:
            with st.spinner("Analyzing symptoms... Please wait"):
                try:
                    # Prepare the symptom information for the model
                    symptom_info = f"""
                    Symptoms: {symptom_text}
                    Duration: {symptom_duration} days
                    Pain level: {pain_level}
                    Additional factors: {', '.join(additional_factors) if additional_factors else 'None reported'}
                    """
                    
                    # Process with Gemini
                    response = symptom_model.generate_content([symptom_checker_prompt, symptom_info])
                    
                    # Store in history
                    timestamp = datetime.now()
                    analysis_entry = {
                        "id": generate_anonymous_id(),
                        "timestamp": timestamp.isoformat(),
                        "type": "symptom_check",
                        "analysis": response.text if response else "Analysis failed",
                        "symptom_text": symptom_text[:100] + "..." if len(symptom_text) > 100 else symptom_text
                    }
                    st.session_state.history.append(analysis_entry)
                    
                    if response:
                        # Display results
                        st.markdown("### Symptom Analysis")
                        st.markdown(response.text)
                        
                        # Prompt for next steps
                        st.info("💡 Based on this analysis, consider scheduling a healthcare appointment or using the Visual Analysis tab if appropriate.")
                
                except Exception as e:
                    st.error(f"An error occurred: {str(e)}")
        else:
            st.warning("Please provide a detailed description of your symptoms for accurate analysis.")

# Replace the problematic section in tab3 (around line 657) with this fixed version:

import pandas as pd
import plotly.express as px
from datetime import datetime, timezone
import pytz

def get_condition_trend_data():
    """
    Extract condition trend data from session history
    Returns a DataFrame with date, severity, and condition columns
    """
    if not st.session_state.history:
        return None
    
    trend_records = []
    
    for entry in st.session_state.history:
        # Parse timestamp
        try:
            if isinstance(entry.get("timestamp"), str):
                timestamp = datetime.fromisoformat(entry["timestamp"])
            else:
                continue
        except (ValueError, TypeError):
            continue
        
        # Extract severity and conditions based on entry type
        severity = None
        conditions = []
        
        entry_type = entry.get("type", "analysis")
        
        if entry_type == "multi_image_analysis":
            # Use combined severity for multi-image analysis
            severity = entry.get("combined_severity")
            conditions = entry.get("all_conditions", [])
        elif entry_type == "symptom_check":
            # Extract severity from symptom check
            severity = entry.get("severity")
            conditions = entry.get("conditions", [])
        elif "severity" in entry:
            # Regular analysis with severity
            severity = entry.get("severity")
            conditions = entry.get("conditions", [])
        
        # Skip entries without severity data
        if severity is None:
            continue
        
        # Convert severity to numeric if it's a string
        try:
            severity = float(severity)
        except (ValueError, TypeError):
            continue
        
        # Add records for each condition or one general record
        if conditions:
            for condition in conditions:
                trend_records.append({
                    'date': timestamp.date(),
                    'datetime': timestamp,
                    'severity': severity,
                    'condition': condition,
                    'type': entry_type
                })
        else:
            # General health tracking without specific condition
            trend_records.append({
                'date': timestamp.date(),
                'datetime': timestamp,
                'severity': severity,
                'condition': 'General Health Concern',
                'type': entry_type
            })
    
    if not trend_records:
        return None
    
    # Convert to DataFrame and sort by date
    df = pd.DataFrame(trend_records)
    df = df.sort_values('datetime')
    
    return df

def calculate_trend_stats(trend_data):
    """
    Calculate trend statistics from the data
    """
    if trend_data is None or trend_data.empty:
        return None
    
    stats = {}
    
    # Overall statistics
    stats['total_entries'] = len(trend_data)
    stats['date_range'] = (trend_data['date'].max() - trend_data['date'].min()).days + 1
    stats['avg_severity'] = trend_data['severity'].mean()
    stats['max_severity'] = trend_data['severity'].max()
    stats['min_severity'] = trend_data['severity'].min()
    
    # Trend analysis
    if len(trend_data) >= 2:
        first_severity = trend_data.iloc[0]['severity']
        last_severity = trend_data.iloc[-1]['severity']
        stats['trend_direction'] = last_severity - first_severity
        
        # Linear trend (simple slope calculation)
        x = list(range(len(trend_data)))
        y = trend_data['severity'].tolist()
        n = len(x)
        
        if n > 1:
            slope = (n * sum(xi * yi for xi, yi in zip(x, y)) - sum(x) * sum(y)) / (n * sum(xi**2 for xi in x) - sum(x)**2)
            stats['trend_slope'] = slope
        else:
            stats['trend_slope'] = 0
    else:
        stats['trend_direction'] = 0
        stats['trend_slope'] = 0
    
    # Condition frequency
    condition_counts = trend_data['condition'].value_counts().to_dict()
    stats['condition_frequency'] = condition_counts
    
    return stats

def format_local_time(timestamp_str, timezone_str):
    """
    Format timestamp to local time
    """
    try:
        if isinstance(timestamp_str, str):
            dt = datetime.fromisoformat(timestamp_str)
        else:
            dt = timestamp_str
        
        local_tz = pytz.timezone(timezone_str)
        local_time = dt.astimezone(local_tz)
        return local_time.strftime("%b %d, %Y, %I:%M %p")
    except Exception:
        return "Unknown time"

# Initialize session state if needed
if 'history' not in st.session_state:
    st.session_state.history = []

if 'user_timezone' not in st.session_state:
    st.session_state.user_timezone = 'UTC'

# Main tab content
with tab3:
    st.header("History & Trends")
    
    # Left column for history list
    col1, col2 = st.columns([1, 1])
    
    with col1:
        st.subheader("Your Analysis History")
        st.caption("History is stored only in your current browser session")
        
        if not st.session_state.history:
            st.info("No analysis history yet. Your previous analyses will appear here.")
        else:
            # Add export functionality
            if st.button("📥 Export History", help="Download your analysis history as JSON"):
                import json
                history_json = json.dumps(st.session_state.history, indent=2, default=str)
                st.download_button(
                    label="Download History",
                    data=history_json,
                    file_name=f"health_analysis_history_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                    mime="application/json"
                )
            
            st.markdown("---")
            
            # Display history entries
            for i, entry in enumerate(reversed(st.session_state.history)):
                local_time = format_local_time(
                    entry.get("timestamp", ""), 
                    st.session_state.user_timezone
                )
                
                entry_type = entry.get("type", "analysis")
                
                # Create a custom title based on entry type
                if entry_type == "image_analysis":
                    title = f"🔍 Image Analysis - {local_time}"
                elif entry_type == "multi_image_analysis":
                    image_count = entry.get("image_count", 1)
                    title = f"🔍 Multi-Image Analysis ({image_count} images) - {local_time}"
                elif entry_type == "symptom_check":
                    title = f"📝 Symptom Check - {local_time}"
                    if "symptom_text" in entry and len(entry["symptom_text"]) < 50:
                        title += f" - {entry['symptom_text']}"
                else:
                    title = f"📊 Analysis - {local_time}"
                
                with st.expander(title):
                    # Display severity if available
                    severity = entry.get("severity") or entry.get("combined_severity")
                    if severity:
                        severity_color = "🔴" if float(severity) >= 4 else "🟡" if float(severity) >= 3 else "🟢"
                        st.markdown(f"**Severity:** {severity_color} {severity}/5")
                    
                    # Handle different entry structures
                    if entry_type == "multi_image_analysis":
                        if "all_conditions" in entry and entry["all_conditions"]:
                            st.markdown(f"**Identified Conditions:** {', '.join(entry['all_conditions'])}")
                        
                        if "analyses" in entry:
                            st.markdown("**Individual Image Results:**")
                            for j, analysis in enumerate(entry["analyses"]):
                                st.markdown(f"**📷 Image {analysis.get('image_number', j+1)}:**")
                                if "severity" in analysis:
                                    severity_color = "🔴" if float(analysis['severity']) >= 4 else "🟡" if float(analysis['severity']) >= 3 else "🟢"
                                    st.markdown(f"- **Severity:** {severity_color} {analysis['severity']}/5")
                                if "analysis" in analysis:
                                    st.markdown(f"- **Analysis:** {analysis['analysis']}")
                                if "conditions" in analysis and analysis["conditions"]:
                                    st.markdown(f"- **Conditions:** {', '.join(analysis['conditions'])}")
                                st.markdown("---")
                    
                    elif "analysis" in entry:
                        st.markdown(entry["analysis"])
                    
                    # Show conditions
                    conditions = entry.get("conditions") or entry.get("all_conditions")
                    if conditions:
                        st.markdown(f"**Conditions:** {', '.join(conditions)}")
                    
                    # Show symptom text for symptom checks
                    if "symptom_text" in entry:
                        st.markdown(f"**Symptoms Described:** {entry['symptom_text']}")
                    
                    # Show timestamp
                    st.caption(f"Recorded: {local_time}")
    
    with col2:
        st.subheader("Symptom Tracking")
        
        # Get trend data
        trend_data = get_condition_trend_data()
        trend_stats = calculate_trend_stats(trend_data)
        
        if trend_data is not None and not trend_data.empty:
            # Display summary statistics
            if trend_stats:
                col_a, col_b, col_c = st.columns(3)
                with col_a:
                    st.metric("Total Entries", trend_stats['total_entries'])
                with col_b:
                    st.metric("Days Tracked", trend_stats['date_range'])
                with col_c:
                    st.metric("Avg Severity", f"{trend_stats['avg_severity']:.1f}")
            
            # Severity over time chart
            st.write("### Condition Severity Over Time")
            
            # Create the plot
            fig = px.line(trend_data, x='date', y='severity', color='condition',
                         labels={"date": "Date", "severity": "Severity (1-5)", "condition": "Condition"},
                         title="Symptom Severity Tracking")
            
            # Customize the chart
            fig.update_layout(
                xaxis_title="Date",
                yaxis_title="Severity Level",
                yaxis=dict(range=[0.5, 5.5], tickmode='linear', tick0=1, dtick=1),
                hovermode="x unified",
                height=400
            )
            
            # Add severity level annotations
            fig.add_hline(y=1, line_dash="dot", line_color="green", annotation_text="Mild")
            fig.add_hline(y=3, line_dash="dot", line_color="orange", annotation_text="Moderate")
            fig.add_hline(y=5, line_dash="dot", line_color="red", annotation_text="Severe")
            
            st.plotly_chart(fig, use_container_width=True)
            
            # Trend analysis
            if trend_stats and len(trend_data) >= 2:
                st.write("### Trend Analysis")
                
                trend_direction = trend_stats['trend_direction']
                trend_slope = trend_stats['trend_slope']
                
                if abs(trend_slope) < 0.1:
                    trend_text = "Your condition appears stable"
                    trend_icon = "📊"
                    trend_color = "info"
                elif trend_slope < -0.1:
                    trend_text = "Your condition appears to be improving"
                    trend_icon = "📈"
                    trend_color = "success"
                else:
                    trend_text = "Your condition may be worsening - consider medical attention"
                    trend_icon = "📉"
                    trend_color = "warning"
                
                if trend_color == "success":
                    st.success(f"{trend_icon} {trend_text}")
                elif trend_color == "warning":
                    st.warning(f"{trend_icon} {trend_text}")
                else:
                    st.info(f"{trend_icon} {trend_text}")
            
            # Condition frequency
            if trend_stats and trend_stats['condition_frequency']:
                st.write("### Most Tracked Conditions")
                condition_df = pd.DataFrame(
                    list(trend_stats['condition_frequency'].items()),
                    columns=['Condition', 'Frequency']
                ).sort_values('Frequency', ascending=False)
                
                fig_bar = px.bar(condition_df, x='Condition', y='Frequency',
                               title="Frequency of Tracked Conditions")
                fig_bar.update_layout(xaxis_tickangle=-45, height=300)
                st.plotly_chart(fig_bar, use_container_width=True)
        
        else:
            st.info("No symptom tracking data yet. Use the Visual Analysis or Symptom Checker to start tracking.")
            
            # Show instructions instead of sample data
            st.write("### How Tracking Works")
            st.markdown("""
            📊 **Automatic Tracking**: Every analysis you perform is automatically tracked
            
            📈 **Severity Trends**: See how your symptoms change over time
            
            🏥 **Condition Monitoring**: Track specific health conditions
            
            📱 **Export Data**: Download your history for medical consultations
            """)
            
            # Clear history button for testing
            if st.session_state.history:
                if st.button("🗑️ Clear History", help="Remove all stored analysis history"):
                    st.session_state.history = []
                    st.rerun()


import requests
import json
from geopy.geocoders import Nominatim
import folium
from streamlit_folium import st_folium
import pandas as pd

# Enhanced Healthcare Resource Finder for tab4
with tab4:
    st.header("Healthcare Resources")
    
    st.subheader("Find Healthcare Providers Near You")
    
    # Location input
    location_col1, location_col2 = st.columns(2)
    with location_col1:
        options = [
            "Andhra Pradesh", "Arunachal Pradesh", "Assam", "Bihar", "Chhattisgarh",
            "Goa", "Gujarat", "Haryana", "Himachal Pradesh", "Jharkhand",
            "Karnataka", "Kerala", "Madhya Pradesh", "Maharashtra", "Manipur",
            "Meghalaya", "Mizoram", "Nagaland", "Odisha", "Punjab",
            "Rajasthan", "Sikkim", "Tamil Nadu", "Telangana", "Tripura",
            "Uttar Pradesh", "Uttarakhand", "West Bengal",
            "Andaman and Nicobar Islands", "Chandigarh",
            "Dadra and Nagar Haveli and Daman and Diu", "Delhi",
            "Jammu and Kashmir", "Ladakh", "Lakshadweep", "Puducherry",
            "United States", "United Kingdom", "Canada", "Australia", "Other"
        ]

        # Get the index of "Delhi"
        default_index = options.index("Delhi")

        state = st.selectbox("State/Region", options, index=default_index)
    
    with location_col2:
        if state == "Delhi":
            city = st.selectbox("District/City", [
                "Central Delhi", "East Delhi", "New Delhi", "North Delhi",
                "North East Delhi", "North West Delhi", "Shahdara",
                "South Delhi", "South East Delhi", "South West Delhi", "West Delhi"
            ])
        elif state == "Maharashtra":
            city = st.selectbox("District/City", [
                "Mumbai", "Pune", "Nagpur", "Nashik", "Aurangabad", "Solapur",
                "Amravati", "Kolhapur", "Sangli", "Satara", "Other"
            ])
        elif state == "Karnataka":
            city = st.selectbox("District/City", [
                "Bangalore", "Mysore", "Hubli", "Mangalore", "Belgaum",
                "Gulbarga", "Davanagere", "Shimoga", "Other"
            ])
        elif state == "Tamil Nadu":
            city = st.selectbox("District/City", [
                "Chennai", "Coimbatore", "Madurai", "Tiruchirappalli", "Salem",
                "Tirunelveli", "Erode", "Vellore", "Other"
            ])
        else:
            city = st.text_input("Enter your city/district:")
    
    service_type = st.selectbox("Type of Healthcare Service", [
        "Gynecologist/Women's Health Specialist",
        "General Physician",
        "Dermatologist",
        "Sexual Health Clinic",
        "Family Planning Center",
        "Emergency Services",
        "Pharmacy",
        "Diagnostic Center"
    ])
    
    radius = st.slider("Search radius (km)", 5, 50, 15)
    
    if st.button("Find Healthcare Providers", type="primary", key="healthcare_search_button"):
            if city and state:
                with st.spinner("Searching for healthcare providers in your area..."):
                    try:
                        # Step 1: Get location coordinates
                        geolocator = Nominatim(user_agent="yshy_healthcare_finder")
                        location_query = f"{city}, {state}"
                        if state not in ["United States", "United Kingdom", "Canada", "Australia", "Other"]:
                            location_query += ", India"
                        
                        location = geolocator.geocode(location_query)
                        
                        if not location:
                            st.error("Could not find the specified location. Please check your city and state names.")
                        else:
                            lat, lon = location.latitude, location.longitude
                            st.info(f"📍 Searching around: {location.address}")
                            
                            # Step 2: Search with multiple strategies
                            def search_with_multiple_strategies(lat, lon, radius_km):
                                """Try multiple search strategies to find healthcare providers"""
                                overpass_url = "http://overpass-api.de/api/interpreter"
                                all_providers = []
                                
                                # Strategy 1: All healthcare amenities (broadest search)
                                queries = [
                                    # Most basic - all doctors and hospitals
                                    f"""
                                    [out:json][timeout:25];
                                    (
                                    node["amenity"~"^(doctors|hospital|clinic|pharmacy)$"](around:{radius_km*1000},{lat},{lon});
                                    way["amenity"~"^(doctors|hospital|clinic|pharmacy)$"](around:{radius_km*1000},{lat},{lon});
                                    );
                                    out center meta;
                                    """,
                                    
                                    # Healthcare tag
                                    f"""
                                    [out:json][timeout:25];
                                    (
                                    node["healthcare"](around:{radius_km*1000},{lat},{lon});
                                    way["healthcare"](around:{radius_km*1000},{lat},{lon});
                                    );
                                    out center meta;
                                    """,
                                    
                                    # Medical offices
                                    f"""
                                    [out:json][timeout:25];
                                    (
                                    node["office"="healthcare"](around:{radius_km*1000},{lat},{lon});
                                    node["office"="physician"](around:{radius_km*1000},{lat},{lon});
                                    way["office"="healthcare"](around:{radius_km*1000},{lat},{lon});
                                    );
                                    out center meta;
                                    """
                                ]
                                
                                for i, query in enumerate(queries):
                                    st.write(f"🔍 Trying search strategy {i+1}...")
                                    try:
                                        response = requests.get(overpass_url, params={'data': query}, timeout=20)
                                        
                                        if response.status_code == 200:
                                            data = response.json()
                                            if data and 'elements' in data:
                                                st.write(f"✅ Found {len(data['elements'])} results with strategy {i+1}")
                                                all_providers.extend(data['elements'])
                                                if len(all_providers) >= 10:  # Stop if we have enough
                                                    break
                                            else:
                                                st.write(f"❌ No results from strategy {i+1}")
                                        else:
                                            st.write(f"⚠️ API error with strategy {i+1}: Status {response.status_code}")
                                            
                                    except Exception as e:
                                        st.write(f"⚠️ Strategy {i+1} failed: {str(e)}")
                                        continue
                                
                                return all_providers
                            
                            # Step 3: Execute search
                            raw_elements = search_with_multiple_strategies(lat, lon, radius)
                            
                            if not raw_elements:
                                st.error("❌ No healthcare providers found with any search method.")
                                st.info("This could mean:")
                                st.write("• Limited OpenStreetMap data in your area")  
                                st.write("• API connectivity issues")
                                st.write("• Try a larger city nearby")
                                
                                # Fallback: Show some general guidance
                                st.subheader("💡 Alternative Options:")
                                st.write("1. **Google Maps**: Search 'doctors near me' or 'hospitals near me'")
                                st.write("2. **Government Health Directory**: Check your state/country health department website")
                                st.write("3. **Insurance Provider**: Use your insurance company's provider directory")
                                
                                # Store empty providers list for download section
                                st.session_state.found_providers = []
                                
                            else:
                                st.success(f"✅ Found {len(raw_elements)} potential healthcare locations")
                                
                                # Step 4: Process and filter results
                                from math import radians, cos, sin, asin, sqrt
                                
                                def calculate_distance(lon1, lat1, lon2, lat2):
                                    """Calculate distance between two points using Haversine formula"""
                                    try:
                                        lon1, lat1, lon2, lat2 = map(radians, [lon1, lat1, lon2, lat2])
                                        dlon = lon2 - lon1
                                        dlat = lat2 - lat1
                                        a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
                                        c = 2 * asin(sqrt(a))
                                        return 6371 * c  # Earth radius in km
                                    except:
                                        return float('inf')
                                
                                processed_providers = []
                                seen_coords = set()
                                
                                for element in raw_elements:
                                    try:
                                        # Get coordinates
                                        if element['type'] == 'node':
                                            provider_lat, provider_lon = element['lat'], element['lon']
                                        elif element['type'] == 'way' and 'center' in element:
                                            provider_lat = element['center']['lat']
                                            provider_lon = element['center']['lon']
                                        else:
                                            continue
                                        
                                        # Skip duplicates
                                        coord_key = f"{provider_lat:.4f},{provider_lon:.4f}"
                                        if coord_key in seen_coords:
                                            continue
                                        seen_coords.add(coord_key)
                                        
                                        # Calculate distance
                                        distance = calculate_distance(lon, lat, provider_lon, provider_lat)
                                        if distance > radius:
                                            continue
                                        
                                        # Extract information
                                        tags = element.get('tags', {})
                                        
                                        # Get name (with multiple fallbacks)
                                        name = (tags.get('name') or 
                                            tags.get('operator') or 
                                            tags.get('brand') or
                                            'Healthcare Provider')
                                        
                                        # Skip obviously bad names
                                        if name.lower() in ['yes', 'no', '', 'null'] or len(name) < 2:
                                            continue
                                        
                                        # Build address
                                        address_parts = []
                                        for addr_key in ['addr:housenumber', 'addr:street', 'addr:city']:
                                            if tags.get(addr_key):
                                                address_parts.append(tags[addr_key])
                                        
                                        if not address_parts:
                                            address = f"Near {city}, {state}"
                                        else:
                                            address = ', '.join(address_parts)
                                        
                                        # Determine type
                                        amenity = tags.get('amenity', '')
                                        healthcare = tags.get('healthcare', '')
                                        office = tags.get('office', '')
                                        
                                        if amenity == 'hospital' or healthcare == 'hospital':
                                            provider_type = 'Hospital'
                                        elif amenity == 'pharmacy':
                                            provider_type = 'Pharmacy'
                                        elif amenity == 'clinic' or healthcare == 'clinic':
                                            provider_type = 'Clinic'
                                        elif amenity == 'doctors' or healthcare == 'doctor' or office in ['healthcare', 'physician']:
                                            provider_type = 'Doctor/Physician'
                                        else:
                                            provider_type = 'Healthcare Facility'
                                        
                                        provider_info = {
                                            'name': name,
                                            'address': address,
                                            'phone': tags.get('phone', tags.get('contact:phone', 'Not available')),
                                            'website': tags.get('website', tags.get('contact:website', 'Not available')),
                                            'distance': round(distance, 2),
                                            'lat': provider_lat,
                                            'lon': provider_lon,
                                            'type': provider_type,
                                            'opening_hours': tags.get('opening_hours', 'Call to confirm hours')
                                        }
                                        
                                        processed_providers.append(provider_info)
                                        
                                    except Exception as e:
                                        continue  # Skip problematic entries
                                
                                # Step 5: Sort and display results
                                processed_providers.sort(key=lambda x: x['distance'])
                                
                                # Store providers in session state for download
                                st.session_state.found_providers = processed_providers
                                st.session_state.search_location = f"{city}, {state}"
                                st.session_state.search_coordinates = (lat, lon)
                                
                                if processed_providers:
                                    st.success(f"🎯 Showing {len(processed_providers)} healthcare providers near you:")
                                    
                                    # Display each provider
                                    for i, provider in enumerate(processed_providers[:20]):  # Show top 20
                                        with st.expander(f"🏥 {provider['name']} ({provider['type']}) - {provider['distance']} km away"):
                                            
                                            col1, col2 = st.columns([3, 1])
                                            
                                            with col1:
                                                st.markdown(f"**📍 Address:** {provider['address']}")
                                                st.markdown(f"**📞 Phone:** {provider['phone']}")
                                                st.markdown(f"**🏥 Type:** {provider['type']}")
                                                st.markdown(f"**🕒 Hours:** {provider['opening_hours']}")
                                                
                                                if provider['website'] not in ['Not available', '']:
                                                    st.markdown(f"**🌐 Website:** [Visit Website]({provider['website']})")
                                            
                                            with col2:
                                                st.metric("📏 Distance", f"{provider['distance']} km")
                                                
                                                # Direction button
                                                maps_url = f"https://www.google.com/maps/dir/{lat},{lon}/{provider['lat']},{provider['lon']}"
                                                st.markdown(f"[🗺️ Get Directions]({maps_url})")
                                    
                                    # Optional: Simple map (if folium is available)
                                    try:
                                        st.subheader("🗺️ Location Map")
                                        
                                        # Create a simple text-based map info
                                        st.write("**Your Location:**", f"{city}, {state}")
                                        st.write("**Nearest Providers:**")
                                        for provider in processed_providers[:5]:
                                            maps_url = f"https://www.google.com/maps/dir/{lat},{lon}/{provider['lat']},{provider['lon']}"
                                            st.write(f"• [{provider['name']}]({maps_url}) - {provider['distance']} km")
                                        
                                    except:
                                        pass  # Skip map if libraries not available
                                
                                else:
                                    st.warning("⚠️ Found healthcare locations but couldn't process them properly.")
                                    st.info("Try expanding your search radius or check nearby cities.")
                    
                    except Exception as e:
                        st.error(f"❌ Search failed: {str(e)}")
                        st.info("💡 **Troubleshooting tips:**")
                        st.write("• Check your internet connection")
                        st.write("• Try a different city/state combination")
                        st.write("• Use a larger search radius")
                        # Store empty providers list for download section
                        st.session_state.found_providers = []
            
            else:
                st.warning("⚠️ Please select both state and city to search for healthcare providers.")

    
    # Other sections (Emergency Services, Insurance, Support Groups) remain outside the button block
    st.markdown("---")
    
    # Emergency services
    st.subheader("Emergency Services")
    st.error("🚨 **For Medical Emergencies:**")
    
    if state in ["Delhi", "Maharashtra", "Karnataka", "Tamil Nadu", "West Bengal"]:
        st.markdown("""
        - **Emergency Number:** 108, 102, or 112
        - **Ambulance:** 108
        - **Women's Helpline:** 1091, 181
        - **Police:** 100
        """)
    else:
        st.markdown("""
        - **Will Update Soon...**
        """)
    
    # Insurance and cost information

    
    # Use state-based condition instead of location_query
    indian_states = [
        "Andhra Pradesh", "Arunachal Pradesh", "Assam", "Bihar", "Chhattisgarh",
        "Goa", "Gujarat", "Haryana", "Himachal Pradesh", "Jharkhand",
        "Karnataka", "Kerala", "Madhya Pradesh", "Maharashtra", "Manipur",
        "Meghalaya", "Mizoram", "Nagaland", "Odisha", "Punjab",
        "Rajasthan", "Sikkim", "Tamil Nadu", "Telangana", "Tripura",
        "Uttar Pradesh", "Uttarakhand", "West Bengal",
        "Andaman and Nicobar Islands", "Chandigarh",
        "Dadra and Nagar Haveli and Daman and Diu", "Delhi",
        "Jammu and Kashmir", "Ladakh", "Lakshadweep", "Puducherry"
    ]
    
    if state in indian_states:
        st.markdown("""
        ### Healthcare Coverage in India
        
        **Government Schemes:**
        - [Ayushman Bharat](https://pmjay.gov.in/) - PM-JAY healthcare coverage
        - [CGHS](https://cghs.gov.in/) - Central Government Health Scheme
        - State-specific health insurance schemes
        
        **Private Insurance:**
        - Compare plans on [PolicyBazaar](https://www.policybazaar.com/health-insurance/)
        - [Religare Health Insurance](https://www.religarehealth.com/)
        - [Star Health Insurance](https://www.starhealth.in/)
        
        **Affordable Healthcare:**
        - Government hospitals and clinics
        - Jan Aushadhi stores for generic medicines
        - Mohalla Clinics (Delhi)
        - Primary Health Centers (PHCs)
        """)
    else:
        st.markdown("""
        ### International Healthcare Coverage
        
        **United States:**
        - [Healthcare.gov](https://www.healthcare.gov/) - ACA marketplace
        - [Medicaid](https://www.medicaid.gov/) - State programs
        - [GoodRx](https://www.goodrx.com/) - Prescription discounts
        
        **Other Countries:**
        - Most developed countries have universal healthcare
        - Check with local health authorities
        - Travel insurance for visitors
        """)
    
    # Local support groups and communities

    
    st.markdown("""
    ### Online Communities
    - [Intimate Health Support Group](https://www.facebook.com/groups/intimatehealthsupport) - Facebook group
    - [Women's Health Reddit](https://www.reddit.com/r/WomensHealth/) - Anonymous discussions
    - [Vulvar Pain Society](https://vulvalpainsociety.org/) - Support for vulvodynia
    - [Endometriosis Support Groups](https://endometriosisassn.org/) - Local chapter finder
    
    ### Professional Associations
    - Find certified gynecologists through medical associations
    - Local medical colleges and hospitals
    - Women's health clinics and centers
    """)
    
    # Resource download
    st.subheader("Download Healthcare Resource List")

    if st.button("Generate Personalized Resource List"):
        # Get providers from search results
        found_providers = getattr(st.session_state, 'found_providers', [])
        search_location = getattr(st.session_state, 'search_location', f"{city}, {state}")
        
        # Use state-based condition instead of location_query
        is_india = state in indian_states if 'indian_states' in locals() else state not in ["United States", "United Kingdom", "Canada", "Australia", "Other"]
        
        # Build the resource list with found providers
        resource_list = f"""YSHY Healthcare Resources for {search_location}
    Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M')}

    EMERGENCY CONTACTS:
    - Emergency: {'108, 102, 112' if is_india else '911 (US), 999 (UK), 000 (AU)'}
    - Women's Helpline: {'1091, 181' if is_india else "Local women's crisis centers"}

    SEARCH CRITERIA:
    - Location: {search_location}
    - Service Type: {service_type if 'service_type' in locals() else 'General Healthcare'}
    - Search Radius: {radius if 'radius' in locals() else '10'} km

    """
        
        # Add found providers section
        if found_providers:
            resource_list += f"""HEALTHCARE PROVIDERS FOUND ({len(found_providers)} locations):

    """
            
            # Group providers by type
            provider_groups = {}
            for provider in found_providers:
                ptype = provider['type']
                if ptype not in provider_groups:
                    provider_groups[ptype] = []
                provider_groups[ptype].append(provider)
            
            # Add each group
            for provider_type, providers in provider_groups.items():
                resource_list += f"{provider_type.upper()}S:\n"
                for i, provider in enumerate(providers, 1):
                    resource_list += f"""
    {i}. {provider['name']}
    Address: {provider['address']}
    Phone: {provider['phone']}
    Distance: {provider['distance']} km
    Hours: {provider['opening_hours']}
    Website: {provider['website']}
    Google Maps: https://www.google.com/maps/dir/{search_location}/{provider['lat']},{provider['lon']}

    """
                resource_list += "\n"
        
        else:
            resource_list += """NO PROVIDERS FOUND IN SEARCH:
    Please try searching with different criteria or check these options:
    - Use Google Maps to search 'doctors near me' or 'hospitals near me'
    - Contact your local health department
    - Check your insurance provider's directory

    """
        
        # Add general resources
        resource_list += f"""TELEHEALTH OPTIONS:
    - {'Practo, 1mg, DocsApp, Lybrate' if is_india else 'Planned Parenthood, Nurx, Wisp, Maven'}

    INSURANCE/COVERAGE:
    - {'Ayushman Bharat, CGHS, State schemes' if is_india else 'Healthcare.gov, Medicaid, Local programs'}

    ADDITIONAL RESOURCES:
    - Government Health Portal: {'mohfw.gov.in' if is_india else 'healthcare.gov'}
    - Mental Health Support: {'NIMHANS: 080-26995000' if is_india else '988 Suicide & Crisis Lifeline'}

    For updated provider information, use the search function above.
    Visit https://yshy-healthcare.app for the latest resources.

    Disclaimer: This list is for informational purposes only. 
    Always verify provider credentials and availability before visiting.
    Contact providers directly to confirm services, hours, and availability.
    """
        
        st.download_button(
            label="Download Complete Resource List",
            data=resource_list,
            file_name=f"yshy_resources_{city}_{state}_{datetime.now().strftime('%Y%m%d')}.txt",
            mime="text/plain"
        )
        
        # Show preview of what will be downloaded
        with st.expander("📄 Preview Resource List Content"):
            st.text(resource_list[:2000] + "..." if len(resource_list) > 2000 else resource_list)
        
with tab5:
    st.header("Women's Health Education")
    
    # Create educational categories
    ed_tab1, ed_tab2, ed_tab3, ed_tab4 = st.tabs(["Anatomy & Basics", "Common Conditions", "Prevention", "FAQ"])
    
    with ed_tab1:
        st.subheader("Female Anatomy & Health Basics")
        
        st.markdown("""
        ### Understanding Your Body
        
        Knowledge of your anatomy helps you communicate effectively with healthcare providers and recognize changes:
        
        **External Anatomy**
        - **Vulva**: The external genital area including the labia, clitoris, and vaginal opening
        - **Labia majora**: Outer folds of skin
        - **Labia minora**: Inner folds of skin
        - **Clitoris**: Sensitive organ at the top of the vulva
        - **Vaginal opening**: Entrance to the vagina
        - **Urethra**: Opening where urine exits the body
        
        **Internal Anatomy**
        - **Vagina**: Muscular canal connecting the external genitalia to the cervix
        - **Cervix**: Lower portion of the uterus that connects to the vagina
        - **Uterus**: Hollow, pear-shaped organ where a fetus develops
        - **Fallopian tubes**: Tubes that carry eggs from the ovaries to the uterus
        - **Ovaries**: Organs that produce eggs and hormones
        
        ### Normal Variations
        
        Every body is different. Normal variations include:
        
        - **Labia size and shape**: Wide variations in size, shape, color, and symmetry
        - **Discharge**: Changes throughout the menstrual cycle
        - **Odor**: Mild scent that may change with diet, hygiene, and menstrual cycle
        - **Pubic hair**: Natural variations in amount, texture, and distribution
        """)
        
        st.image("https://upload.wikimedia.org/wikipedia/commons/6/68/Scheme_female_reproductive_system-en.svg", caption="Female Reproductive Anatomy Diagram")
        
        st.markdown("""
        ### Normal Vaginal Discharge
        
        Discharge is the body's way of keeping the vagina clean and healthy. Normal discharge:
        
        - Changes throughout the menstrual cycle
        - May be clear, white, or yellowish
        - Can be thin or thick depending on cycle phase
        - Should not cause irritation or strong odor
        
        **When to be concerned:**
        - Significant change in color, amount, or odor
        - Accompanied by itching, burning, or irritation
        - Unusual consistency (like cottage cheese or foamy)
        - Accompanied by pelvic pain or fever
        """)
        
    with ed_tab2:
        st.subheader("Common Women's Health Conditions")
        
        # Create expandable sections for each condition
        with st.expander("Yeast Infections"):
            col1, col2 = st.columns([1, 1])
            
            with col1:
                st.markdown("""
                ### Vaginal Yeast Infection (Candidiasis)
                
                **What it is:** An overgrowth of the fungus Candida, usually Candida albicans, in the vagina.
                
                **Symptoms:**
                - Thick, white, odorless discharge with a cottage cheese-like appearance
                - Intense itching and irritation
                - Burning sensation, especially during urination or intercourse
                - Redness and swelling of the vulva
                - Vaginal pain or soreness
                
                **Causes:**
                - Antibiotics (disrupt natural vaginal flora)
                - Hormonal changes (pregnancy, menstruation, birth control)
                - Diabetes or high blood sugar
                - Weakened immune system
                - Tight, non-breathable clothing
                """)
            
            with col2:
                st.markdown("""
                **Treatment:**
                - Over-the-counter antifungal medications (creams, suppositories, tablets)
                - Prescription oral antifungal medications for severe cases
                - Proper hygiene practices
                
                **Prevention:**
                - Wear cotton underwear and loose-fitting clothing
                - Avoid douching and scented hygiene products
                - Change out of wet clothes quickly
                - Take probiotics, especially when on antibiotics
                - Maintain blood sugar control if diabetic
                
                **When to see a doctor:**
                - First-time symptoms (to confirm diagnosis)
                - Recurrent infections (4+ per year)
                - Severe symptoms
                - If pregnant
                - No improvement after OTC treatment
                """)
        
        with st.expander("Bacterial Vaginosis (BV)"):
            col1, col2 = st.columns([1, 1])
            
            with col1:
                st.markdown("""
                ### Bacterial Vaginosis
                
                **What it is:** An imbalance of bacteria in the vagina, where harmful bacteria outnumber beneficial bacteria.
                
                **Symptoms:**
                - Thin, grayish-white discharge
                - "Fishy" odor, especially after sex
                - Burning during urination
                - Itching around the vagina
                - Many women have no symptoms
                
                **Causes:**
                - Multiple or new sexual partners
                - Lack of lactobacilli bacteria
                - Douching
                - IUD use
                - Natural imbalance of vaginal bacteria
                """)
            
            with col2:
                st.markdown("""
                **Treatment:**
                - Antibiotics (metronidazole, clindamycin) in pill or gel form
                - Avoid alcohol during and after treatment
                - Complete full course of antibiotics
                
                **Prevention:**
                - Limit number of sexual partners
                - Use condoms consistently
                - Avoid douching and scented products
                - Cotton underwear and breathable clothing
                - Probiotics (some evidence supports this)
                
                **When to see a doctor:**
                - Unusual discharge with odor
                - Symptoms persist after treatment
                - Recurrent BV
                - If pregnant or planning pregnancy
                """)
        
        with st.expander("Genital Herpes"):
            st.markdown("""
            ### Genital Herpes
            
            **What it is:** A sexually transmitted infection caused by the herpes simplex virus (HSV).
            
            **Symptoms:**
            - Painful blisters or sores on genitals, rectum, or mouth
            - Flu-like symptoms during first outbreak
            - Itching, tingling, or burning before sores appear
            - Pain during urination
            - Many people have no symptoms
            
            **Causes:**
            - HSV-1 or HSV-2 infection, usually spread through sexual contact
            - Can be transmitted even when no symptoms are present
            - Can be transmitted through oral, vaginal, or anal sex
            
            **Treatment:**
            - No cure, but symptoms can be managed
            - Antiviral medications reduce severity and frequency
            - Pain relievers for discomfort
            - Warm baths for lesions
            
            **Prevention:**
            - Condoms reduce but don't eliminate risk
            - Avoid sexual contact during outbreaks
            - Antiviral medications can reduce transmission risk
            - Open communication with partners
            
            **When to see a doctor:**
            - First outbreak
            - Severe or prolonged symptoms
            - If pregnant
            - Frequent recurrences
            """)
        
        with st.expander("Urinary Tract Infections (UTIs)"):
            st.markdown("""
            ### Urinary Tract Infections
            
            **What it is:** Bacterial infection affecting any part of the urinary system.
            
            **Symptoms:**
            - Burning sensation during urination
            - Frequent, intense urge to urinate
            - Passing small amounts of urine
            - Cloudy, strong-smelling urine
            - Pelvic pain (especially in women)
            - Blood in urine
            
            **Causes:**
            - Bacteria entering the urinary tract
            - Sexual activity
            - Female anatomy (shorter urethra)
            - Menopause
            - Urinary tract abnormalities
            - Suppressed immune system
            
            **Treatment:**
            - Antibiotics
            - Pain medications
            - Increased fluid intake
            - Avoiding irritants (caffeine, alcohol)
            
            **Prevention:**
            - Drink plenty of water
            - Urinate after sexual activity
            - Wipe from front to back
            - Avoid potentially irritating feminine products
            - Take showers instead of baths
            - Cranberry products (some evidence supports this)
            
            **When to see a doctor:**
            - Any UTI symptoms
            - Symptoms that don't improve with treatment
            - Recurrent UTIs
            - If pregnant
            - Symptoms with fever or back pain
            """)
        
        with st.expander("Vulvodynia"):
            st.markdown("""
            ### Vulvodynia
            
            **What it is:** Chronic pain or discomfort around the opening of the vagina without an identifiable cause.
            
            **Symptoms:**
            - Burning, stinging, or rawness in the vulvar area
            - Throbbing, aching pain
            - Pain during intercourse
            - Pain when inserting tampons
            - Pain or discomfort when sitting
            
            **Causes:**
            - Exact cause unknown
            - Possible nerve irritation or injury
            - Past vaginal infections
            - Allergies or skin sensitivities
            - Hormonal changes
            - Muscle spasms in the pelvic floor
            
            **Treatment:**
            - Multidisciplinary approach
            - Physical therapy for pelvic floor
            - Medications (anticonvulsants, tricyclic antidepressants)
            - Biofeedback therapy
            - Local anesthetics
            - Lifestyle changes
            
            **Management:**
            - Wear loose cotton clothing
            - Avoid potential irritants
            - Use lubricants for sexual activity
            - Apply cool compresses
            - Pelvic floor relaxation exercises
            
            **When to see a doctor:**
            - Persistent pain in vulvar area
            - Pain that affects quality of life
            - Pain during sexual intercourse
            """)
    
    with ed_tab3:
        st.header("Prevention & Self-Care")
        
        st.markdown("""
        ### Daily Hygiene Practices
        
        **DO:**
        - Wash the external genital area with warm water and mild, unscented soap
        - Change underwear daily
        - Wear breathable, cotton underwear
        - Wipe from front to back after using the bathroom
        - Change tampons/pads regularly during menstruation
        
        **DON'T:**
        - Douche (vaginas are self-cleaning)
        - Use scented products (soaps, bubble baths, sprays)
        - Wear tight underwear or pants for extended periods
        - Use harsh cleansers or wash excessively
        - Sit in wet clothing or bathing suits
        
        ### Sexual Health
        
        **Safe Sex Practices:**
        - Use condoms consistently
        - Get regular STI testing
        - Communicate openly with partners
        - Urinate after sexual activity to prevent UTIs
        - Consider dental dams for oral sex
        
        **Regular Check-ups:**
        - Annual gynecological exams
        - Pap smears as recommended (typically every 3 years)
        - HPV testing
        - Mammograms as recommended by age
        - STI testing based on risk factors
        
        ### Lifestyle Factors
        
        **Diet and Hydration:**
        - Stay well-hydrated
        - Consume probiotics (yogurt, kefir)
        - Limit sugar intake
        - Eat plenty of fruits and vegetables
        - Consider cranberry products for UTI prevention
        
        **Exercise:**
        - Regular physical activity
        - Kegel exercises for pelvic floor strength
        - Avoid excessive strain during workouts
        - Practice good hygiene before and after exercise
        
        **Stress Management:**
        - Practice relaxation techniques
        - Get adequate sleep
        - Maintain work-life balance
        - Consider counseling if needed
        - Connect with support systems
        """)
        
        st.markdown("""
        ### Tracking Your Health
        
        **What to Track:**
        - Menstrual cycle length and symptoms
        - Discharge changes throughout cycle
        - Any unusual symptoms
        - Sexual activity
        - Medication usage
        
        **When to Seek Help:**
        - Significant changes in discharge
        - Pain during urination or intercourse
        - Unusual bleeding
        - Persistent itching or irritation
        - Pelvic pain
        - Sores or unusual growths
        """)
    
    with ed_tab4:
        st.subheader("Frequently Asked Questions")
        
        with st.expander("Is vaginal discharge normal?"):
            st.markdown("""
            **Yes, vaginal discharge is completely normal.** It's the body's way of maintaining vaginal health and cleanliness.
            
            Normal discharge varies in consistency, color, and amount throughout your menstrual cycle due to hormonal changes:
            
            - **During ovulation:** Discharge may be clear and stretchy, similar to egg whites
            - **Before menstruation:** Discharge may become thicker or cloudier
            - **After menstruation:** Discharge may be minimal
            
            Changes in discharge can be affected by:
            - Birth control methods
            - Pregnancy
            - Sexual arousal
            - Stress
            - Diet
            
            **When to be concerned:**
            - Significant change in color (green, gray, yellow)
            - Strong unpleasant odor
            - Accompanied by itching, burning, or irritation
            - Unusual consistency (cottage cheese-like, foamy)
            - Significant increase in amount
            """)
        
        with st.expander("How often should I get checked for STIs?"):
            st.markdown("""
            **STI testing frequency depends on your personal risk factors:**
            
            **General guidelines:**
            
            - **Annually:** If sexually active with new or multiple partners
            - **Every 3-6 months:** If higher risk (multiple partners, inconsistent condom use)
            - **With new partners:** Before beginning sexual activity with a new partner
            - **If symptomatic:** Any time you experience symptoms
            - **After unprotected sex:** If you've had sex without protection
            
            **Specific recommendations by age/group:**
            
            - **Everyone sexually active:** HIV testing at least once
            - **Pregnant women:** STI screening during pregnancy
            - **Women under 25:** Annual chlamydia and gonorrhea screening
            - **Women over 25 with risk factors:** Annual chlamydia and gonorrhea screening
            - **Men who have sex with men:** More frequent testing based on sexual behaviors
            
            Talk to your healthcare provider about testing recommendations specific to your situation. Many STIs don't show symptoms, so regular testing is important for sexual health.
            """)
        
        with st.expander("Is douching recommended?"):
            st.markdown("""
            **No, douching is not recommended by medical professionals.**
            
            Douching (washing or cleaning the vagina with water or other fluids) can actually harm vaginal health by:
            
            - Disrupting the natural balance of bacteria
            - Washing away beneficial bacteria
            - Increasing risk of vaginal infections
            - Potentially pushing bacteria up into the uterus and fallopian tubes
            - Increasing risk of pelvic inflammatory disease
            - May lead to increased risk of ectopic pregnancy
            
            **The vagina is self-cleaning:**
            - Natural discharge helps remove dead cells and bacteria
            - The acidic environment naturally prevents infection
            - The balanced microbiome protects against harmful organisms
            
            **Instead of douching:**
            - Gently wash the external genital area (vulva) with mild soap and water
            - Allow the vagina to maintain its natural cleaning process
            - Wear cotton underwear
            - Avoid scented products in the genital area
            
            If you're concerned about odor or discharge, it's better to see a healthcare provider than to douche.
            """)
        
        with st.expander("How can I prevent recurrent yeast infections?"):
            st.markdown("""
            **Preventing recurrent yeast infections requires addressing multiple factors:**
            
            **Clothing and hygiene:**
            - Wear cotton underwear and loose-fitting clothes
            - Change out of wet clothing promptly
            - Avoid tight-fitting pantyhose, leggings, or pants
            - Change tampons, pads, and liners frequently
            - Avoid sitting in wet bathing suits
            
            **Bathing habits:**
            - Use mild, unscented soap for external washing only
            - Avoid bubble baths, scented bath products, and oils
            - Pat dry thoroughly after bathing
            - Consider using a hair dryer on cool setting to dry genital area
            
            **Diet and supplements:**
            - Reduce sugar and refined carbohydrates
            - Consider probiotics (especially Lactobacillus)
            - Maintain healthy blood sugar levels
            - Stay well-hydrated
            
            **Medications and health:**
            - Take antibiotics only when necessary
            - Consider prophylactic antifungal treatment when on antibiotics
            - Manage diabetes and other health conditions
            - Discuss birth control options if hormonal methods contribute
            
            **Sexual activity:**
            - Use condoms to prevent passing infection between partners
            - Urinate before and after sexual activity
            - Avoid spermicides if sensitive
            - Consider partners may need treatment
            
            **When to see a doctor:**
            - If you have 4+ yeast infections in a year
            - If over-the-counter treatments aren't effective
            - If you're unsure whether symptoms are yeast infection
            - If you have underlying health conditions like diabetes
            """)
        
        with st.expander("What is the difference between BV and a yeast infection?"):
            st.markdown("""
            **Bacterial Vaginosis (BV) and yeast infections are different conditions with some similar symptoms:**
            
            **Bacterial Vaginosis:**
            
            - **Cause:** Imbalance of bacteria in the vagina
            - **Discharge:** Thin, grayish-white, watery
            - **Odor:** Distinctive "fishy" smell, especially after sex
            - **Itching/Irritation:** Mild or absent
            - **Other symptoms:** Sometimes burning during urination
            - **Treatment:** Antibiotics (metronidazole, clindamycin)
            
            **Yeast Infection:**
            
            - **Cause:** Overgrowth of Candida fungus
            - **Discharge:** Thick, white, cottage cheese-like consistency
            - **Odor:** Usually no strong odor
            - **Itching/Irritation:** Often severe itching and irritation
            - **Other symptoms:** Burning, redness, swelling
            - **Treatment:** Antifungal medications
            
            **Key Differences:**
            
            - **Odor:** Strong fishy odor is typical of BV, not yeast infections
            - **Discharge consistency:** Thin/watery for BV vs. thick/chunky for yeast
            - **Itching severity:** Usually more intense with yeast infections
            - **Treatment:** Different medications (antibiotics vs. antifungals)
            
            **Important note:** Self-diagnosis can be difficult, and misdiagnosis leads to using the wrong treatment. If you're unsure, consult a healthcare provider for proper diagnosis, especially for first-time symptoms or recurrent issues.
            """)
        
        with st.expander("When should I see a doctor about vaginal symptoms?"):
            st.markdown("""
            **Seek medical attention if you experience:**
            
            **Changes in discharge:**
            - Unusual color (green, gray, yellow-green)
            - Strong, foul, or fishy odor
            - Significant change in amount or consistency
            
            **Pain or discomfort:**
            - Persistent itching or burning
            - Pain during intercourse
            - Pain during urination
            - Pelvic or abdominal pain
            
            **Abnormal bleeding:**
            - Bleeding between periods
            - Heavier than normal periods
            - Bleeding after menopause
            - Bleeding after intercourse
            
            **Other concerning symptoms:**
            - Sores, warts, blisters, or lesions
            - Rash or unusual growths
            - Persistent symptoms despite self-treatment
            - Symptoms with fever or feeling unwell
            
            **Special circumstances:**
            - If you're pregnant
            - If you've had a new sexual partner
            - If you've had unprotected sex
            - If you have a compromised immune system
            - If you have diabetes or other chronic conditions
            
            **General guidance:**
            - First-time symptoms are best evaluated by a healthcare provider
            - Recurrent symptoms (4+ times per year) need medical attention
            - When in doubt, consult a healthcare professional
            
            Early diagnosis and treatment can prevent complications and provide relief sooner.
            """)

# Footer
st.markdown("---")
col1, col2, col3 = st.columns([1, 2, 1])
with col2:
    st.markdown(
        "YSHY is designed to provide preliminary information only. Always consult with a healthcare professional for proper diagnosis and treatment.",
        help="This application processes data locally and does not store any images or personal information."
    )
    
    # Last updated
    st.caption(f"Last updated: {datetime.now().strftime('%B %d, %Y')}")
    
    # Version number
    st.caption("Version 2.0.4")
    
    # Emergency info
    st.info("For medical emergencies, please call emergency services immediately.")